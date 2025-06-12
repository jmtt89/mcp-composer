from typing import Dict, List
from .domain.server_kit import ServerKit
from .downstream_controller import DownstreamController
from fastapi import FastAPI
from .gateway import Gateway
from .config import Config
from starlette.routing import Mount
import logging

# Get logger for this module
logger = logging.getLogger(__name__)


class Composer:
    def __init__(self, downstream_controller: DownstreamController, config: Config):
        self.server_kits_map: Dict[str, ServerKit] = {}
        self.downstream_controller = downstream_controller
        self.gateway_map: Dict[str, Gateway] = {}
        self._asgi_app = FastAPI()
        self.config = config
        self.config_manager = config.config_manager  # Reference to ConfigurationManager

    def asgi_gateway_routes(self):
        return self._asgi_app

    async def migrate_server_kits(self):
        """Migrate existing ServerKits to support assigned_servers."""
        await self.config_manager.migrate_existing_server_kits(self.server_kits_map)

    # APIs
    # ServerKit
    def list_server_kits(self) -> List[ServerKit]:
        return list(self.server_kits_map.values())

    def get_server_kit(self, name: str) -> ServerKit:
        if name not in self.server_kits_map:
            raise ValueError(f"Server kit '{name}' not found")
        return self.server_kits_map[name]

    def create_server_kit(
        self,
        name: str,
        enabled: bool = True,
    ) -> ServerKit:
        if (
            not self.downstream_controller
            or not self.downstream_controller.is_initialized()
        ):
            raise ValueError("Downstream controller not set or not initialized")
        server_kit = ServerKit.new_server_kit(name)
        for server, tools in self.downstream_controller.list_all_servers_tools():
            server_kit.servers_enabled[server.get_control_name()] = enabled
            server_kit.servers_tools_hierarchy_map[server.get_control_name()] = []
            for tool in tools:
                server_kit.tools_enabled[tool.control_name] = enabled
                server_kit.servers_tools_hierarchy_map[
                    server.get_control_name()
                ].append(tool.control_name)
                server_kit.tools_servers_map[tool.control_name] = (
                    server.get_control_name()
                )
        self.server_kits_map[name] = server_kit
        return server_kit

    def disable_server_kit(self, name: str) -> ServerKit:
        server_kit = self.server_kits_map[name]
        server_kit.disable_kit()
        return server_kit

    def enable_server_kit(self, name: str) -> ServerKit:
        server_kit = self.server_kits_map[name]
        server_kit.enable_kit()
        return server_kit

    def disable_server(self, name: str, server_name: str) -> ServerKit:
        server_kit = self.server_kits_map[name]
        server_kit.disable_server(server_name)
        return server_kit

    def enable_server(self, name: str, server_name: str) -> ServerKit:
        server_kit = self.server_kits_map[name]
        server_kit.enable_server(server_name)
        return server_kit

    def disable_tool(self, name: str, tool_name: str) -> ServerKit:
        server_kit = self.server_kits_map[name]
        server_kit.disable_tool(tool_name)
        return server_kit

    def enable_tool(self, name: str, tool_name: str) -> ServerKit:
        server_kit = self.server_kits_map[name]
        server_kit.enable_tool(tool_name)
        return server_kit

    # Gateway
    def list_gateways(self) -> List[Gateway]:
        return list(self.gateway_map.values())

    def get_gateway(self, name: str) -> Gateway:
        if name not in self.gateway_map:
            raise ValueError(f"Gateway '{name}' not found")
        return self.gateway_map[name]

    async def add_gateway(self, server_kit: ServerKit):
        if server_kit.name in self.gateway_map:
            raise ValueError(f"Gateway {server_kit.name} already exists")
        gateway = Gateway(
            server_kit,
            self.downstream_controller,
            self.config.mcp_composer_proxy_url,
        )
        await gateway.setup()
        self.gateway_map[server_kit.name] = gateway
        self._asgi_app.mount(f"/{server_kit.name}", gateway.as_asgi_route())
        return gateway

    def remove_gateway(self, name: str):
        if len(self.gateway_map) == 1:
            raise ValueError("Cannot remove the last gateway")
        if name not in self.gateway_map:
            raise ValueError(f"Gateway {name} does not exist")

        # Find and remove the mounted route
        self._remove_route_from_app(name)

        # Remove the gateway from the map
        gateway = self.gateway_map[name]
        del self.gateway_map[name]
        return gateway

    def _remove_route_from_app(self, name: str):
        """Remove a route from the ASGI app. Separated for testability."""
        target_path = f"/{name}"
        routes_to_keep = []
        route_removed = False
        
        for route in self._asgi_app.routes:
            # Check if it's a Mount route and the path matches
            if isinstance(route, Mount) and route.path == target_path:
                route_removed = True
                # Skip this route (don't add to routes_to_keep)
            else:
                routes_to_keep.append(route)
        
        # Replace the routes list with the filtered one
        self._asgi_app.routes[:] = routes_to_keep
        
        if not route_removed:
            logger.warning(f"No matching route found for removal: {target_path}")
        
        return route_removed
