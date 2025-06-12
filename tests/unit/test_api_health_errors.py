"""Tests for API health check error handling."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api import v1_api_router


def test_readiness_probe_exception_handling():
    """Test readiness probe handles exceptions correctly."""
    # Create a minimal FastAPI app with the router
    app = FastAPI()
    app.include_router(v1_api_router)
    
    client = TestClient(app)
    
    # Mock composer with downstream_controller that raises exception
    mock_composer = Mock()
    mock_composer.downstream_controller.is_initialized.side_effect = RuntimeError("Controller error")
    app.state.composer = mock_composer
    
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "Application is not ready"


def test_startup_probe_exception_handling():
    """Test startup probe handles exceptions correctly."""
    # Create a minimal FastAPI app with the router
    app = FastAPI()
    app.include_router(v1_api_router)
    
    client = TestClient(app)
    
    # Mock composer with downstream_controller that raises exception
    mock_composer = Mock()
    mock_composer.downstream_controller.is_initialized.side_effect = RuntimeError("Controller error")
    app.state.composer = mock_composer
    
    response = client.get("/api/v1/health/startup")
    assert response.status_code == 503
    assert response.json()["detail"] == "Application startup failed"
