# MCP Composer - GitHub Copilot Instructions

This repository implements MCP Composer, a gateway service for centrally managing Model Context Protocol (MCP) servers. When working with this codebase, please follow these guidelines:

## Project Architecture

This is a FastAPI-based Python application that acts as a gateway for multiple MCP servers. The main components are:

- **Composer**: The main orchestrator that manages server kits and gateways
- **Gateway**: MCP server implementation that handles client connections via SSE (Server-Sent Events)
- **ServerKit**: Manages configurations for which downstream MCP servers and tools are enabled
- **DownstreamController**: Handles connections to external MCP servers
- **Domain Models**: Located in `src/domain/` including `ServerKit` and `DownstreamServer` classes

## Technology Stack and Dependencies

- Use **Python 3.12+** as the minimum version
- Use **FastAPI** for the web framework with async/await patterns
- Use **uv** for dependency management (not pip or poetry)
- Use **Pydantic** for data validation and serialization
- Use **MCP library** (`mcp[cli]>=1.6.0`) for Model Context Protocol support
- Use **python-dotenv** for environment variable management
- Use **Ruff** for code formatting and linting

## Code Style and Conventions

- Always use async/await for I/O operations and API endpoints
- Follow FastAPI patterns for dependency injection and request handling
- Use type hints extensively with proper imports from `typing`
- Use Pydantic BaseModel for data classes and API request/response models
- Follow the existing logging pattern using the `logging` module
- Use proper exception handling with meaningful error messages

## File Structure Patterns

- Place API routes in `src/api.py` with the `/api/v1` prefix
- Domain models go in `src/domain/` directory
- Main application logic stays in `src/` root
- Configuration handling in `src/config.py`
- Use relative imports within the src directory

## Environment and Configuration

- Load configuration from JSON files (see `mcp_servers.example.json`)
- Support both stdio and SSE connection types for MCP servers
- Use environment variables for runtime configuration:
  - `HOST`, `PORT` for server binding
  - `MCP_COMPOSER_PROXY_URL` for the public endpoint URL
  - `MCP_SERVERS_CONFIG_PATH` for the config file location

## API Design Patterns

- Use RESTful endpoints with proper HTTP methods
- Implement CRUD operations for ServerKits and Gateways
- Use POST for enable/disable operations on servers and tools
- Return proper Pydantic models from API endpoints
- Include proper error handling and HTTP status codes

## MCP Server Integration

- Support both stdio (command-line) and SSE (HTTP) MCP server connections
- Implement proper session management for downstream MCP servers
- Handle tool namespacing by prefixing with server control names
- Manage server and tool enable/disable states properly

## Development Workflow

- Use `make install` for dependency installation
- Use `make format` for code formatting with Ruff
- Use `make run` to start the development server
- Support Docker deployment with the provided Dockerfile and docker-compose.yml

## Frontend Integration

- The UI is a single HTML file with vanilla JavaScript at `src/ui/index.html`
- API calls use the `/api/v1` prefix
- Support real-time updates for server and tool status changes
- Include proper error handling and user notifications

When suggesting code changes or new features, ensure they follow these patterns and integrate properly with the existing architecture. Always consider the async nature of the application and proper error handling for MCP server connections.
