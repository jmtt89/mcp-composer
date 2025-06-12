from .domain.downstream_server import (
    DownstreamMCPServerConfig,
    DownstreamMCPServer,
    DownstreamMCPServerTool,
)
from typing import Dict, List, Tuple, TYPE_CHECKING
import asyncio
from contextlib import AsyncExitStack

if TYPE_CHECKING:
    from .domain.server_kit import ServerKit


class DownstreamController:
    def __init__(self, configs: List[DownstreamMCPServerConfig]):
        self._all_servers_tools: List[
            Tuple[DownstreamMCPServer, List[DownstreamMCPServerTool]]
        ] = []
        self._servers_map: Dict[str, DownstreamMCPServer] = {}
        self._tools_map: Dict[str, DownstreamMCPServerTool] = {}
        self._asyncio_lock = asyncio.Lock()
        self.configs = configs
        self.exit_stack = AsyncExitStack()
        self._initialized = False

    async def initialize(self):
        async with self._asyncio_lock:
            for config in self.configs:
                await self.register_downstream_mcp_server(config)
            self._initialized = True

    def is_initialized(self) -> bool:
        return self._initialized

    async def shutdown(self):
        async with self._asyncio_lock:
            for server, _ in self._all_servers_tools:
                await server.shutdown()
            await self.exit_stack.aclose()

    async def register_downstream_mcp_server(self, config: DownstreamMCPServerConfig):
        server = DownstreamMCPServer(config)
        await server.initialize(self.exit_stack)
        self._servers_map[server.get_control_name()] = server
        tools = await server.list_tools()
        self._all_servers_tools.append((server, tools))
        for tool in tools:
            self._tools_map[tool.control_name] = tool

    def list_all_servers_tools(
        self,
    ) -> List[Tuple[DownstreamMCPServer, List[DownstreamMCPServerTool]]]:
        return self._all_servers_tools

    def get_tool_by_control_name(
        self, tool_control_name: str
    ) -> DownstreamMCPServerTool:
        return self._tools_map[tool_control_name]

    def get_server_by_control_name(
        self, server_control_name: str
    ) -> DownstreamMCPServer:
        return self._servers_map[server_control_name]

    async def add_server_dynamically(self, config: DownstreamMCPServerConfig):
        """Add a new MCP server dynamically without restarting the application."""
        async with self._asyncio_lock:
            server_name = config.name
            
            # Check if server already exists
            if server_name in self._servers_map:
                raise ValueError(f"Server '{server_name}' already exists")
            
            # Register the new server
            await self.register_downstream_mcp_server(config)

    async def remove_server_dynamically(self, server_name: str):
        """Remove an MCP server dynamically."""
        async with self._asyncio_lock:
            if server_name not in self._servers_map:
                raise ValueError(f"Server '{server_name}' not found")
            
            # Get the server
            server = self._servers_map[server_name]
            
            # Remove from servers map
            del self._servers_map[server_name]
            
            # Remove tools from tools map
            tools_to_remove = [
                tool_name for tool_name, tool in self._tools_map.items()
                if tool.server_control_name == server_name
            ]
            for tool_name in tools_to_remove:
                del self._tools_map[tool_name]
            
            # Remove from all_servers_tools list
            self._all_servers_tools = [
                (s, tools) for s, tools in self._all_servers_tools
                if s.get_control_name() != server_name
            ]
            
            # Shutdown the server
            await server.shutdown()

    def check_server_dependencies(self, server_name: str, server_kits_map: Dict[str, 'ServerKit']) -> List[str]:
        """Check which ServerKits depend on this server."""
        from .domain.server_kit import ServerKit  # Import here to avoid circular import
        
        dependent_kits = []
        for kit_name, server_kit in server_kits_map.items():
            if server_kit.is_server_assigned(server_name):
                dependent_kits.append(kit_name)
        return dependent_kits

    def list_available_servers(self) -> List[str]:
        """List all available server names in the registry."""
        return list(self._servers_map.keys())

    def get_server_status(self, server_name: str) -> str:
        """Get the connection status of a server."""
        if server_name not in self._servers_map:
            return "not_found"
        
        # For now, if server exists in map, consider it connected
        # This could be enhanced with actual health checking
        return "connected"

    def get_server_tools_count(self, server_name: str) -> int:
        """Get the number of tools provided by a server."""
        tools = [
            tool for tool_name, tool in self._tools_map.items()
            if tool.server_control_name == server_name
        ]
        return len(tools)
