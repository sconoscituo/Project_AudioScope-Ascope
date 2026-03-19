"""
서비스 팩토리 모듈.
싱글톤 캐싱을 적용한 팩토리 패턴으로 서비스 인스턴스를 생성·관리합니다.
"""

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)


class ServiceFactory:
    """
    서비스 인스턴스를 생성하고 싱글톤으로 캐싱하는 팩토리 클래스.

    Usage:
        factory = ServiceFactory()
        news_svc  = factory.create_news_service()
        tts_svc   = factory.create_tts_service()
        summarizer = factory.create_summarizer()
    """

    _instances: dict[str, Any] = {}
    _lock = threading.Lock()

    # ── 팩토리 메서드 ──

    def create_news_service(self):
        """NaverNewsFetcher 싱글톤 인스턴스를 반환합니다."""
        return self._get_or_create("news_service", self._build_news_service)

    def create_tts_service(self):
        """SupertoneTTS 싱글톤 인스턴스를 반환합니다."""
        return self._get_or_create("tts_service", self._build_tts_service)

    def create_summarizer(self):
        """GeminiSummarizer 싱글톤 인스턴스를 반환합니다."""
        return self._get_or_create("summarizer", self._build_summarizer)

    # ── 내부 빌더 ──

    @staticmethod
    def _build_news_service():
        from app.services.news_fetcher import NaverNewsFetcher
        instance = NaverNewsFetcher()
        logger.info("ServiceFactory: NaverNewsFetcher created.")
        return instance

    @staticmethod
    def _build_tts_service():
        from app.services.tts import SupertoneTTS
        instance = SupertoneTTS()
        logger.info("ServiceFactory: SupertoneTTS created.")
        return instance

    @staticmethod
    def _build_summarizer():
        from app.services.summarizer import GeminiSummarizer
        instance = GeminiSummarizer()
        logger.info("ServiceFactory: GeminiSummarizer created.")
        return instance

    # ── 싱글톤 캐시 헬퍼 ──

    def _get_or_create(self, key: str, builder):
        """키가 캐시에 없으면 builder를 호출해 생성 후 저장합니다 (thread-safe)."""
        if key not in self._instances:
            with self._lock:
                if key not in self._instances:
                    self._instances[key] = builder()
        return self._instances[key]

    # ── 유틸리티 ──

    @classmethod
    def reset(cls) -> None:
        """캐시를 초기화합니다 (테스트 전용)."""
        with cls._lock:
            cls._instances.clear()
        logger.info("ServiceFactory: instance cache cleared.")

    @classmethod
    def initialized_keys(cls) -> list[str]:
        """현재 캐싱된 서비스 키 목록을 반환합니다."""
        return list(cls._instances.keys())
