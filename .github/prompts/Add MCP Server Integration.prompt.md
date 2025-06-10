# Add New MCP Server Integration

Your goal is to add support for a new MCP server integration to the MCP Composer.

Ask for the server configuration details if not provided:
- Server name
- Connection type (stdio or SSE)
- Command and arguments (for stdio)
- URL endpoint (for SSE)
- Environment variables needed

Requirements for the integration:
- Add the server configuration to `mcp_servers.json` following the existing pattern
- Ensure the DownstreamController can properly initialize the connection
- Test both stdio and SSE connection types work correctly
- Update the ServerKit to include the new server's tools
- Verify the Gateway can proxy requests to the new server
- Add proper error handling for connection failures

Use the existing configuration patterns from [mcp_servers.example.json](mcp_servers.example.json) and follow the DownstreamMCPServerConfig model in [domain/downstream_server.py](src/domain/downstream_server.py).

Test the integration by:
1. Starting the MCP Composer service
2. Verifying the new server appears in the Gateway's server list
3. Testing tool execution through the Gateway API
4. Checking logs for proper connection establishment
