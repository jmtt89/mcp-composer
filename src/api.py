from fastapi import APIRouter, Request, HTTPException
from typing import List
from .composer import Composer
from .domain.server_kit import ServerKit
from .domain.mcp_models import (
    MCPServerConfig,
    MCPServerResponse,
    ServerAssignmentRequest,
    MCPServerUpdateRequest,
    MCPServerListResponse,
    ServerDependencyResponse
)
from pydantic import BaseModel
from .gateway import Gateway
import time
import logging

v1_api_router = APIRouter(prefix="/api/v1")

# Global variable to track application startup time
_app_start_time = time.time()

logger = logging.getLogger(__name__)


@v1_api_router.get("/health")
async def health_check():
    """Basic health check endpoint for Docker healthcheck"""
    return {"status": "healthy", "timestamp": time.time()}


@v1_api_router.get("/health/live")
async def liveness_probe():
    """
    Liveness probe endpoint.
    This should only fail if the application is in an unrecoverable state.
    """
    try:
        # Basic check that the application is running
        return {
            "status": "alive",
            "timestamp": time.time(),
            "uptime": time.time() - _app_start_time
        }
    except Exception as e:
        logger.error(f"Liveness probe failed: {e}")
        raise HTTPException(status_code=503, detail="Application is not alive")


