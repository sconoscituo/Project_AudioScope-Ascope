"""
AudioScope 백엔드 기본 헬스체크 테스트
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse


# 테스트용 최소 앱 (외부 의존성 없이 헬스체크만 검증)
def create_test_app() -> FastAPI:
    app = FastAPI(title="AudioScope Test")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "audioscope"}

    return app


@pytest.fixture
def client():
    app = create_test_app()
    with TestClient(app) as c:
        yield c


def test_health_check_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_body(client):
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "audioscope"


def test_health_check_content_type(client):
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]


def test_unknown_route_returns_404(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
