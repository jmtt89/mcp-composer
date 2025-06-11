"""Unit tests for DownstreamController class."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from contextlib import AsyncExitStack

from src.downstream_controller import DownstreamController
from src.domain.downstream_server import DownstreamMCPServerConfig, DownstreamMCPServer


class TestDownstreamController:
    """Test cases for DownstreamController class."""

    def test_controller_initialization(self, mock_downstream_server_configs):
        """Test controller initialization."""
        controller = DownstreamController(mock_downstream_server_configs)
        
        assert controller.configs == mock_downstream_server_configs
        assert controller._all_servers_tools == []
        assert controller._servers_map == {}
        assert controller._tools_map == {}
        assert controller._initialized is False
        assert controller.exit_stack is not None

    def test_is_initialized_false(self, mock_downstream_server_configs):
        """Test is_initialized returns False before initialization."""
        controller = DownstreamController(mock_downstream_server_configs)
        
        assert controller.is_initialized() is False

    def test_is_initialized_true(self, mock_downstream_server_configs):
        """Test is_initialized returns True after initialization."""
        controller = DownstreamController(mock_downstream_server_configs)
        controller._initialized = True
        
        assert controller.is_initialized() is True

    @patch('src.downstream_controller.DownstreamMCPServer')
    async def test_register_downstream_mcp_server(self, mock_server_class, mock_downstream_server_configs):
        """Test registering a downstream MCP server."""
        controller = DownstreamController([])
        
        # Mock server instance
        mock_server = MagicMock(spec=DownstreamMCPServer)
        mock_server.get_control_name.return_value = "test-server"
        mock_server.initialize = AsyncMock()
        mock_server.list_tools = AsyncMock(return_value=[])
        mock_server_class.return_value = mock_server
        
        config = mock_downstream_server_configs[0]
        await controller.register_downstream_mcp_server(config)
        
        # Verify server was registered
        assert "test-server" in controller._servers_map
        assert controller._servers_map["test-server"] == mock_server
        assert len(controller._all_servers_tools) == 1
        
        # Verify server was initialized
        mock_server.initialize.assert_called_once()
        mock_server.list_tools.assert_called_once()

    @patch('src.downstream_controller.DownstreamMCPServer')
    async def test_register_server_with_tools(self, mock_server_class, mock_downstream_server_configs):
        """Test registering a server with tools."""
        controller = DownstreamController([])
        
        # Mock tools
        from src.domain.downstream_server import DownstreamMCPServerTool
        from mcp.types import Tool
        
        mock_tool1 = MagicMock(spec=DownstreamMCPServerTool)
        mock_tool1.control_name = "test-server-tool1"
        mock_tool2 = MagicMock(spec=DownstreamMCPServerTool)
        mock_tool2.control_name = "test-server-tool2"
        
        # Mock server instance
        mock_server = MagicMock(spec=DownstreamMCPServer)
        mock_server.get_control_name.return_value = "test-server"
        mock_server.initialize = AsyncMock()
        mock_server.list_tools = AsyncMock(return_value=[mock_tool1, mock_tool2])
        mock_server_class.return_value = mock_server
        
        config = mock_downstream_server_configs[0]
        await controller.register_downstream_mcp_server(config)
        
        # Verify tools were registered
        assert "test-server-tool1" in controller._tools_map
        assert "test-server-tool2" in controller._tools_map
        assert controller._tools_map["test-server-tool1"] == mock_tool1
        assert controller._tools_map["test-server-tool2"] == mock_tool2

    @patch('src.downstream_controller.DownstreamMCPServer')
    async def test_initialize(self, mock_server_class, mock_downstream_server_configs):
        """Test controller initialization."""
        controller = DownstreamController(mock_downstream_server_configs)
        
        # Mock server instances
        mock_servers = []
        for i, config in enumerate(mock_downstream_server_configs):
            mock_server = MagicMock(spec=DownstreamMCPServer)
            mock_server.get_control_name.return_value = config.name
            mock_server.initialize = AsyncMock()
            mock_server.list_tools = AsyncMock(return_value=[])
            mock_servers.append(mock_server)
        
        mock_server_class.side_effect = mock_servers
        
        await controller.initialize()
        
        assert controller._initialized is True
        assert len(controller._servers_map) == len(mock_downstream_server_configs)
        
        # Verify all servers were initialized
        for mock_server in mock_servers:
            mock_server.initialize.assert_called_once()

    @patch('src.downstream_controller.DownstreamMCPServer')
    async def test_shutdown(self, mock_server_class, mock_downstream_server_configs):
        """Test controller shutdown."""
        controller = DownstreamController([])
        
        # Add some mock servers
        mock_server1 = MagicMock(spec=DownstreamMCPServer)
        mock_server1.shutdown = AsyncMock()
        mock_server2 = MagicMock(spec=DownstreamMCPServer)
        mock_server2.shutdown = AsyncMock()
        
        controller._all_servers_tools = [  # type: ignore
            (mock_server1, []),
            (mock_server2, [])
        ]
        
        # Mock exit stack
        controller.exit_stack = MagicMock()
        controller.exit_stack.aclose = AsyncMock()
        
        await controller.shutdown()
        
        # Verify all servers were shutdown
        mock_server1.shutdown.assert_called_once()
        mock_server2.shutdown.assert_called_once()
        controller.exit_stack.aclose.assert_called_once()

    def test_list_all_servers_tools(self, mock_downstream_server_configs):
        """Test listing all servers and tools."""
        controller = DownstreamController(mock_downstream_server_configs)
        
        # Add some mock data
        mock_server = MagicMock()
        mock_tools = [MagicMock(), MagicMock()]
        controller._all_servers_tools = [(mock_server, mock_tools)]  # type: ignore
        
        result = controller.list_all_servers_tools()
        
        assert result == [(mock_server, mock_tools)]

    def test_get_tool_by_control_name(self, mock_downstream_server_configs):
        """Test getting tool by control name."""
        controller = DownstreamController(mock_downstream_server_configs)
        
        mock_tool = MagicMock()
        controller._tools_map["test-tool"] = mock_tool
        
        result = controller.get_tool_by_control_name("test-tool")
        
        assert result == mock_tool

    def test_get_tool_by_control_name_not_found(self, mock_downstream_server_configs):
        """Test getting non-existent tool by control name."""
        controller = DownstreamController(mock_downstream_server_configs)
        
        with pytest.raises(KeyError):
            controller.get_tool_by_control_name("non-existent")

    def test_get_server_by_control_name(self, mock_downstream_server_configs):
        """Test getting server by control name."""
        controller = DownstreamController(mock_downstream_server_configs)
        
        mock_server = MagicMock()
        controller._servers_map["test-server"] = mock_server
        
        result = controller.get_server_by_control_name("test-server")
        
        assert result == mock_server

    def test_get_server_by_control_name_not_found(self, mock_downstream_server_configs):
        """Test getting non-existent server by control name."""
        controller = DownstreamController(mock_downstream_server_configs)
        
        with pytest.raises(KeyError):
            controller.get_server_by_control_name("non-existent")

    async def test_controller_with_empty_configs(self):
        """Test controller with empty configurations."""
        controller = DownstreamController([])
        
        await controller.initialize()
        
        assert controller._initialized is True
        assert controller._all_servers_tools == []
        assert controller._servers_map == {}
        assert controller._tools_map == {}

    @patch('src.downstream_controller.DownstreamMCPServer')
    async def test_asyncio_lock_usage(self, mock_server_class, mock_downstream_server_configs):
        """Test that asyncio lock is properly used during initialization."""
        controller = DownstreamController(mock_downstream_server_configs)
        
        # Mock server instance
        mock_server = MagicMock(spec=DownstreamMCPServer)
        mock_server.get_control_name.return_value = "test-server"
        mock_server.initialize = AsyncMock()
        mock_server.list_tools = AsyncMock(return_value=[])
        mock_server_class.return_value = mock_server
        
        # Verify that the lock is acquired during initialization
        with patch.object(controller, '_asyncio_lock') as mock_lock:
            mock_lock.__aenter__ = AsyncMock()
            mock_lock.__aexit__ = AsyncMock()
            
            await controller.initialize()
            
            # The lock context manager should have been used
            mock_lock.__aenter__.assert_called()
            mock_lock.__aexit__.assert_called()

    @patch('src.downstream_controller.DownstreamMCPServer')
    async def test_server_initialization_failure(self, mock_server_class, mock_downstream_server_configs):
        """Test handling of server initialization failure."""
        controller = DownstreamController(mock_downstream_server_configs[:1])
        
        # Mock server that fails during initialization
        mock_server = MagicMock(spec=DownstreamMCPServer)
        mock_server.initialize = AsyncMock(side_effect=Exception("Initialization failed"))
        mock_server_class.return_value = mock_server
        
        # Initialization should propagate the exception
        with pytest.raises(Exception, match="Initialization failed"):
            await controller.initialize()
        
        # Controller should not be marked as initialized
        assert controller._initialized is False
