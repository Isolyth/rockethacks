"""Tests for main.py — FastAPI app configuration."""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestApp:
    def test_root_endpoint(self):
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    def test_root_returns_json(self):
        client = TestClient(app)
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_nonexistent_route_returns_404(self):
        client = TestClient(app)
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_cors_middleware_present(self):
        """Verify CORS headers are returned for allowed origins."""
        client = TestClient(app)
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_disallowed_origin(self):
        """Non-allowed origins should not get CORS headers."""
        client = TestClient(app)
        response = client.options(
            "/",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") != "http://evil.com"

    def test_analyze_router_mounted(self):
        """The /ws/analyze WebSocket route should exist."""
        routes = [route.path for route in app.routes]
        assert "/ws/analyze" in routes

    def test_get_on_websocket_route_fails(self):
        """A regular GET on /ws/analyze should not return 200."""
        client = TestClient(app)
        response = client.get("/ws/analyze")
        # WebSocket endpoint returns 403 or similar for non-websocket requests
        assert response.status_code != 200

    def test_post_on_root_not_allowed(self):
        client = TestClient(app)
        response = client.post("/")
        assert response.status_code == 405
