"""Unit tests for Gateway class."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import cast

from src.gateway import Gateway
from src.domain.server_kit import ServerKit
from src.downstream_controller import DownstreamController
from mcp.types import Tool, ListToolsResult, CallToolRequest, CallToolResult


class TestGateway:
    """Test cases for Gateway class."""

    @pytest.fixture
    def mock_server_kit(self):
        """Mock server kit fixture."""
        kit = MagicMock(spec=ServerKit)
        kit.name = "test-kit"
        kit.enabled = True
        kit.list_enabled_tool_names.return_value = ["server1-tool1", "server1-tool2"]
        kit.tools_enabled = {"server1-tool1": True, "server1-tool2": True}
        return kit

    @pytest.fixture
    def mock_downstream_controller(self):
        """Mock downstream controller fixture."""
        controller = MagicMock(spec=DownstreamController)
        
        # Mock tools
        from src.domain.downstream_server import DownstreamMCPServerTool
        mock_tool1 = MagicMock(spec=DownstreamMCPServerTool)
        mock_tool1.to_new_name_tool.return_value = Tool(
            name="server1-tool1",
            description="Test tool 1",
            inputSchema={}
        )
        mock_tool1.server_control_name = "server1"
        
        mock_tool2 = MagicMock(spec=DownstreamMCPServerTool)
        mock_tool2.to_new_name_tool.return_value = Tool(
            name="server1-tool2",
            description="Test tool 2",
            inputSchema={}
        )
        mock_tool2.server_control_name = "server1"
        
        controller.get_tool_by_control_name.side_effect = lambda name: {
            "server1-tool1": mock_tool1,
            "server1-tool2": mock_tool2
        }.get(name)
        
        return controller

    def test_gateway_initialization(self, mock_server_kit, mock_downstream_controller):
        """Test gateway initialization."""
        proxy_url = "http://localhost:8000"
        
        gateway = Gateway(mock_server_kit, mock_downstream_controller, proxy_url)
        
        assert gateway.server_kit == mock_server_kit
        assert gateway.downstream_controller == mock_downstream_controller
        assert gateway.sse_path == "/mcp/test-kit/sse"
        assert gateway.messages_path == "/mcp/test-kit/messages"
        assert gateway.gateway_endpoint == "http://localhost:8000/mcp/test-kit/sse"
        assert gateway.server is not None
        assert gateway.sse is not None

    def test_gateway_name_property(self, mock_server_kit, mock_downstream_controller):
        """Test gateway name property."""
        gateway = Gateway(mock_server_kit, mock_downstream_controller, "http://localhost:8000")
        
        assert gateway.name == "test-kit"

    @patch('src.gateway.SseServerTransport')
    @patch('src.gateway.Server')
    async def test_gateway_setup(self, mock_server_class, mock_sse_class, mock_server_kit, mock_downstream_controller):
        """Test gateway setup."""
        mock_server = MagicMock()
        mock_server.request_handlers = {}
        mock_server_class.return_value = mock_server
        
        mock_sse = MagicMock()
        mock_sse_class.return_value = mock_sse
        
        gateway = Gateway(mock_server_kit, mock_downstream_controller, "http://localhost:8000")
        gateway.server = mock_server
        gateway.sse = mock_sse
        
        await gateway.setup()
        
        # Check that request handlers were set up
        from mcp.types import ListToolsRequest, CallToolRequest
        assert ListToolsRequest in mock_server.request_handlers
        assert CallToolRequest in mock_server.request_handlers

    async def test_list_tools_handler_enabled_kit(self, mock_server_kit, mock_downstream_controller):
        """Test list tools handler when kit is enabled."""
        gateway = Gateway(mock_server_kit, mock_downstream_controller, "http://localhost:8000")
        await gateway.setup()
        
        # Get the list tools handler
        from mcp.types import ListToolsRequest
        handler = gateway.server.request_handlers[ListToolsRequest]
        
        # Call the handler
        result = await handler(None)
        
        # Check result
        assert hasattr(result, 'root')
        list_tools_result = cast(ListToolsResult, result.root)
        assert len(list_tools_result.tools) == 2
        assert list_tools_result.tools[0].name == "server1-tool1"
        assert list_tools_result.tools[1].name == "server1-tool2"

    async def test_list_tools_handler_disabled_kit(self, mock_server_kit, mock_downstream_controller):
        """Test list tools handler when kit is disabled."""
        mock_server_kit.enabled = False
        
        gateway = Gateway(mock_server_kit, mock_downstream_controller, "http://localhost:8000")
        await gateway.setup()
        
        # Get the list tools handler
        from mcp.types import ListToolsRequest
        handler = gateway.server.request_handlers[ListToolsRequest]
        
        # Call the handler
        result = await handler(None)
        
        # Check result - should be empty when kit is disabled
        assert hasattr(result, 'root')
        list_tools_result = cast(ListToolsResult, result.root)
        assert len(list_tools_result.tools) == 0

    async def test_call_tool_handler_success(self, mock_server_kit, mock_downstream_controller):
        """Test call tool handler success case."""
        # Mock the tool using the fixture's pattern
        from mcp.types import Tool
        
        # Create the actual tool for mock_tool1 from the fixture
        actual_tool = Tool(name="tool1", description="Test tool", inputSchema={})
        
        # Get the existing mock_tool1 from the fixture's side_effect 
        mock_tool1 = mock_downstream_controller.get_tool_by_control_name("server1-tool1")
        mock_tool1.tool = actual_tool  # Add the missing tool attribute
        
        # Mock the server session
        mock_session = AsyncMock()
        mock_session.call_tool.return_value = CallToolResult(content=[], isError=False)
        
        # Mock the downstream server
        mock_server = MagicMock()
        mock_server.session = mock_session
        mock_downstream_controller.get_server_by_control_name.return_value = mock_server
        
        gateway = Gateway(mock_server_kit, mock_downstream_controller, "http://localhost:8000")
        await gateway.setup()
        
        # Create a call tool request
        request = MagicMock()
        request.params.name = "server1-tool1"
        request.params.arguments = {"test": "value"}
        
        # Get the call tool handler
        from mcp.types import CallToolRequest
        handler = gateway.server.request_handlers[CallToolRequest]
        
        # Call the handler
        result = await handler(request)
        
        # Check that the tool was called correctly
        mock_session.call_tool.assert_called_once_with("tool1", {"test": "value"})
        assert hasattr(result, 'root')
        call_tool_result = cast(CallToolResult, result.root)
        assert not call_tool_result.isError

    async def test_call_tool_handler_kit_disabled(self, mock_server_kit, mock_downstream_controller):
        """Test call tool handler when kit is disabled."""
        mock_server_kit.enabled = False
        
        gateway = Gateway(mock_server_kit, mock_downstream_controller, "http://localhost:8000")
        await gateway.setup()
        
        # Create a call tool request
        request = MagicMock()
        request.params.name = "server1-tool1"
        request.params.arguments = {}
        
        # Get the call tool handler
        from mcp.types import CallToolRequest
        handler = gateway.server.request_handlers[CallToolRequest]
        
        # Call the handler
        result = await handler(request)
        
        # Should return error result
        assert hasattr(result, 'root')
        call_tool_result = cast(CallToolResult, result.root)
        assert call_tool_result.isError is True

    async def test_call_tool_handler_tool_disabled(self, mock_server_kit, mock_downstream_controller):
        """Test call tool handler when tool is disabled."""
        mock_server_kit.tools_enabled = {"server1-tool1": False}
        
        gateway = Gateway(mock_server_kit, mock_downstream_controller, "http://localhost:8000")
        await gateway.setup()
        
        # Create a call tool request
        request = MagicMock()
        request.params.name = "server1-tool1"
        request.params.arguments = {}
        
        # Get the call tool handler
        from mcp.types import CallToolRequest
        handler = gateway.server.request_handlers[CallToolRequest]
        
        # Call the handler
        result = await handler(request)
        
        # Should return error result
        assert hasattr(result, 'root')
        call_tool_result = cast(CallToolResult, result.root)
        assert call_tool_result.isError is True

    async def test_call_tool_handler_no_session(self, mock_server_kit, mock_downstream_controller):
        """Test call tool handler when server has no session."""
        # Mock the downstream server without session
        mock_server = MagicMock()
        mock_server.session = None
        mock_downstream_controller.get_server_by_control_name.return_value = mock_server
        
        gateway = Gateway(mock_server_kit, mock_downstream_controller, "http://localhost:8000")
        await gateway.setup()
        
        # Create a call tool request
        request = MagicMock()
        request.params.name = "server1-tool1"
        request.params.arguments = {}
        
        # Get the call tool handler
        from mcp.types import CallToolRequest
        handler = gateway.server.request_handlers[CallToolRequest]
        
        # Call the handler
        result = await handler(request)
        
        # Should return error result
        assert hasattr(result, 'root')
        call_tool_result = cast(CallToolResult, result.root)
        assert call_tool_result.isError is True

    @patch('src.gateway.Starlette')
    def test_as_asgi_route(self, mock_starlette, mock_server_kit, mock_downstream_controller):
        """Test as_asgi_route method."""
        mock_app = MagicMock()
        mock_starlette.return_value = mock_app
        
        gateway = Gateway(mock_server_kit, mock_downstream_controller, "http://localhost:8000")
        
        result = gateway.as_asgi_route()
        
        assert result == mock_app
        mock_starlette.assert_called_once()
        
        # Check that routes were configured
        call_args = mock_starlette.call_args
        assert 'routes' in call_args.kwargs
        assert 'debug' in call_args.kwargs
        assert call_args.kwargs['debug'] is True

    def test_gateway_paths_generation(self, mock_server_kit, mock_downstream_controller):
        """Test that gateway paths are generated correctly."""
        test_cases = [
            ("simple-kit", "/mcp/simple-kit/sse", "/mcp/simple-kit/messages"),
            ("complex_kit-name", "/mcp/complex_kit-name/sse", "/mcp/complex_kit-name/messages"),
        ]
        
        for kit_name, expected_sse_path, expected_messages_path in test_cases:
            mock_server_kit.name = kit_name
            
            gateway = Gateway(mock_server_kit, mock_downstream_controller, "http://localhost:8000")
            
            assert gateway.sse_path == expected_sse_path
            assert gateway.messages_path == expected_messages_path

    def test_gateway_endpoint_generation(self, mock_server_kit, mock_downstream_controller):
        """Test that gateway endpoint is generated correctly."""
        test_cases = [
            ("http://localhost:8000", "http://localhost:8000/mcp/test-kit/sse"),
            ("https://example.com:9000", "https://example.com:9000/mcp/test-kit/sse"),
            ("http://192.168.1.100", "http://192.168.1.100/mcp/test-kit/sse"),
        ]
        
        for proxy_url, expected_endpoint in test_cases:
            gateway = Gateway(mock_server_kit, mock_downstream_controller, proxy_url)
            
            assert gateway.gateway_endpoint == expected_endpoint
