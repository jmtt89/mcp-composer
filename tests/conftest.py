# Test configuration and shared fixtures
import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
import httpx

from src.config import Config
from src.composer import Composer
from src.downstream_controller import DownstreamController
from src.domain.downstream_server import DownstreamMCPServerConfig
from src.domain.server_kit import ServerKit


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_mcp_servers_config():
    """Test MCP servers configuration."""
    return {
        "mcpServers": {
            "test-server-1": {
                "command": "echo",
                "args": ["test"]
            },
            "test-server-2": {
                "url": "http://localhost:9001/mcp"
            },
            "test-stdio-server": {
                "command": "python",
                "args": ["-c", "print('test')"],
                "env": {"TEST_VAR": "test_value"}
            }
        }
    }


@pytest.fixture
def temp_config_file(test_mcp_servers_config):
    """Create a temporary MCP servers config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_mcp_servers_config, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def test_config(temp_config_file):
    """Test configuration with temporary config file."""
    import os
    # Store original env vars
    original_config_path = os.environ.get("MCP_SERVERS_CONFIG_PATH")
    original_proxy_url = os.environ.get("MCP_COMPOSER_PROXY_URL")
    original_host = os.environ.get("HOST")
    original_port = os.environ.get("PORT")
    
    # Set test env vars
    os.environ["MCP_SERVERS_CONFIG_PATH"] = temp_config_file
    os.environ["MCP_COMPOSER_PROXY_URL"] = "http://localhost:8000"
    os.environ["HOST"] = "127.0.0.1"
    os.environ["PORT"] = "8000"
    
    config = Config()
    
    yield config
    
    # Restore original env vars
    if original_config_path is not None:
        os.environ["MCP_SERVERS_CONFIG_PATH"] = original_config_path
    else:
        os.environ.pop("MCP_SERVERS_CONFIG_PATH", None)
    
    if original_proxy_url is not None:
        os.environ["MCP_COMPOSER_PROXY_URL"] = original_proxy_url
    else:
        os.environ.pop("MCP_COMPOSER_PROXY_URL", None)
        
    if original_host is not None:
        os.environ["HOST"] = original_host
    else:
        os.environ.pop("HOST", None)
        
    if original_port is not None:
        os.environ["PORT"] = original_port
    else:
        os.environ.pop("PORT", None)


@pytest.fixture
def mock_downstream_server_configs():
    """Mock downstream server configurations."""
    return [
        DownstreamMCPServerConfig(
            name="test-server-1",
            command="echo",
            args=["test"]
        ),
        DownstreamMCPServerConfig(
            name="test-server-2",
            url="http://localhost:9001/mcp"
        )
    ]


@pytest.fixture
async def mock_downstream_controller(mock_downstream_server_configs):
    """Mock downstream controller for testing."""
    controller = DownstreamController(mock_downstream_server_configs)
    
    # Mock the initialization
    controller._initialized = True
    controller._all_servers_tools = []
    controller._servers_map = {}
    controller._tools_map = {}
    
    # Add mock servers and tools
    from src.domain.downstream_server import DownstreamMCPServer, DownstreamMCPServerTool
    from mcp.types import Tool
    
    for config in mock_downstream_server_configs:
        # Mock server
        mock_server = MagicMock(spec=DownstreamMCPServer)
        mock_server.get_control_name.return_value = config.name
        mock_server.config = config
        
        # Mock tools for each server
        mock_tools = []
        for i in range(2):  # 2 tools per server
            tool_name = f"tool_{i+1}"
            mock_tool_obj = Tool(
                name=tool_name,
                description=f"Test tool {i+1} for {config.name}",
                inputSchema={"type": "object", "properties": {}}
            )
            mock_tool = DownstreamMCPServerTool(config.name, mock_tool_obj)
            mock_tools.append(mock_tool)
            controller._tools_map[mock_tool.control_name] = mock_tool
        
        controller._servers_map[config.name] = mock_server
        controller._all_servers_tools.append((mock_server, mock_tools))
    
    return controller


@pytest.fixture
async def test_composer(test_config, mock_downstream_controller):
    """Test composer instance."""
    composer = Composer(mock_downstream_controller, test_config)
    return composer


@pytest.fixture
async def test_server_kit(test_composer):
    """Test server kit."""
    return test_composer.create_server_kit("test-kit")


@pytest.fixture
async def test_app(test_composer):
    """Test FastAPI application."""
    from src.main import app
    
    # Replace the composer in app state
    app.state.composer = test_composer
    
    return app


@pytest.fixture
async def test_client(test_app):
    """Test client for API testing."""
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
async def async_test_client(test_app):
    """Async test client for API testing."""
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
