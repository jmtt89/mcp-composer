"""Integration tests for API endpoints."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

from src.main import app
from src.domain.server_kit import ServerKit


class TestAPIEndpoints:
    """Test cases for API endpoints."""

    @pytest.fixture
    def client(self, test_app):
        """Test client fixture."""
        return TestClient(test_app)

    def test_kits_list_empty(self, client):
        """Test listing empty server kits."""
        response = client.get("/api/v1/kits")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_kits_list_with_data(self, client, test_composer):
        """Test listing server kits with data."""
        # Create some test kits
        test_composer.create_server_kit("kit1")
        test_composer.create_server_kit("kit2")
        
        response = client.get("/api/v1/kits")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(kit["name"] == "kit1" for kit in data)
        assert any(kit["name"] == "kit2" for kit in data)

    def test_kit_get_existing(self, client, test_composer):
        """Test getting an existing server kit."""
        test_composer.create_server_kit("test-kit")
        
        response = client.get("/api/v1/kits/test-kit")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-kit"
        assert data["enabled"] is True

    def test_kit_get_not_found(self, client):
        """Test getting a non-existent server kit."""
        response = client.get("/api/v1/kits/non-existent")
        
        assert response.status_code == 404  # Our improved API returns 404 for not found
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_kit_disable(self, client, test_composer):
        """Test disabling a server kit."""
        test_composer.create_server_kit("test-kit")
        
        response = client.post("/api/v1/kits/test-kit/disable")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-kit"
        assert data["enabled"] is False

    def test_kit_enable(self, client, test_composer):
        """Test enabling a server kit."""
        kit = test_composer.create_server_kit("test-kit")
        kit.enabled = False
        
        response = client.post("/api/v1/kits/test-kit/enable")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-kit"
        assert data["enabled"] is True

    def test_server_disable(self, client, test_composer):
        """Test disabling a server."""
        kit = test_composer.create_server_kit("test-kit")
        server_name = list(kit.servers_enabled.keys())[0]
        
        response = client.post(f"/api/v1/kits/test-kit/servers/{server_name}/disable")
        
        assert response.status_code == 200
        data = response.json()
        assert data["servers_enabled"][server_name] is False

    def test_server_enable(self, client, test_composer):
        """Test enabling a server."""
        kit = test_composer.create_server_kit("test-kit")
        server_name = list(kit.servers_enabled.keys())[0]
        kit.servers_enabled[server_name] = False
        
        response = client.post(f"/api/v1/kits/test-kit/servers/{server_name}/enable")
        
        assert response.status_code == 200
        data = response.json()
        assert data["servers_enabled"][server_name] is True

    def test_tool_disable(self, client, test_composer):
        """Test disabling a tool."""
        kit = test_composer.create_server_kit("test-kit")
        tool_name = list(kit.tools_enabled.keys())[0]
        
        response = client.post(f"/api/v1/kits/test-kit/tools/{tool_name}/disable")
        
        assert response.status_code == 200
        data = response.json()
        assert data["tools_enabled"][tool_name] is False

    def test_tool_enable(self, client, test_composer):
        """Test enabling a tool."""
        kit = test_composer.create_server_kit("test-kit")
        tool_name = list(kit.tools_enabled.keys())[0]
        kit.tools_enabled[tool_name] = False
        
        response = client.post(f"/api/v1/kits/test-kit/tools/{tool_name}/enable")
        
        assert response.status_code == 200
        data = response.json()
        assert data["tools_enabled"][tool_name] is True

    def test_gateways_list_empty(self, client):
        """Test listing empty gateways."""
        response = client.get("/api/v1/gateways")
        
        assert response.status_code == 200
        assert response.json() == []

    async def test_gateways_list_with_data(self, client, test_composer):
        """Test listing gateways with data."""
        kit1 = test_composer.create_server_kit("kit1")
        kit2 = test_composer.create_server_kit("kit2")
        
        # Add gateways
        with patch('src.composer.Gateway') as mock_gateway_class:
            mock_gateway = MagicMock()
            mock_gateway.name = kit1.name
            mock_gateway.gateway_endpoint = f"http://localhost:8000/mcp/{kit1.name}/sse"
            mock_gateway.server_kit = kit1
            mock_gateway.setup = AsyncMock()
            mock_gateway.as_asgi_route.return_value = MagicMock()
            mock_gateway_class.return_value = mock_gateway
            
            await test_composer.add_gateway(kit1)
            
            mock_gateway2 = MagicMock()
            mock_gateway2.name = kit2.name
            mock_gateway2.gateway_endpoint = f"http://localhost:8000/mcp/{kit2.name}/sse"
            mock_gateway2.server_kit = kit2
            mock_gateway2.setup = AsyncMock()
            mock_gateway2.as_asgi_route.return_value = MagicMock()
            mock_gateway_class.return_value = mock_gateway2
            
            await test_composer.add_gateway(kit2)
        
        response = client.get("/api/v1/gateways")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_gateway_get_existing(self, client, test_composer):
        """Test getting an existing gateway."""
        kit = test_composer.create_server_kit("test-kit")
        
        with patch('src.composer.Gateway') as mock_gateway_class:
            mock_gateway = MagicMock()
            mock_gateway.name = kit.name
            mock_gateway.gateway_endpoint = f"http://localhost:8000/mcp/{kit.name}/sse"
            mock_gateway.server_kit = kit
            mock_gateway.setup = AsyncMock()
            mock_gateway.as_asgi_route.return_value = MagicMock()
            mock_gateway_class.return_value = mock_gateway
            
            await test_composer.add_gateway(kit)
        
        response = client.get("/api/v1/gateways/test-kit")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-kit"
        assert "gateway_endpoint" in data

    def test_gateway_get_not_found(self, client):
        """Test getting a non-existent gateway."""
        response = client.get("/api/v1/gateways/non-existent")
        
        assert response.status_code == 404  # Our improved API returns 404 for not found
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_gateway_add(self, client, test_composer):
        """Test adding a new gateway."""
        kit = test_composer.create_server_kit("source-kit")
        
        request_data = {
            "name": "new-gateway",
            "server_kit": kit.model_dump()
        }
        
        with patch('src.composer.Gateway') as mock_gateway_class:
            mock_gateway = MagicMock()
            mock_gateway.name = "new-gateway"
            mock_gateway.gateway_endpoint = "http://localhost:8000/mcp/new-gateway/sse"
            mock_gateway.server_kit = kit  # Use the real ServerKit instead of MagicMock
            mock_gateway.setup = AsyncMock()
            mock_gateway.as_asgi_route.return_value = MagicMock()
            mock_gateway_class.return_value = mock_gateway
            
            response = client.post("/api/v1/gateways", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "new-gateway"

    async def test_gateway_remove(self, client, test_composer):
        """Test removing a gateway."""
        kit1 = test_composer.create_server_kit("kit1")
        kit2 = test_composer.create_server_kit("kit2")
        
        with patch('src.composer.Gateway') as mock_gateway_class:
            mock_gateway = MagicMock()
            mock_gateway.name = kit1.name
            mock_gateway.gateway_endpoint = f"http://localhost:8000/mcp/{kit1.name}/sse"
            mock_gateway.server_kit = kit1
            mock_gateway.setup = AsyncMock()
            mock_gateway.as_asgi_route.return_value = MagicMock()
            mock_gateway_class.return_value = mock_gateway
            
            await test_composer.add_gateway(kit1)
            await test_composer.add_gateway(kit2)
        
        # Mock the _remove_route_from_app method to avoid FastAPI routing complexity
        with patch.object(test_composer, '_remove_route_from_app', return_value=True):
            response = client.delete("/api/v1/gateways/kit1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "kit1"
