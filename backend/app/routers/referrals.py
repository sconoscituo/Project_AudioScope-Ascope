"""
추천 보상 API 라우터.
추천 코드 생성, 추천 등록, 보상 확인.
3명 추천 시 7일 프리미엄 잠금해제.
referral_code는 User 모델에 인덱스된 컬럼으로 저장하여 O(1) 조회.
"""

import hashlib
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.referral import Referral
from app.models.user import User
from app.services.subscription import upgrade_subscription
from app.utils.auth import get_current_user
from app.utils.response import error_response, success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/referrals", tags=["referrals"])

REFERRALS_FOR_REWARD = 3
REWARD_PLAN = "trial"


def _generate_code(user_id: str) -> str:
    """user_id에서 8자리 추천 코드를 생성합니다."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:8].upper()


async def _ensure_referral_code(db: AsyncSession, user: User) -> str:
    """사용자의 referral_code가 없으면 생성하여 저장합니다."""
    if user.referral_code:
        return user.referral_code
    code = _generate_code(str(user.id))
    user.referral_code = code
    await db.flush()
    return code


@router.get("/my-code")
async def get_my_referral_code(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내 추천 코드와 추천 현황을 반환합니다."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return error_response("사용자를 찾을 수 없습니다.", 404)

    code = await _ensure_referral_code(db, user)

    count_stmt = select(func.count()).select_from(Referral).where(
        Referral.referrer_id == user_id
    )
    count = (await db.execute(count_stmt)).scalar_one()

    return success_response({
        "referral_code": code,
        "referral_count": count,
        "referrals_needed": max(0, REFERRALS_FOR_REWARD - count),
        "reward_unlocked": count >= REFERRALS_FOR_REWARD,
    })


@router.post("/apply")
async def apply_referral_code(
    code: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """추천 코드를 적용합니다 (가입 후 1회)."""
    normalized_code = code.strip().upper()

    # 자기 자신의 코드 체크
    me = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if me and me.referral_code == normalized_code:
        return error_response("본인의 추천 코드는 사용할 수 없습니다.", 400)

    # 이미 추천 받은 적 있는지 체크
    existing = (await db.execute(
        select(Referral).where(Referral.referred_id == user_id)
    )).scalar_one_or_none()
    if existing:
        return error_response("이미 추천 코드를 사용했습니다.", 400)

    # 추천인 찾기 - DB 인덱스로 O(1) 조회
    referrer = (await db.execute(
        select(User).where(
            User.referral_code == normalized_code,
            User.is_active.is_(True),
        )
    )).scalar_one_or_none()

    if referrer is None:
        return error_response("유효하지 않은 추천 코드입니다.", 400)

    # 추천 기록 저장
    ref = Referral(
        referrer_id=referrer.id,
        referred_id=user_id,
        referral_code=normalized_code,
    )
    db.add(ref)
    await db.flush()

    # 추천인의 총 추천 수 확인 → 보상 지급
    total_refs = (await db.execute(
        select(func.count()).select_from(Referral).where(
            Referral.referrer_id == referrer.id
        )
    )).scalar_one()

    reward_msg = None
    if total_refs >= REFERRALS_FOR_REWARD:
        unrewarded = (await db.execute(
            select(Referral).where(
                Referral.referrer_id == referrer.id,
                Referral.reward_granted.is_(False),
            )
        )).scalars().all()

        if unrewarded:
            for r in unrewarded:
                r.reward_granted = True
            await upgrade_subscription(
                db, str(referrer.id), REWARD_PLAN, "referral", f"referral_{total_refs}", 0
            )
            reward_msg = f"추천인에게 {REFERRALS_FOR_REWARD}명 달성 보상이 지급되었습니다!"

    logger.info("Referral applied: referrer=%s, referred=%s, total=%d", referrer.id, user_id, total_refs)

    return success_response({
        "message": "추천 코드가 적용되었습니다!",
        "referrer_reward": reward_msg,
    })
