"""포트원 결제 연동 - 구독 결제 처리."""

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

PORTONE_API_BASE = "https://api.iamport.kr"


async def _get_portone_access_token() -> str:
    """포트원 API 액세스 토큰을 발급받습니다."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PORTONE_API_BASE}/users/getToken",
            json={
                "imp_key": settings.PORTONE_API_KEY,
                "imp_secret": settings.PORTONE_API_SECRET,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            raise ValueError(f"포트원 토큰 발급 실패: {data.get('message')}")
        return data["response"]["access_token"]


async def verify_payment(imp_uid: str, merchant_uid: str, expected_amount: int) -> dict[str, Any]:
    """
    포트원 결제를 검증합니다.

    Args:
        imp_uid: 포트원 결제 고유번호 (imp_xxx)
        merchant_uid: 주문번호 (서비스 내부 ID)
        expected_amount: 결제 예상 금액 (원)

    Returns:
        dict: {
            "success": bool,
            "imp_uid": str,
            "merchant_uid": str,
            "amount": int,
            "status": str,  # "paid" | "failed" | "cancelled"
            "paid_at": int,  # Unix timestamp
            "message": str,
        }
    """
    try:
        access_token = await _get_portone_access_token()
    except Exception as exc:
        logger.error("포트원 토큰 발급 실패: %s", exc)
        return {
            "success": False,
            "imp_uid": imp_uid,
            "merchant_uid": merchant_uid,
            "amount": 0,
            "status": "failed",
            "paid_at": None,
            "message": f"결제 서비스 연결 실패: {exc}",
        }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PORTONE_API_BASE}/payments/{imp_uid}",
                headers={"Authorization": access_token},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("code") != 0:
            return {
                "success": False,
                "imp_uid": imp_uid,
                "merchant_uid": merchant_uid,
                "amount": 0,
                "status": "failed",
                "paid_at": None,
                "message": data.get("message", "결제 정보 조회 실패"),
            }

        payment = data["response"]
        actual_amount = payment.get("amount", 0)
        status = payment.get("status", "failed")

        # 금액 위변조 검증
        if status == "paid" and actual_amount != expected_amount:
            logger.warning(
                "결제 금액 불일치: imp_uid=%s, expected=%d, actual=%d",
                imp_uid, expected_amount, actual_amount,
            )
            return {
                "success": False,
                "imp_uid": imp_uid,
                "merchant_uid": merchant_uid,
                "amount": actual_amount,
                "status": "amount_mismatch",
                "paid_at": payment.get("paid_at"),
                "message": f"결제 금액 불일치 (예상: {expected_amount}원, 실제: {actual_amount}원)",
            }

        logger.info("결제 검증 완료: imp_uid=%s, status=%s, amount=%d", imp_uid, status, actual_amount)
        return {
            "success": status == "paid",
            "imp_uid": imp_uid,
            "merchant_uid": merchant_uid,
            "amount": actual_amount,
            "status": status,
            "paid_at": payment.get("paid_at"),
            "message": "결제 검증 성공" if status == "paid" else f"결제 상태: {status}",
        }

    except httpx.HTTPError as exc:
        logger.error("포트원 API 호출 실패: %s", exc)
        return {
            "success": False,
            "imp_uid": imp_uid,
            "merchant_uid": merchant_uid,
            "amount": 0,
            "status": "failed",
            "paid_at": None,
            "message": f"결제 검증 중 오류 발생: {exc}",
        }


async def cancel_payment(
    imp_uid: str,
    reason: str,
    cancel_request_amount: int | None = None,
) -> dict[str, Any]:
    """
    포트원 결제를 취소합니다.

    Args:
        imp_uid: 포트원 결제 고유번호
        reason: 취소 사유
        cancel_request_amount: 부분 취소 금액 (None이면 전액 취소)

    Returns:
        dict: {
            "success": bool,
            "imp_uid": str,
            "cancel_amount": int,
            "message": str,
        }
    """
    try:
        access_token = await _get_portone_access_token()
    except Exception as exc:
        logger.error("포트원 토큰 발급 실패 (취소): %s", exc)
        return {
            "success": False,
            "imp_uid": imp_uid,
            "cancel_amount": 0,
            "message": f"결제 서비스 연결 실패: {exc}",
        }

    payload: dict[str, Any] = {"imp_uid": imp_uid, "reason": reason}
    if cancel_request_amount is not None:
        payload["cancel_request_amount"] = cancel_request_amount

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PORTONE_API_BASE}/payments/cancel",
                headers={"Authorization": access_token},
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("code") != 0:
            return {
                "success": False,
                "imp_uid": imp_uid,
                "cancel_amount": 0,
                "message": data.get("message", "결제 취소 실패"),
            }

        cancelled = data["response"]
        cancel_amount = cancelled.get("cancel_amount", 0)
        logger.info("결제 취소 완료: imp_uid=%s, cancel_amount=%d", imp_uid, cancel_amount)
        return {
            "success": True,
            "imp_uid": imp_uid,
            "cancel_amount": cancel_amount,
            "message": "결제가 취소되었습니다.",
        }

    except httpx.HTTPError as exc:
        logger.error("포트원 취소 API 호출 실패: %s", exc)
        return {
            "success": False,
            "imp_uid": imp_uid,
            "cancel_amount": 0,
            "message": f"결제 취소 중 오류 발생: {exc}",
        }
