"""Test liveness probe and basic health endpoints in API."""

import pytest
from unittest.mock import patch, Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import v1_api_router


def test_liveness_probe_basic():
    """Test that basic liveness probe works."""
    app = FastAPI()
    app.include_router(v1_api_router)
    client = TestClient(app)
    
    response = client.get("/api/v1/health/live")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert "uptime" in data


def test_basic_health_check():
    """Test basic health check endpoint."""
    app = FastAPI()
    app.include_router(v1_api_router)
    client = TestClient(app)
    
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_liveness_probe_exception_handling():
    """Test liveness probe exception handling - covers lines 45-47."""
    app = FastAPI()
    app.include_router(v1_api_router)
    client = TestClient(app)
    
    # Mock _app_start_time to be an object that will cause TypeError on subtraction
    with patch('src.api._app_start_time', "invalid_time"):
        response = client.get("/api/v1/health/live")
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"] == "Application is not alive"
