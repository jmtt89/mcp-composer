# Debug MCP Connection Issues

Your goal is to diagnose and fix MCP server connection problems in the MCP Composer.

Ask for the problem details if not provided:
- Which MCP server is failing to connect
- Error messages from logs
- Connection type (stdio or SSE)
- Server configuration being used

Debugging steps to follow:
1. Check the server configuration in `mcp_servers.json` for syntax errors
2. Verify the DownstreamController initialization process
3. Review the server session establishment in DownstreamMCPServer
4. Check for proper async context management with AsyncExitStack
5. Validate tool listing and registration process
6. Test the Gateway's ability to proxy requests

Common issues to investigate:
- **Stdio connections**: Command path, arguments, environment variables
- **SSE connections**: URL accessibility, network connectivity, CORS issues
- **Session management**: Proper initialization and cleanup
- **Tool registration**: Naming conflicts, tool availability
- **Gateway routing**: Proper request forwarding and response handling

Use these files for debugging:
- [DownstreamController](src/downstream_controller.py) for connection management
- [DownstreamMCPServer](src/domain/downstream_server.py) for server initialization
- [Gateway](src/gateway.py) for request handling
- [Config](src/config.py) for configuration loading

Enable debug logging and check server startup logs for detailed error information.
