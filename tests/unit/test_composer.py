"""Unit tests for Composer class."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.composer import Composer
from src.downstream_controller import DownstreamController
from src.config import Config
from src.domain.server_kit import ServerKit
from src.gateway import Gateway


class TestComposer:
    """Test cases for Composer class."""

    def test_composer_initialization(self, test_config, mock_downstream_controller):
        """Test composer initialization."""
        composer = Composer(mock_downstream_controller, test_config)
        
        assert composer.downstream_controller == mock_downstream_controller
        assert composer.config == test_config
        assert composer.server_kits_map == {}
        assert composer.gateway_map == {}
        assert composer._asgi_app is not None

    async def test_list_server_kits_empty(self, test_composer):
        """Test listing server kits when none exist."""
        kits = await test_composer.list_server_kits()
        
        assert kits == []

    async def test_list_server_kits_with_data(self, test_composer):
        """Test listing server kits with existing data."""
        # Create some test kits
        kit1 = test_composer.create_server_kit("kit1")
        kit2 = test_composer.create_server_kit("kit2")
        
        kits = await test_composer.list_server_kits()
        
        assert len(kits) == 2
        assert kit1 in kits
        assert kit2 in kits

    async def test_get_server_kit(self, test_composer):
        """Test getting a specific server kit."""
        kit = test_composer.create_server_kit("test-kit")
        
        retrieved_kit = await test_composer.get_server_kit("test-kit")
        
        assert retrieved_kit == kit

    async def test_get_server_kit_not_found(self, test_composer):
        """Test getting a non-existent server kit."""
        with pytest.raises(ValueError, match="Server kit 'non-existent' not found"):
            await test_composer.get_server_kit("non-existent")

    def test_create_server_kit(self, test_composer):
        """Test creating a new server kit."""
        kit = test_composer.create_server_kit("new-kit")
        
        assert kit.name == "new-kit"
        assert kit.enabled is True
        assert "new-kit" in test_composer.server_kits_map
        assert test_composer.server_kits_map["new-kit"] == kit

    def test_create_server_kit_with_disabled_default(self, test_composer):
        """Test creating a server kit with disabled default."""
        kit = test_composer.create_server_kit("disabled-kit", enabled=False)
        
        assert kit.name == "disabled-kit"
        assert kit.enabled is True  # Kit is always enabled by default
        # But individual servers and tools should be disabled
        for server_enabled in kit.servers_enabled.values():
            assert server_enabled is False
        for tool_enabled in kit.tools_enabled.values():
            assert tool_enabled is False

    def test_create_server_kit_without_controller(self, test_config):
        """Test creating server kit without initialized controller."""
        controller = MagicMock()
        controller.is_initialized.return_value = False
        
        composer = Composer(controller, test_config)
        
        with pytest.raises(ValueError, match="Downstream controller not set or not initialized"):
            composer.create_server_kit("test-kit")

    def test_create_server_kit_populates_servers_and_tools(self, test_composer):
        """Test that creating a server kit populates servers and tools."""
        kit = test_composer.create_server_kit("populated-kit")
        
        # Should have servers from mock controller
        assert len(kit.servers_enabled) == 2
        assert "test-server-1" in kit.servers_enabled
        assert "test-server-2" in kit.servers_enabled
        
        # Should have tools from mock controller (2 tools per server)
        assert len(kit.tools_enabled) == 4
        
        # Check hierarchy mapping
        assert len(kit.servers_tools_hierarchy_map) == 2
        for server_name, tools in kit.servers_tools_hierarchy_map.items():
            assert len(tools) == 2  # 2 tools per server

    async def test_disable_server_kit(self, test_composer):
        """Test disabling a server kit."""
        kit = test_composer.create_server_kit("test-kit")
        assert kit.enabled is True
        
        updated_kit = await test_composer.disable_server_kit("test-kit")
        
        assert updated_kit.enabled is False
        assert test_composer.server_kits_map["test-kit"].enabled is False

    async def test_enable_server_kit(self, test_composer):
        """Test enabling a server kit."""
        kit = test_composer.create_server_kit("test-kit")
        kit.enabled = False
        
        updated_kit = await test_composer.enable_server_kit("test-kit")
        
        assert updated_kit.enabled is True
        assert test_composer.server_kits_map["test-kit"].enabled is True

    async def test_disable_server(self, test_composer):
        """Test disabling a server."""
        kit = test_composer.create_server_kit("test-kit")
        server_name = list(kit.servers_enabled.keys())[0]
        
        updated_kit = await test_composer.disable_server("test-kit", server_name)
        
        assert updated_kit.servers_enabled[server_name] is False

    async def test_enable_server(self, test_composer):
        """Test enabling a server."""
        kit = test_composer.create_server_kit("test-kit")
        server_name = list(kit.servers_enabled.keys())[0]
        kit.servers_enabled[server_name] = False
        
        updated_kit = await test_composer.enable_server("test-kit", server_name)
        
        assert updated_kit.servers_enabled[server_name] is True

    async def test_disable_tool(self, test_composer):
        """Test disabling a tool."""
        kit = test_composer.create_server_kit("test-kit")
        tool_name = list(kit.tools_enabled.keys())[0]
        
        updated_kit = await test_composer.disable_tool("test-kit", tool_name)
        
        assert updated_kit.tools_enabled[tool_name] is False

    async def test_enable_tool(self, test_composer):
        """Test enabling a tool."""
        kit = test_composer.create_server_kit("test-kit")
        tool_name = list(kit.tools_enabled.keys())[0]
        kit.tools_enabled[tool_name] = False
        
        updated_kit = await test_composer.enable_tool("test-kit", tool_name)
        
        assert updated_kit.tools_enabled[tool_name] is True

    async def test_list_gateways_empty(self, test_composer):
        """Test listing gateways when none exist."""
        gateways = await test_composer.list_gateways()
        
        assert gateways == []

    async def test_get_gateway(self, test_composer):
        """Test getting a specific gateway."""
        kit = test_composer.create_server_kit("test-kit")
        gateway = await test_composer.add_gateway(kit)
        
        retrieved_gateway = await test_composer.get_gateway("test-kit")
        
        assert retrieved_gateway == gateway

    async def test_get_gateway_not_found(self, test_composer):
        """Test getting a non-existent gateway."""
        with pytest.raises(ValueError, match="Gateway 'non-existent' not found"):
            await test_composer.get_gateway("non-existent")

    @patch('src.composer.Gateway')
    async def test_add_gateway(self, mock_gateway_class, test_composer):
        """Test adding a gateway."""
        kit = test_composer.create_server_kit("test-kit")
        mock_gateway = MagicMock(spec=Gateway)
        mock_gateway.setup = AsyncMock()
        mock_gateway.as_asgi_route.return_value = MagicMock()
        mock_gateway_class.return_value = mock_gateway
        
        gateway = await test_composer.add_gateway(kit)
        
        assert gateway == mock_gateway
        assert "test-kit" in test_composer.gateway_map
        assert test_composer.gateway_map["test-kit"] == mock_gateway
        mock_gateway.setup.assert_called_once()

    async def test_add_gateway_already_exists(self, test_composer):
        """Test adding a gateway that already exists."""
        kit = test_composer.create_server_kit("test-kit")
        await test_composer.add_gateway(kit)
        
        with pytest.raises(ValueError, match="Gateway test-kit already exists"):
            await test_composer.add_gateway(kit)

    @patch('src.composer.Gateway')
    async def test_remove_gateway(self, mock_gateway_class, test_composer):
        """Test removing a gateway."""
        kit = test_composer.create_server_kit("test-kit")
        kit2 = test_composer.create_server_kit("test-kit-2")
        
        mock_gateway = MagicMock(spec=Gateway)
        mock_gateway.setup = AsyncMock()
        mock_gateway.as_asgi_route.return_value = MagicMock()
        mock_gateway_class.return_value = mock_gateway
        
        gateway1 = await test_composer.add_gateway(kit)
        await test_composer.add_gateway(kit2)
        
        # Mock the _remove_route_from_app method to avoid FastAPI routing complexity
        with patch.object(test_composer, '_remove_route_from_app', return_value=True) as mock_remove_route:
            removed_gateway = await test_composer.remove_gateway("test-kit")
        
        assert removed_gateway == gateway1
        assert "test-kit" not in test_composer.gateway_map
        assert "test-kit-2" in test_composer.gateway_map
        mock_remove_route.assert_called_once_with("test-kit")

    async def test_remove_gateway_not_found(self, test_composer):
        """Test removing a non-existent gateway."""
        with pytest.raises(ValueError, match="Gateway non-existent does not exist"):
            await test_composer.remove_gateway("non-existent")

    @patch('src.composer.Gateway')
    async def test_remove_last_gateway(self, mock_gateway_class, test_composer):
        """Test removing the last gateway should fail."""
        kit = test_composer.create_server_kit("test-kit")
        
        mock_gateway = MagicMock(spec=Gateway)
        mock_gateway.setup = AsyncMock()
        mock_gateway.as_asgi_route.return_value = MagicMock()
        mock_gateway_class.return_value = mock_gateway
        
        await test_composer.add_gateway(kit)
        
        with pytest.raises(ValueError, match="Cannot remove the last gateway"):
            await test_composer.remove_gateway("test-kit")

    def test_asgi_gateway_routes(self, test_composer):
        """Test getting ASGI gateway routes."""
        asgi_app = test_composer.asgi_gateway_routes()
        
        assert asgi_app == test_composer._asgi_app

    async def test_operations_on_nonexistent_kit(self, test_composer):
        """Test operations on non-existent kit should fail."""
        with pytest.raises(KeyError):
            await test_composer.disable_server_kit("non-existent")
        
        with pytest.raises(KeyError):
            await test_composer.enable_server_kit("non-existent")
        
        with pytest.raises(KeyError):
            await test_composer.disable_server("non-existent", "server")
        
        with pytest.raises(KeyError):
            await test_composer.enable_server("non-existent", "server")
        
        with pytest.raises(KeyError):
            await test_composer.disable_tool("non-existent", "tool")
        
        with pytest.raises(KeyError):
            await test_composer.enable_tool("non-existent", "tool")
