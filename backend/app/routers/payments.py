"""
포트원 결제 API 라우터.
구독 결제 검증 및 취소 엔드포인트를 제공합니다.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.payment import cancel_payment, verify_payment
from app.services.subscription import get_or_create_subscription, upgrade_subscription
from app.utils.auth import get_current_user
from app.utils.response import error_response, success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

PLAN_PRICES = {
    "monthly": 4900,
    "yearly": 39000,
}


class PaymentVerifyRequest(BaseModel):
    imp_uid: str = Field(..., description="포트원 결제 고유번호 (imp_xxx)")
    merchant_uid: str = Field(..., description="주문번호")
    plan: str = Field(..., description="구독 플랜 (monthly | yearly)")


class PaymentCancelRequest(BaseModel):
    imp_uid: str = Field(..., description="포트원 결제 고유번호")
    reason: str = Field(default="사용자 요청", description="취소 사유")


@router.post("/verify")
async def verify_subscription_payment(
    body: PaymentVerifyRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    구독 결제를 검증하고 프리미엄을 활성화합니다.

    1. 포트원 서버에서 결제 정보를 조회
    2. 금액 위변조 검증 (예상 금액 vs 실제 결제 금액)
    3. 검증 통과 시 구독 업그레이드 처리
    """
    if body.plan not in PLAN_PRICES:
        return error_response("유효하지 않은 플랜입니다. (monthly | yearly)", 400)

    expected_amount = PLAN_PRICES[body.plan]

    result = await verify_payment(
        imp_uid=body.imp_uid,
        merchant_uid=body.merchant_uid,
        expected_amount=expected_amount,
    )

    if not result["success"]:
        logger.warning(
            "Payment verification failed: user=%s, imp_uid=%s, reason=%s",
            user_id, body.imp_uid, result.get("message"),
        )
        return error_response(result.get("message", "결제 검증에 실패했습니다."), 400)

    # 구독 업그레이드
    try:
        sub = await upgrade_subscription(
            db=db,
            user_id=user_id,
            plan=body.plan,
            payment_provider="portone",
            payment_id=body.imp_uid,
            price_krw=result["amount"],
        )
        await db.commit()
    except Exception as exc:
        logger.error("Subscription upgrade failed after payment: user=%s, exc=%s", user_id, exc)
        return error_response("결제는 완료되었으나 구독 처리 중 오류가 발생했습니다. 고객센터에 문의하세요.", 500)

    logger.info(
        "Payment verified and subscription upgraded: user=%s, plan=%s, imp_uid=%s",
        user_id, body.plan, body.imp_uid,
    )

    return success_response({
        "message": "결제가 완료되었습니다. 프리미엄이 활성화되었습니다.",
        "plan": body.plan,
        "imp_uid": body.imp_uid,
        "amount": result["amount"],
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
    })


@router.post("/cancel")
async def cancel_subscription_payment(
    body: PaymentCancelRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    구독 결제를 취소합니다.

    - 포트원을 통해 결제 취소 처리
    - 구독 상태를 cancelled로 변경 (만료일까지 이용 가능)
    """
    sub = await get_or_create_subscription(db, user_id)

    if not sub.is_active_premium:
        return error_response("활성화된 프리미엄 구독이 없습니다.", 400)

    imp_uid = body.imp_uid or sub.payment_id
    if not imp_uid:
        return error_response("취소할 결제 정보를 찾을 수 없습니다.", 400)

    result = await cancel_payment(
        imp_uid=imp_uid,
        reason=body.reason,
    )

    if not result["success"]:
        logger.warning(
            "Payment cancel failed: user=%s, imp_uid=%s, reason=%s",
            user_id, imp_uid, result.get("message"),
        )
        return error_response(result.get("message", "결제 취소에 실패했습니다."), 400)

    # 구독 상태 업데이트
    sub.status = "cancelled"
    sub.cancelled_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info("Subscription payment cancelled: user=%s, imp_uid=%s", user_id, imp_uid)

    return success_response({
        "message": "구독이 취소되었습니다. 만료일까지 프리미엄을 이용하실 수 있습니다.",
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
        "cancel_amount": result.get("cancel_amount", 0),
    })
