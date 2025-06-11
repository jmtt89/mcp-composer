# Add Configuration Option

Your goal is to add a new configuration option to the MCP Composer.

Ask for the configuration details if not provided:
- Configuration parameter name
- Default value
- Environment variable name
- Where it should be used in the application
- Validation requirements

Requirements for configuration options:
- Add the environment variable to [.env.example](.env.example)
- Update the Config class in [src/config.py](src/config.py)
- Add proper type hints and default values
- Include validation if needed
- Update documentation in README.md if user-facing

Configuration patterns to follow:
- Use `os.environ.get()` for reading environment variables
- Provide sensible default values
- Use proper type conversion (int, bool, etc.)
- Add logging for configuration loading if needed
- Follow the existing naming conventions

Existing configuration examples:
- `HOST` and `PORT` for server binding
- `MCP_COMPOSER_PROXY_URL` for external URL configuration
- `MCP_SERVERS_CONFIG_PATH` for config file location

Integration points:
- Pass configuration through the Config object to other components
- Update the Composer initialization if needed
- Modify Docker configuration if the option affects deployment
- Update the application startup process if required

Test the configuration:
1. Verify default values work correctly
2. Test with environment variables set
3. Validate error handling for invalid values
4. Check configuration loading during application startup
