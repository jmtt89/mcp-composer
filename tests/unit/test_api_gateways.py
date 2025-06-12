"""Test gateways endpoints in API."""

import pytest
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import v1_api_router


def test_list_gateways():
    """Test listing gateways endpoint."""
    app = FastAPI()
    app.include_router(v1_api_router)
    
    # Mock composer with gateways
    mock_composer = Mock()
    mock_composer.list_gateways.return_value = []
    
    # Set the composer in app state
    app.state.composer = mock_composer
    
    client = TestClient(app)
    response = client.get("/api/v1/gateways")
    
    assert response.status_code == 200
    data = response.json()
    assert data == []