@v1_api_router.get("/health/ready")
async def readiness_probe(request: Request):
    """
    Readiness probe endpoint.
    This indicates if the application is ready to receive traffic.
    """
    try:
        # Check if composer is available and downstream controller is initialized
        composer = getattr(request.app.state, 'composer', None)
        
        if not composer:
            raise HTTPException(status_code=503, detail="Composer not available")
        
        if not composer.downstream_controller.is_initialized():
            raise HTTPException(status_code=503, detail="Downstream controller not initialized")
        
        # Additional checks can be added here:
        # - Database connectivity
        # - External service dependencies
        # - Critical configuration validation
        
        return {
            "status": "ready",
            "timestamp": time.time(),
            "downstream_servers": len(composer.downstream_controller.list_all_servers_tools()),
            "active_gateways": len(composer.list_gateways())
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        raise HTTPException(status_code=503, detail="Application is not ready")


@v1_api_router.get("/health/startup")
async def startup_probe(request: Request):
    """
    Startup probe endpoint.
    This indicates if the application has finished starting up.
    """
    try:
        # Check if the application has completed its startup sequence
        composer = getattr(request.app.state, 'composer', None)
        
        if not composer:
            raise HTTPException(status_code=503, detail="Application still starting up")
        
        if not composer.downstream_controller.is_initialized():
            raise HTTPException(status_code=503, detail="Downstream controller initialization in progress")
        
        # Check that we have a reasonable startup time (e.g., at least 1 second)
        startup_duration = time.time() - _app_start_time
        if startup_duration < 1.0:
            raise HTTPException(status_code=503, detail="Application startup in progress")
        
        return {
            "status": "started",
            "timestamp": time.time(),
            "startup_duration": startup_duration,
            "downstream_servers_initialized": len(composer.downstream_controller.list_all_servers_tools())
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Startup probe failed: {e}")
        raise HTTPException(status_code=503, detail="Application startup failed")


@v1_api_router.get("/kits")
async def list_server_kits(request: Request) -> List[ServerKit]:
    composer: Composer = request.app.state.composer
    return composer.list_server_kits()


@v1_api_router.get("/kits/{name}")
async def get_server_kit(request: Request, name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    try:
        return composer.get_server_kit(name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@v1_api_router.post("/kits/{name}/disable")
async def disable_server_kit(request: Request, name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return composer.disable_server_kit(name)


@v1_api_router.post("/kits/{name}/enable")
async def enable_server_kit(request: Request, name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return composer.enable_server_kit(name)


@v1_api_router.post("/kits/{name}/servers/{server_name}/disable")
async def disable_server(request: Request, name: str, server_name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return composer.disable_server(name, server_name)


@v1_api_router.post("/kits/{name}/servers/{server_name}/enable")
async def enable_server(request: Request, name: str, server_name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return composer.enable_server(name, server_name)


@v1_api_router.post("/kits/{name}/tools/{tool_name}/disable")
async def disable_tool(request: Request, name: str, tool_name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return composer.disable_tool(name, tool_name)


@v1_api_router.post("/kits/{name}/tools/{tool_name}/enable")
async def enable_tool(request: Request, name: str, tool_name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return composer.enable_tool(name, tool_name)


# Gateway
class GatewayResponse(BaseModel):
    name: str
    gateway_endpoint: str
    server_kit: ServerKit


def new_gateway_response(gateway: Gateway) -> GatewayResponse:
    return GatewayResponse(
        name=gateway.name,
        gateway_endpoint=gateway.gateway_endpoint,
        server_kit=gateway.server_kit,
    )


@v1_api_router.get("/gateways")
async def list_gateways(request: Request) -> List[GatewayResponse]:
    composer: Composer = request.app.state.composer
    gateways = composer.list_gateways()
    return [new_gateway_response(gateway) for gateway in gateways]


@v1_api_router.get("/gateways/{name}")
async def get_gateway(request: Request, name: str) -> GatewayResponse:
    composer: Composer = request.app.state.composer
    try:
        gateway = composer.get_gateway(name)
        return new_gateway_response(gateway)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


class AddGatewayRequest(BaseModel):
    name: str
    server_kit: ServerKit


@v1_api_router.post("/gateways")
async def add_gateway(
    request: Request, add_gateway_request: AddGatewayRequest
) -> GatewayResponse:
    composer: Composer = request.app.state.composer
    server_kit: ServerKit = composer.create_server_kit(add_gateway_request.name)
    server_kit.servers_enabled = add_gateway_request.server_kit.servers_enabled
    server_kit.tools_enabled = add_gateway_request.server_kit.tools_enabled
    gateway = await composer.add_gateway(server_kit)
    return new_gateway_response(gateway)


@v1_api_router.delete("/gateways/{name}")
async def remove_gateway(request: Request, name: str) -> GatewayResponse:
    composer: Composer = request.app.state.composer
    gateway = composer.remove_gateway(name)
    return new_gateway_response(gateway)


# === MCP Server Management Endpoints ===

@v1_api_router.get("/mcp")
async def list_mcp_servers(request: Request) -> MCPServerListResponse:
    """List all available MCP servers in the registry."""
    composer: Composer = request.app.state.composer
    
    server_names = composer.downstream_controller.list_available_servers()
    servers = []
    
    for server_name in server_names:
        # Create a basic config object for each server
        # Note: In a real implementation, we'd store the original config
        config = MCPServerConfig(
            name=server_name,
            command="<configured>",  # Placeholder since we don't store original config
            args=[],
            env={}
        )
        
        server_response = MCPServerResponse.from_config_and_controller(
            config, composer.downstream_controller, composer.server_kits_map
        )
        servers.append(server_response)
    
    return MCPServerListResponse(
        servers=servers,
        total_count=len(servers)
    )


@v1_api_router.post("/mcp")
async def create_mcp_server(request: Request, server_config: MCPServerConfig) -> MCPServerResponse:
    """Add a new MCP server to the registry."""
    composer: Composer = request.app.state.composer
    
    try:
        # Convert to downstream config format
        downstream_config = server_config.to_downstream_config()
        
        # Add server dynamically
        await composer.downstream_controller.add_server_dynamically(downstream_config)
        
        # Save to configuration file
        await composer.config_manager.add_mcp_server(server_config)
        
        # Return response
        return MCPServerResponse.from_config_and_controller(
            server_config, composer.downstream_controller, composer.server_kits_map
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create MCP server {server_config.name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create MCP server")


@v1_api_router.get("/mcp/{server_name}")
async def get_mcp_server(request: Request, server_name: str) -> MCPServerResponse:
    """Get information about a specific MCP server."""
    composer: Composer = request.app.state.composer
    
    if server_name not in composer.downstream_controller.list_available_servers():
        raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found")
    
    # Create a basic config object
    config = MCPServerConfig(
        name=server_name,
        command="<configured>",
        args=[],
        env={}
    )
    
    return MCPServerResponse.from_config_and_controller(
        config, composer.downstream_controller, composer.server_kits_map
    )


@v1_api_router.delete("/mcp/{server_name}")
async def delete_mcp_server(request: Request, server_name: str):
    """Remove an MCP server from the registry."""
    composer: Composer = request.app.state.composer
    
    try:
        # Check dependencies first
        dependencies = composer.downstream_controller.check_server_dependencies(
            server_name, composer.server_kits_map
        )
        
        if dependencies:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot remove server '{server_name}'. It is used by ServerKits: {', '.join(dependencies)}"
            )
        
        # Remove server
        await composer.downstream_controller.remove_server_dynamically(server_name)
        
        # Update configuration file
        await composer.config_manager.remove_mcp_server(server_name)
        
        return {"message": f"MCP server '{server_name}' removed successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove MCP server {server_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove MCP server")


@v1_api_router.get("/mcp/{server_name}/status")
async def get_mcp_server_status(request: Request, server_name: str):
    """Get the connection status of an MCP server."""
    composer: Composer = request.app.state.composer
    
    if server_name not in composer.downstream_controller.list_available_servers():
        raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found")
    
    status = composer.downstream_controller.get_server_status(server_name)
    tools_count = composer.downstream_controller.get_server_tools_count(server_name)
    
    return {
        "server_name": server_name,
        "status": status,
        "tools_count": tools_count
    }


@v1_api_router.get("/mcp/{server_name}/dependencies")
async def get_mcp_server_dependencies(request: Request, server_name: str) -> ServerDependencyResponse:
    """Get dependency information for an MCP server."""
    composer: Composer = request.app.state.composer
    
    if server_name not in composer.downstream_controller.list_available_servers():
        raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found")
    
    dependencies = composer.downstream_controller.check_server_dependencies(
        server_name, composer.server_kits_map
    )
    
    return ServerDependencyResponse(
        server_name=server_name,
        dependent_kits=dependencies,
        can_be_removed=len(dependencies) == 0
    )


# === ServerKit MCP Assignment Endpoints ===

@v1_api_router.get("/kits/{kit_name}/mcp")
async def list_kit_assigned_servers(request: Request, kit_name: str) -> List[str]:
    """List MCP servers assigned to a specific ServerKit."""
    composer: Composer = request.app.state.composer
    
    try:
        server_kit = composer.get_server_kit(kit_name)
        return server_kit.list_assigned_servers()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@v1_api_router.get("/kits/{kit_name}/mcp/available")
async def list_kit_available_servers(request: Request, kit_name: str) -> List[str]:
    """List MCP servers available for assignment to a ServerKit."""
    composer: Composer = request.app.state.composer
    
    try:
        server_kit = composer.get_server_kit(kit_name)
        all_servers = composer.downstream_controller.list_available_servers()
        assigned_servers = server_kit.list_assigned_servers()
        
        # Return servers that are not yet assigned
        available_servers = [s for s in all_servers if s not in assigned_servers]
        return available_servers
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@v1_api_router.post("/kits/{kit_name}/mcp/{server_name}/assign")
async def assign_server_to_kit(
    request: Request,
    kit_name: str,
    server_name: str,
    assignment_request: ServerAssignmentRequest = ServerAssignmentRequest()
) -> ServerKit:
    """Assign an MCP server to a ServerKit."""
    composer: Composer = request.app.state.composer
    
    try:
        server_kit = composer.get_server_kit(kit_name)
        
        # Verify server exists
        if server_name not in composer.downstream_controller.list_available_servers():
            raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found")
        
        # Check if already assigned
        if server_kit.is_server_assigned(server_name):
            raise HTTPException(status_code=400, detail=f"Server '{server_name}' is already assigned to kit '{kit_name}'")
        
        # Assign the server
        server_kit.assign_mcp_server(server_name)
        
        # Add server's tools to the kit
        # Get tools from downstream controller
        for server, tools in composer.downstream_controller.list_all_servers_tools():
            if server.get_control_name() == server_name:
                # Clear existing hierarchy for this server (in case of reassignment)
                server_kit.servers_tools_hierarchy_map[server_name] = []
                
                for tool in tools:
                    tool_name = tool.control_name
                    server_kit.tools_enabled[tool_name] = assignment_request.auto_enable
                    server_kit.tools_servers_map[tool_name] = server_name
                    server_kit.servers_tools_hierarchy_map[server_name].append(tool_name)
                break
        
        # Save ServerKit assignments to configuration file
        await composer.config_manager.update_server_kit_assignments(server_kit)
        
        return server_kit
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign server {server_name} to kit {kit_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign server to kit")


@v1_api_router.post("/kits/{kit_name}/mcp/{server_name}/unassign")
async def unassign_server_from_kit(request: Request, kit_name: str, server_name: str) -> ServerKit:
    """Unassign an MCP server from a ServerKit."""
    composer: Composer = request.app.state.composer
    
    try:
        server_kit = composer.get_server_kit(kit_name)
        
        # Check if server is assigned
        if not server_kit.is_server_assigned(server_name):
            raise HTTPException(status_code=400, detail=f"Server '{server_name}' is not assigned to kit '{kit_name}'")
        
        # Unassign the server (this will clean up tools automatically)
        server_kit.unassign_mcp_server(server_name)
        
        # Save ServerKit assignments to configuration file
        await composer.config_manager.update_server_kit_assignments(server_kit)
        
        return server_kit
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unassign server {server_name} from kit {kit_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to unassign server from kit")
