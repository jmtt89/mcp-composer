"""Test MCP servers endpoints in API."""

import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import v1_api_router


def test_list_mcp_servers():
    """Test listing MCP servers endpoint."""
    app = FastAPI()
    app.include_router(v1_api_router)
    
    # Mock composer and downstream controller
    mock_composer = Mock()
    mock_downstream_controller = Mock()
    mock_composer.downstream_controller = mock_downstream_controller
    mock_composer.server_kits_map = {}
    
    # Mock the list of server names (empty list to avoid complex model creation)
    mock_downstream_controller.list_available_servers.return_value = []
    
    # Set the composer in app state
    app.state.composer = mock_composer
    
    client = TestClient(app)
    response = client.get("/api/v1/mcp")
    
    assert response.status_code == 200
    data = response.json()
    assert "servers" in data
    assert "total_count" in data
    assert data["total_count"] == 0
    assert data["servers"] == []


def test_list_mcp_servers_with_servers():
    """Test listing MCP servers with actual servers."""
    app = FastAPI()
    app.include_router(v1_api_router)
    
    # Mock composer and downstream controller
    mock_composer = Mock()
    mock_downstream_controller = Mock()
    mock_composer.downstream_controller = mock_downstream_controller
    mock_composer.server_kits_map = {}
    
    # Mock the list of server names with actual servers
    mock_downstream_controller.list_available_servers.return_value = ["test-server"]
    
    # Mock MCPServerResponse.from_config_and_controller to return a simple dict
    with patch("src.api.MCPServerResponse") as mock_mcp_response:
        mock_server_instance = Mock()
        mock_server_instance.dict.return_value = {"name": "test-server", "status": "connected"}
        mock_mcp_response.from_config_and_controller.return_value = mock_server_instance
        
        # Mock MCPServerListResponse
        with patch("src.api.MCPServerListResponse") as mock_list_response:
            mock_list_response.return_value.dict.return_value = {
                "servers": [{"name": "test-server", "status": "connected"}],
                "total_count": 1
            }
            
            # Set the composer in app state
            app.state.composer = mock_composer
            
            client = TestClient(app)
            response = client.get("/api/v1/mcp")
            
            assert response.status_code == 200
            # Verify that the mocked methods were called
            mock_mcp_response.from_config_and_controller.assert_called_once()
            mock_list_response.assert_called_once()


def test_create_mcp_server_value_error():
    """Test creating MCP server with invalid config that raises ValueError."""
    app = FastAPI()
    app.include_router(v1_api_router)
    
    # Mock composer and downstream controller
    mock_composer = Mock()
    mock_composer.server_kits_map = {}
    
    # Set the composer in app state
    app.state.composer = mock_composer
    
    client = TestClient(app)
    
    # Send POST request with invalid JSON to trigger validation error
    response = client.post("/api/v1/mcp", json={
        "name": "",  # Invalid empty name
        "command": "",  # Invalid empty command
        "args": "not-a-list",  # Invalid type
        "env": "not-a-dict"  # Invalid type
    })
    
    # Should get validation error from Pydantic
    assert response.status_code == 422


def test_get_mcp_server_not_found():
    """Test getting a specific MCP server that doesn't exist - covers lines 286-287."""
    app = FastAPI()
    app.include_router(v1_api_router)
    
    # Mock composer and downstream controller
    mock_composer = Mock()
    mock_downstream_controller = Mock()
    mock_composer.downstream_controller = mock_downstream_controller
    
    # Mock empty server list
    mock_downstream_controller.list_available_servers.return_value = []
    
    # Set the composer in app state
    app.state.composer = mock_composer
    
    client = TestClient(app)
    response = client.get("/api/v1/mcp/nonexistent-server")
    
    assert response.status_code == 404
    data = response.json()
    assert "MCP server 'nonexistent-server' not found" in data["detail"]
