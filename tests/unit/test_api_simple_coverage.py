"""Test simple API endpoints for coverage."""

import pytest
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import v1_api_router


def test_basic_endpoints_simple():
    """Test basic endpoints without complex mocking."""
    app = FastAPI()
    app.include_router(v1_api_router)
    client = TestClient(app)
    
    # Test basic health endpoint (already working)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    # Test liveness endpoint (already working)
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
