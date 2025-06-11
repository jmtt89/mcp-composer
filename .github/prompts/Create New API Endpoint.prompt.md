# Create New API Endpoint

Your goal is to create a new REST API endpoint for the MCP Composer.

Ask for the endpoint specifications if not provided:
- HTTP method (GET, POST, PUT, DELETE)
- URL path and parameters
- Request body schema (if applicable)
- Response schema
- Business logic requirements

Requirements for the endpoint:
- Add the route to `src/api.py` with the `/api/v1` prefix
- Use proper FastAPI decorators and dependency injection
- Implement async/await patterns for I/O operations
- Create Pydantic models for request/response if needed
- Add proper error handling with meaningful HTTP status codes
- Follow the existing pattern of accessing the Composer from `request.app.state.composer`

Use existing endpoints as reference patterns:
- [API routes](src/api.py)
- [Composer methods](src/composer.py)
- [Domain models](src/domain/)

Ensure the endpoint:
1. Follows RESTful conventions
2. Has proper type hints and return types
3. Handles exceptions gracefully
4. Returns appropriate HTTP status codes
5. Integrates with the existing Composer architecture
6. Includes proper logging if needed
