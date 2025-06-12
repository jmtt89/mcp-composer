from pydantic import BaseModel, Field
from typing import List, Dict, Optional, TYPE_CHECKING
from .downstream_server import DownstreamMCPServerConfig

if TYPE_CHECKING:
    from .server_kit import ServerKit


class MCPServerConfig(BaseModel):
    """Configuration for creating a new MCP server."""
    name: str = Field(..., description="Unique name for the MCP server")
    command: str = Field(..., description="Command to execute the MCP server")
    args: List[str] = Field(default_factory=list, description="Arguments for the command")
    env: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")
    
    def to_downstream_config(self) -> DownstreamMCPServerConfig:
        """Convert to DownstreamMCPServerConfig format."""
        return DownstreamMCPServerConfig(
            name=self.name,
            command=self.command,
            args=self.args,
            env=self.env or {}
        )


class MCPServerResponse(BaseModel):
    """Response model for MCP server information."""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    status: str  # "connected", "disconnected", "error", "not_found"
    tools_count: int
    assigned_to_kits: List[str]
    
    @classmethod
    def from_config_and_controller(
        cls, 
        config: "MCPServerConfig", 
        downstream_controller,
        server_kits_map: Dict[str, "ServerKit"]
    ) -> "MCPServerResponse":
        """Create response from config and controller state."""
        # Get assigned kits
        assigned_kits = []
        for kit_name, server_kit in server_kits_map.items():
            if server_kit.is_server_assigned(config.name):
                assigned_kits.append(kit_name)
        
        return cls(
            name=config.name,
            command=config.command,
            args=config.args,
            env=config.env or {},
            status=downstream_controller.get_server_status(config.name),
            tools_count=downstream_controller.get_server_tools_count(config.name),
            assigned_to_kits=assigned_kits
        )


class ServerAssignmentRequest(BaseModel):
    """Request model for server assignment operations."""
    auto_enable: bool = Field(
        default=True, 
        description="Automatically enable the server when assigned to ServerKit"
    )


class MCPServerUpdateRequest(BaseModel):
    """Request model for updating MCP server configuration."""
    command: Optional[str] = Field(default=None, description="Updated command")
    args: Optional[List[str]] = Field(default=None, description="Updated arguments")
    env: Optional[Dict[str, str]] = Field(default=None, description="Updated environment variables")


class MCPServerListResponse(BaseModel):
    """Response model for listing MCP servers."""
    servers: List[MCPServerResponse]
    total_count: int


class ServerDependencyResponse(BaseModel):
    """Response model for server dependency information."""
    server_name: str
    dependent_kits: List[str]
    can_be_removed: bool
