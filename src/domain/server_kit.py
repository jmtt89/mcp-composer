from typing import List, Dict
from pydantic import BaseModel


class ServerKit(BaseModel):
    name: str
    enabled: bool
    assigned_servers: List[str] = []  # NEW: Only these servers are available to this ServerKit
    servers_enabled: Dict[str, bool]
    tools_enabled: Dict[str, bool]
    servers_tools_hierarchy_map: Dict[str, List[str]]
    tools_servers_map: Dict[str, str]

    @classmethod
    def new_server_kit(cls, name: str) -> "ServerKit":
        return ServerKit(
            name=name,
            enabled=True,
            assigned_servers=[],
            servers_enabled={},
            tools_enabled={},
            servers_tools_hierarchy_map={},
            tools_servers_map={},
        )

    def list_enabled_tool_names(self) -> List[str]:
        tool_names = []
        for tool_name, enabled in self.tools_enabled.items():
            server_name = self.tools_servers_map[tool_name]
            
            # NEW: Check if server is assigned to this ServerKit
            if self.assigned_servers and server_name not in self.assigned_servers:
                continue
                
            server_enabled = self.servers_enabled[server_name]
            if not server_enabled:
                continue
            if not enabled:
                continue
            tool_names.append(tool_name)
        return tool_names

    def disable_kit(self):
        self.enabled = False

    def enable_kit(self):
        self.enabled = True

    def disable_server(self, server_name: str):
        self.servers_enabled[server_name] = False

    def enable_server(self, server_name: str):
        self.servers_enabled[server_name] = True

    def disable_tool(self, tool_name: str):
        self.tools_enabled[tool_name] = False

    def enable_tool(self, tool_name: str):
        self.tools_enabled[tool_name] = True

    def assign_mcp_server(self, server_name: str):
        """Assign an MCP server to this ServerKit, making it available for use."""
        if server_name not in self.assigned_servers:
            self.assigned_servers.append(server_name)
            # Auto-enable the server when assigned
            self.servers_enabled[server_name] = True

    def unassign_mcp_server(self, server_name: str):
        """Unassign an MCP server from this ServerKit, removing it and its tools."""
        if server_name in self.assigned_servers:
            self.assigned_servers.remove(server_name)
            
            # Remove server from enabled servers
            if server_name in self.servers_enabled:
                del self.servers_enabled[server_name]
            
            # Remove server's tools from tools_enabled and tools_servers_map
            tools_to_remove = [
                tool_name for tool_name, mapped_server in self.tools_servers_map.items()
                if mapped_server == server_name
            ]
            for tool_name in tools_to_remove:
                if tool_name in self.tools_enabled:
                    del self.tools_enabled[tool_name]
                if tool_name in self.tools_servers_map:
                    del self.tools_servers_map[tool_name]
            
            # Remove server from hierarchy map
            if server_name in self.servers_tools_hierarchy_map:
                del self.servers_tools_hierarchy_map[server_name]

    def list_assigned_servers(self) -> List[str]:
        """Return list of servers assigned to this ServerKit."""
        return self.assigned_servers.copy()

    def is_server_assigned(self, server_name: str) -> bool:
        """Check if a server is assigned to this ServerKit."""
        return server_name in self.assigned_servers
