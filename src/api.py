from fastapi import APIRouter, Request, HTTPException
from typing import List
from .composer import Composer
from .domain.server_kit import ServerKit
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
            "downstream_servers": len(composer.downstream_controller._all_servers_tools),
            "active_gateways": len(composer.gateway_map)
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
            "downstream_servers_initialized": len(composer.downstream_controller._all_servers_tools)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Startup probe failed: {e}")
        raise HTTPException(status_code=503, detail="Application startup failed")


@v1_api_router.get("/kits")
async def list_server_kits(request: Request) -> List[ServerKit]:
    composer: Composer = request.app.state.composer
    return await composer.list_server_kits()


@v1_api_router.get("/kits/{name}")
async def get_server_kit(request: Request, name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    try:
        return await composer.get_server_kit(name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@v1_api_router.post("/kits/{name}/disable")
async def disable_server_kit(request: Request, name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return await composer.disable_server_kit(name)


@v1_api_router.post("/kits/{name}/enable")
async def enable_server_kit(request: Request, name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return await composer.enable_server_kit(name)


@v1_api_router.post("/kits/{name}/servers/{server_name}/disable")
async def disable_server(request: Request, name: str, server_name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return await composer.disable_server(name, server_name)


@v1_api_router.post("/kits/{name}/servers/{server_name}/enable")
async def enable_server(request: Request, name: str, server_name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return await composer.enable_server(name, server_name)


@v1_api_router.post("/kits/{name}/tools/{tool_name}/disable")
async def disable_tool(request: Request, name: str, tool_name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return await composer.disable_tool(name, tool_name)


@v1_api_router.post("/kits/{name}/tools/{tool_name}/enable")
async def enable_tool(request: Request, name: str, tool_name: str) -> ServerKit:
    composer: Composer = request.app.state.composer
    return await composer.enable_tool(name, tool_name)


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
    gateways = await composer.list_gateways()
    return [new_gateway_response(gateway) for gateway in gateways]


@v1_api_router.get("/gateways/{name}")
async def get_gateway(request: Request, name: str) -> GatewayResponse:
    composer: Composer = request.app.state.composer
    try:
        gateway = await composer.get_gateway(name)
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
    gateway = await composer.remove_gateway(name)
    return new_gateway_response(gateway)
