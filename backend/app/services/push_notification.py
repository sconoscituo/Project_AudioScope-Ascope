"""
FCM(Firebase Cloud Messaging) 푸시 알림 서비스.
브리핑 완료 알림 등을 사용자 기기에 발송합니다.
"""

import logging

import httpx

logger = logging.getLogger(__name__)


class FCMService:
    """FCM Legacy HTTP API를 사용하는 푸시 알림 서비스."""

    FCM_URL = "https://fcm.googleapis.com/fcm/send"

    def __init__(self, server_key: str):
        self.server_key = server_key
        self.headers = {
            "Authorization": f"key={server_key}",
            "Content-Type": "application/json",
        }

    async def send_to_token(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: dict | None = None,
    ) -> bool:
        """단일 기기 토큰으로 알림을 발송합니다."""
        if not self.server_key:
            logger.warning("FCM_SERVER_KEY가 설정되지 않아 알림을 건너뜁니다.")
            return False

        payload = {
            "to": fcm_token,
            "notification": {"title": title, "body": body},
            "data": data or {},
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    self.FCM_URL, json=payload, headers=self.headers
                )
                resp.raise_for_status()
                result = resp.json()
                if result.get("failure", 0) > 0:
                    logger.warning(
                        "FCM 발송 실패 (token=...%s): %s",
                        fcm_token[-8:],
                        result,
                    )
                    return False
                logger.debug("FCM 발송 성공: token=...%s", fcm_token[-8:])
                return True
        except Exception as exc:
            logger.error("FCM 발송 오류: %s", exc)
            return False

    async def send_briefing_ready(self, fcm_token: str, briefing_title: str) -> bool:
        """브리핑 준비 완료 알림을 발송합니다."""
        return await self.send_to_token(
            fcm_token,
            title="모닝 브리핑 준비됨",
            body=f"{briefing_title} - 지금 들어보세요",
            data={"type": "briefing_ready"},
        )

    async def send_to_tokens(
        self,
        fcm_tokens: list[str],
        title: str,
        body: str,
        data: dict | None = None,
    ) -> dict[str, int]:
        """여러 기기 토큰으로 알림을 발송합니다. 성공/실패 수를 반환합니다."""
        success, failure = 0, 0
        for token in fcm_tokens:
            ok = await self.send_to_token(token, title, body, data)
            if ok:
                success += 1
            else:
                failure += 1
        return {"success": success, "failure": failure}
