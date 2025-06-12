"""Test server kits endpoints in API."""

import pytest
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import v1_api_router


def test_list_server_kits():
    """Test listing server kits endpoint."""
    app = FastAPI()
    app.include_router(v1_api_router)
    
    # Mock composer with empty server kits list
    mock_composer = Mock()
    mock_composer.list_server_kits.return_value = []
    
    # Set the composer in app state
    app.state.composer = mock_composer
    
    client = TestClient(app)
    response = client.get("/api/v1/kits")
    
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_get_server_kit_not_found():
    """Test getting a server kit that doesn't exist."""
    app = FastAPI()
    app.include_router(v1_api_router)
    
    # Mock composer to raise ValueError
    mock_composer = Mock()
    mock_composer.get_server_kit.side_effect = ValueError("Server kit 'nonexistent' not found")
    
    # Set the composer in app state
    app.state.composer = mock_composer
    
    client = TestClient(app)
    response = client.get("/api/v1/kits/nonexistent")
    
    assert response.status_code == 404
    assert "Server kit 'nonexistent' not found" in response.json()["detail"]
