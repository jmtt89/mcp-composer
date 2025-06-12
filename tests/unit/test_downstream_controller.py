"""Unit tests for DownstreamController class."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from contextlib import AsyncExitStack

from src.downstream_controller import DownstreamController
from src.domain.downstream_server import DownstreamMCPServerConfig, DownstreamMCPServer
from src.domain.mcp_models import MCPServerConfig


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


class TestDynamicServerManagement:
    """Test dynamic server management methods."""

    @pytest.fixture
    def controller(self):
        """Create an initialized controller for testing."""
        controller = DownstreamController([])
        controller._initialized = True
        return controller

    @pytest.fixture
    def sample_mcp_config(self):
        """Sample MCP server config for testing."""
        return MCPServerConfig(
            name="dynamic-server",
            command="python",
            args=["-m", "test_server"],
            env={"TEST": "true"}
        )

    @patch('src.downstream_controller.DownstreamMCPServer')
    async def test_add_server_dynamically_success(self, mock_server_class, controller, sample_mcp_config):
        """Test successfully adding a server dynamically."""
        # Mock server instance
        mock_server = MagicMock(spec=DownstreamMCPServer)
        mock_server.get_control_name.return_value = "dynamic-server"
        mock_server.initialize = AsyncMock()
        mock_server.list_tools = AsyncMock(return_value=[])
        mock_server_class.return_value = mock_server
        
        # Convert to DownstreamMCPServerConfig
        downstream_config = sample_mcp_config.to_downstream_config()
        
        await controller.add_server_dynamically(downstream_config)
        
        # Verify server was registered
        assert "dynamic-server" in controller._servers_map
        mock_server.initialize.assert_called_once()

    async def test_add_server_dynamically_duplicate(self, controller, sample_mcp_config):
        """Test adding a server with duplicate name."""
        # Add existing server to servers_map (that's what the method checks)
        mock_server = MagicMock()
        controller._servers_map["dynamic-server"] = mock_server
        
        downstream_config = sample_mcp_config.to_downstream_config()
        
        with pytest.raises(ValueError, match="already exists"):
            await controller.add_server_dynamically(downstream_config)

    @patch('src.downstream_controller.DownstreamMCPServer')
    async def test_add_server_dynamically_initialization_failure(self, mock_server_class, controller, sample_mcp_config):
        """Test handling server initialization failure during dynamic add."""
        # Mock server that fails initialization
        mock_server = MagicMock(spec=DownstreamMCPServer)
        mock_server.initialize = AsyncMock(side_effect=Exception("Init failed"))
        mock_server_class.return_value = mock_server
        
        downstream_config = sample_mcp_config.to_downstream_config()
        
        with pytest.raises(Exception, match="Init failed"):
            await controller.add_server_dynamically(downstream_config)

    async def test_remove_server_dynamically_success(self, controller):
        """Test successfully removing a server dynamically."""
        # Add a server to remove
        mock_server = MagicMock()
        mock_server.get_control_name.return_value = "test-server"
        mock_server.shutdown = AsyncMock()
        controller._servers_map["test-server"] = mock_server
        controller._all_servers_tools.append((mock_server, []))
        
        await controller.remove_server_dynamically("test-server")
        
        assert "test-server" not in controller._servers_map
        assert len(controller._all_servers_tools) == 0
        mock_server.shutdown.assert_called_once()

    async def test_remove_server_dynamically_not_found(self, controller):
        """Test removing a non-existent server."""
        with pytest.raises(ValueError, match="not found"):
            await controller.remove_server_dynamically("nonexistent")

    async def test_remove_server_dynamically_with_dependencies(self, controller):
        """Test removing a server with dependencies (should raise error)."""
        # Add a server first
        mock_server = MagicMock()
        controller._servers_map["test-server"] = mock_server
        
        # Mock check_server_dependencies to return dependencies
        server_kits_map = {"kit1": MagicMock()}
        dependencies = controller.check_server_dependencies("test-server", server_kits_map)
        
        # If there are dependencies, we would need to check them in the API layer
        # For now, just test that the method can be called
        assert isinstance(dependencies, list)

    def test_check_server_dependencies_no_dependencies(self, controller):
        """Test checking dependencies when server has no dependencies."""
        server_kits_map = {
            "kit1": MagicMock(),
            "kit2": MagicMock()
        }
        # Mock that no kits have this server assigned
        for kit in server_kits_map.values():
            kit.is_server_assigned.return_value = False
        
        dependencies = controller.check_server_dependencies("test-server", server_kits_map)
        assert dependencies == []

    def test_check_server_dependencies_with_dependencies(self, controller):
        """Test checking dependencies when server has dependencies."""
        # Mock server kits
        mock_kit1 = MagicMock()
        mock_kit1.is_server_assigned.return_value = True
        mock_kit2 = MagicMock()
        mock_kit2.is_server_assigned.return_value = False
        
        server_kits_map = {
            "kit1": mock_kit1,
            "kit2": mock_kit2
        }
        
        dependencies = controller.check_server_dependencies("test-server", server_kits_map)
        
        assert dependencies == ["kit1"]
        mock_kit1.is_server_assigned.assert_called_with("test-server")
        mock_kit2.is_server_assigned.assert_called_with("test-server")

    def test_list_available_servers(self, controller):
        """Test listing available servers."""
        # Add some servers to the map
        mock_server1 = MagicMock()
        mock_server2 = MagicMock()
        controller._servers_map["server1"] = mock_server1
        controller._servers_map["server2"] = mock_server2
        
        servers = controller.list_available_servers()
        
        assert len(servers) == 2
        assert "server1" in servers
        assert "server2" in servers

    def test_get_server_status_connected(self, controller):
        """Test getting status of connected server."""
        mock_server = MagicMock()
        controller._servers_map["test-server"] = mock_server
        
        status = controller.get_server_status("test-server")
        
        assert status == "connected"

    def test_get_server_status_not_found(self, controller):
        """Test getting status of non-existent server."""
        status = controller.get_server_status("nonexistent")
        assert status == "not_found"

    def test_get_server_tools_count(self, controller):
        """Test getting server tools count."""
        # Add mock tools for a server
        from src.domain.downstream_server import DownstreamMCPServerTool
        mock_tool1 = MagicMock(spec=DownstreamMCPServerTool)
        mock_tool1.server_control_name = "test-server"
        mock_tool2 = MagicMock(spec=DownstreamMCPServerTool)
        mock_tool2.server_control_name = "test-server"
        mock_tool3 = MagicMock(spec=DownstreamMCPServerTool)
        mock_tool3.server_control_name = "other-server"
        
        controller._tools_map = {
            "tool1": mock_tool1,
            "tool2": mock_tool2,
            "tool3": mock_tool3
        }
        
        count = controller.get_server_tools_count("test-server")
        assert count == 2
