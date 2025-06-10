"""Unit tests for downstream server domain models."""
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.domain.downstream_server import (
    DownstreamMCPServerConfig,
    DownstreamMCPServer,
    DownstreamMCPServerTool,
    ConnectionType
)
from mcp.types import Tool


class TestDownstreamMCPServerConfig:
    """Test cases for DownstreamMCPServerConfig."""

    def test_stdio_server_config(self):
        """Test stdio server configuration."""
        config = DownstreamMCPServerConfig(
            name="test-stdio",
            command="python",
            args=["-m", "test_module"],
            env={"TEST_VAR": "value"}
        )
        
        assert config.name == "test-stdio"
        assert config.command == "python"
        assert config.args == ["-m", "test_module"]
        assert config.env == {"TEST_VAR": "value"}
        assert config.url is None
        assert config.get_connection_type() == ConnectionType.STDIO

    def test_sse_server_config(self):
        """Test SSE server configuration."""
        config = DownstreamMCPServerConfig(
            name="test-sse",
            url="http://localhost:8001/mcp"
        )
        
        assert config.name == "test-sse"
        assert config.url == "http://localhost:8001/mcp"
        assert config.command is None
        assert config.args is None
        assert config.env is None
        assert config.get_connection_type() == ConnectionType.SSE

    def test_invalid_config_no_command_or_url(self):
        """Test invalid configuration with neither command nor URL."""
        config = DownstreamMCPServerConfig(name="invalid")
        
        with pytest.raises(ValueError, match="Invalid server config"):
            config.get_connection_type()

    def test_config_with_both_command_and_url(self):
        """Test configuration with both command and URL (should prefer stdio)."""
        config = DownstreamMCPServerConfig(
            name="both",
            command="python",
            url="http://localhost:8001/mcp"
        )
        
        # Should return STDIO since command is checked first
        assert config.get_connection_type() == ConnectionType.STDIO

    def test_config_defaults(self):
        """Test default values for optional fields."""
        config = DownstreamMCPServerConfig(
            name="minimal",
            command="python"
        )
        
        assert config.args is None
        assert config.env is None
        assert config.url is None

    def test_pydantic_model_validation(self):
        """Test Pydantic model validation."""
        # Test valid config
        config = DownstreamMCPServerConfig(
            name="valid",
            command="python"
        )
        assert config.name == "valid"
        
        # Test model serialization
        config_dict = config.model_dump()
        assert config_dict["name"] == "valid"
        assert config_dict["command"] == "python"


class TestDownstreamMCPServerTool:
    """Test cases for DownstreamMCPServerTool."""

    def test_tool_creation(self):
        """Test creating a downstream MCP server tool."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            inputSchema={"type": "object", "properties": {"param": {"type": "string"}}}
        )
        
        server_tool = DownstreamMCPServerTool("test-server", tool)
        
        assert server_tool.server_control_name == "test-server"
        assert server_tool.control_name == "test-server-test_tool"
        assert server_tool.tool == tool

    def test_to_new_name_tool(self):
        """Test converting to new name tool."""
        original_tool = Tool(
            name="original_name",
            description="Test description",
            inputSchema={"type": "object"}
        )
        
        server_tool = DownstreamMCPServerTool("my-server", original_tool)
        new_tool = server_tool.to_new_name_tool()
        
        assert new_tool.name == "my-server-original_name"
        assert new_tool.description == "Test description"
        assert new_tool.inputSchema == {"type": "object"}

    def test_tool_control_name_generation(self):
        """Test control name generation for tools."""
        test_cases = [
            ("server1", "tool1", "server1-tool1"),
            ("complex-server", "complex_tool", "complex-server-complex_tool"),
            ("s", "t", "s-t"),
        ]
        
        for server_name, tool_name, expected_control_name in test_cases:
            tool = Tool(name=tool_name, description="test", inputSchema={})
            server_tool = DownstreamMCPServerTool(server_name, tool)
            
            assert server_tool.control_name == expected_control_name


class TestDownstreamMCPServer:
    """Test cases for DownstreamMCPServer."""

    def test_server_initialization(self):
        """Test server initialization."""
        config = DownstreamMCPServerConfig(
            name="test-server",
            command="python"
        )
        
        server = DownstreamMCPServer(config)
        
        assert server.config == config
        assert server.session is None
        assert server.read_stream is None
        assert server.write_stream is None
        assert server._control_name is None

    def test_get_control_name_before_initialization(self):
        """Test getting control name before initialization should fail."""
        config = DownstreamMCPServerConfig(
            name="test-server",
            command="python"
        )
        server = DownstreamMCPServer(config)
        
        with pytest.raises(AssertionError):
            server.get_control_name()

    def test_get_control_name_after_mock_initialization(self):
        """Test getting control name after mock initialization."""
        config = DownstreamMCPServerConfig(
            name="test-server",
            command="python"
        )
        server = DownstreamMCPServer(config)
        server._control_name = "test-server"
        
        assert server.get_control_name() == "test-server"

    async def test_shutdown(self):
        """Test server shutdown."""
        config = DownstreamMCPServerConfig(
            name="test-server",
            command="python"
        )
        server = DownstreamMCPServer(config)
        
        # Mock some initialized state
        server.session = MagicMock()
        server.read_stream = MagicMock()
        server.write_stream = MagicMock()
        
        await server.shutdown()
        
        assert server.session is None
        assert server.read_stream is None
        assert server.write_stream is None

    async def test_list_tools_without_session(self):
        """Test listing tools without initialized session should fail."""
        config = DownstreamMCPServerConfig(
            name="test-server",
            command="python"
        )
        server = DownstreamMCPServer(config)
        server._control_name = "test-server"
        
        with pytest.raises(ValueError, match="Server not initialized"):
            await server.list_tools()

    async def test_list_tools_without_control_name(self):
        """Test listing tools without control name should fail."""
        config = DownstreamMCPServerConfig(
            name="test-server",
            command="python"
        )
        server = DownstreamMCPServer(config)
        
        with pytest.raises(AssertionError):
            await server.list_tools()

    async def test_list_tools_with_mock_session(self):
        """Test listing tools with mock session."""
        config = DownstreamMCPServerConfig(
            name="test-server",
            command="python"
        )
        server = DownstreamMCPServer(config)
        server._control_name = "test-server"
        
        # Mock session and its list_tools method
        mock_session = MagicMock()
        mock_tools_result = MagicMock()
        mock_tools_result.tools = [
            Tool(name="tool1", description="Test tool 1", inputSchema={}),
            Tool(name="tool2", description="Test tool 2", inputSchema={})
        ]
        mock_session.list_tools = AsyncMock(return_value=mock_tools_result)
        server.session = mock_session
        
        tools = await server.list_tools()
        
        assert len(tools) == 2
        assert tools[0].server_control_name == "test-server"
        assert tools[0].control_name == "test-server-tool1"
        assert tools[1].server_control_name == "test-server"
        assert tools[1].control_name == "test-server-tool2"
        
        mock_session.list_tools.assert_called_once()


class TestConnectionType:
    """Test cases for ConnectionType enum."""

    def test_connection_type_values(self):
        """Test connection type enum values."""
        assert ConnectionType.STDIO == "stdio"
        assert ConnectionType.SSE == "sse"

    def test_connection_type_comparison(self):
        """Test connection type comparison."""
        assert ConnectionType.STDIO != ConnectionType.SSE
        assert ConnectionType.STDIO == "stdio"
        assert ConnectionType.SSE == "sse"
