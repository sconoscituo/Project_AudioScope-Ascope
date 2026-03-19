"""
AI 뉴스 추천 서비스.
사용자 청취 이력 기반으로 Gemini AI가 관심 카테고리 분석 후 맞춤 브리핑 추천.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

import google.generativeai as genai
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.briefing import Briefing, BriefingArticle
from app.models.listen_history import ListenHistory
from app.models.user import UserCategoryPreference

logger = logging.getLogger(__name__)
settings = get_settings()

KST = timezone(timedelta(hours=9))

RECOMMENDATION_SYSTEM_PROMPT = """당신은 AudioScope의 AI 추천 엔진입니다.
사용자의 청취 이력과 카테고리 선호도를 분석하여 맞춤형 뉴스 브리핑을 추천합니다.

분석 기준:
- 자주 청취한 카테고리 (가중치 높음)
- 완청 여부 (완청한 브리핑의 카테고리에 높은 점수)
- 최근 7일 이력 우선
- 다양성을 위해 새로운 카테고리도 일부 포함

응답 형식 (JSON만 반환):
{
  "preferred_categories": ["category1", "category2"],
  "reason": "추천 이유 한 문장",
  "diversity_category": "새로 시도해볼 카테고리"
}
"""


async def get_user_listen_summary(db: AsyncSession, user_id: str) -> dict:
    """최근 30일 청취 이력을 카테고리별로 집계합니다."""
    since = datetime.now(timezone.utc) - timedelta(days=30)

    # 청취한 브리핑 ID 목록
    history_stmt = (
        select(ListenHistory.briefing_id, ListenHistory.completed)
        .where(
            ListenHistory.user_id == user_id,
            ListenHistory.listened_at >= since,
        )
    )
    result = await db.execute(history_stmt)
    histories = result.all()

    if not histories:
        return {"listened_count": 0, "category_counts": {}, "completed_categories": {}}

    briefing_ids = [h.briefing_id for h in histories]
    completed_ids = {h.briefing_id for h in histories if h.completed}

    # 브리핑별 기사 카테고리 집계
    articles_stmt = (
        select(BriefingArticle.briefing_id, BriefingArticle.category)
        .where(BriefingArticle.briefing_id.in_(briefing_ids))
    )
    articles_result = await db.execute(articles_stmt)
    articles = articles_result.all()

    category_counts: dict[str, int] = {}
    completed_categories: dict[str, int] = {}

    for article in articles:
        cat = article.category or "기타"
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if article.briefing_id in completed_ids:
            completed_categories[cat] = completed_categories.get(cat, 0) + 1

    return {
        "listened_count": len(histories),
        "category_counts": category_counts,
        "completed_categories": completed_categories,
    }


async def analyze_user_preferences(db: AsyncSession, user_id: str) -> dict:
    """
    Gemini AI로 사용자 선호 카테고리를 분석합니다.

    Returns:
        dict: {
            "preferred_categories": list[str],
            "reason": str,
            "diversity_category": str | None,
        }
    """
    listen_summary = await get_user_listen_summary(db, user_id)

    # 청취 이력이 없으면 설정된 선호도 기반으로 반환
    if listen_summary["listened_count"] == 0:
        pref_stmt = (
            select(UserCategoryPreference.category)
            .where(
                UserCategoryPreference.user_id == user_id,
                UserCategoryPreference.is_enabled == True,  # noqa: E712
            )
            .order_by(UserCategoryPreference.priority.desc())
            .limit(3)
        )
        pref_result = await db.execute(pref_stmt)
        categories = [row[0] for row in pref_result.all()]

        return {
            "preferred_categories": categories or settings.default_category_list[:3],
            "reason": "설정한 카테고리 선호도 기반 추천입니다.",
            "diversity_category": None,
        }

    if not settings.GEMINI_API_KEY:
        # Gemini 미설정 시 이력 기반 단순 집계
        sorted_cats = sorted(
            listen_summary["category_counts"].items(),
            key=lambda x: x[1],
            reverse=True,
        )
        top_cats = [c for c, _ in sorted_cats[:3]]
        return {
            "preferred_categories": top_cats,
            "reason": "최근 청취 이력 기반 추천입니다.",
            "diversity_category": None,
        }

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=RECOMMENDATION_SYSTEM_PROMPT,
        )

        prompt = (
            f"사용자 청취 이력 분석:\n"
            f"총 청취 횟수: {listen_summary['listened_count']}\n"
            f"카테고리별 청취 횟수: {json.dumps(listen_summary['category_counts'], ensure_ascii=False)}\n"
            f"완청한 카테고리: {json.dumps(listen_summary['completed_categories'], ensure_ascii=False)}\n\n"
            f"위 데이터를 분석하여 추천 카테고리를 JSON 형식으로 반환하세요."
        )

        response = await model.generate_content_async(prompt)
        raw_text = response.text.strip()

        # JSON 블록 추출
        if "```" in raw_text:
            parts = raw_text.split("```")
            for part in parts:
                if part.startswith("json"):
                    raw_text = part[4:].strip()
                    break
                elif "{" in part:
                    raw_text = part.strip()
                    break

        result = json.loads(raw_text)
        logger.info("Gemini preference analysis complete for user=%s", user_id)
        return result

    except Exception as exc:
        logger.warning("Gemini preference analysis failed: %s", exc)
        sorted_cats = sorted(
            listen_summary["category_counts"].items(),
            key=lambda x: x[1],
            reverse=True,
        )
        top_cats = [c for c, _ in sorted_cats[:3]]
        return {
            "preferred_categories": top_cats,
            "reason": "최근 청취 이력 기반 추천입니다.",
            "diversity_category": None,
        }


async def get_recommended_briefings(
    db: AsyncSession,
    user_id: str,
    limit: int = 10,
) -> dict:
    """
    사용자 맞춤 브리핑 추천 목록을 반환합니다.

    Returns:
        dict: {
            "briefings": list[dict],
            "preferred_categories": list[str],
            "reason": str,
        }
    """
    preferences = await analyze_user_preferences(db, user_id)
    preferred_cats = preferences.get("preferred_categories", [])

    # 최근 7일 완료된 브리핑 조회
    since = datetime.now(KST) - timedelta(days=7)
    stmt = (
        select(Briefing)
        .where(
            Briefing.status == "completed",
            Briefing.created_at >= since,
        )
        .order_by(Briefing.scheduled_date.desc(), Briefing.period)
        .limit(limit * 3)
    )
    result = await db.execute(stmt)
    all_briefings = result.scalars().all()

    # 이미 들은 브리핑 ID
    listened_stmt = select(ListenHistory.briefing_id).where(
        ListenHistory.user_id == user_id
    )
    listened_ids = {row[0] for row in (await db.execute(listened_stmt)).all()}

    # 선호 카테고리와 연관도 점수 계산
    scored: list[tuple[float, Briefing]] = []
    for briefing in all_briefings:
        if briefing.id in listened_ids:
            continue
        score = _score_briefing(briefing, preferred_cats)
        scored.append((score, briefing))

    scored.sort(key=lambda x: x[0], reverse=True)
    recommended = [b for _, b in scored[:limit]]

    briefings_data = [
        {
            "id": str(b.id),
            "period": b.period,
            "scheduled_date": b.scheduled_date.isoformat() if b.scheduled_date else None,
            "title": b.title,
            "audio_url": b.audio_url,
            "duration_seconds": b.duration_seconds,
            "article_count": b.article_count,
        }
        for b in recommended
    ]

    return {
        "briefings": briefings_data,
        "preferred_categories": preferred_cats,
        "reason": preferences.get("reason", ""),
        "diversity_category": preferences.get("diversity_category"),
    }


def _score_briefing(briefing: Briefing, preferred_cats: list[str]) -> float:
    """브리핑과 선호 카테고리의 연관도 점수를 계산합니다."""
    score = 0.0

    # 카테고리 매칭 (브리핑 title/period 기반 단순 점수)
    title_lower = (briefing.title or "").lower()
    for i, cat in enumerate(preferred_cats):
        if cat in title_lower:
            score += (len(preferred_cats) - i) * 2.0

    # 최신성 가중치: 오늘에 가까울수록 높은 점수
    if briefing.scheduled_date:
        days_ago = (datetime.now(KST).date() - briefing.scheduled_date).days
        score += max(0, 7 - days_ago) * 0.5

    return score
