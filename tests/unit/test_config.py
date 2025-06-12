"""Unit tests for Config class."""
import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open

from src.config import Config
from src.domain.downstream_server import DownstreamMCPServerConfig


class TestConfig:
    """Test cases for Config class."""

    def test_config_initialization_with_defaults(self, monkeypatch):
        """Test config initialization with default values."""
        # Clear environment variables to ensure defaults are used
        monkeypatch.delenv("HOST", raising=False)
        monkeypatch.delenv("PORT", raising=False)
        monkeypatch.delenv("MCP_COMPOSER_PROXY_URL", raising=False)
        
        config = Config()
        
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.mcp_composer_proxy_url == "http://localhost:8000"
        assert isinstance(config.servers, list)

    def test_config_initialization_with_env_vars(self, monkeypatch):
        """Test config initialization with environment variables."""
        monkeypatch.setenv("HOST", "192.168.1.1")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("MCP_COMPOSER_PROXY_URL", "http://example.com:9000")
        
        config = Config()
        
        assert config.host == "192.168.1.1"
        assert config.port == 9000
        assert config.mcp_composer_proxy_url == "http://example.com:9000"

    def test_load_mcp_servers_config_from_json(self, temp_config_file):
        """Test loading MCP servers config from JSON file."""
        # Set the config path
        os.environ["MCP_SERVERS_CONFIG_PATH"] = temp_config_file
        
        config = Config()
        
        assert len(config.servers) == 3
        
        # Check first server (stdio)
        server1 = config.servers[0]
        assert server1.name == "test-server-1"
        assert server1.command == "echo"
        assert server1.args == ["test"]
        
        # Check second server (SSE)
        server2 = config.servers[1]
        assert server2.name == "test-server-2"
        assert server2.url == "http://localhost:9001/mcp"
        
        # Check third server (stdio with env)
        server3 = config.servers[2]
        assert server3.name == "test-stdio-server"
        assert server3.command == "python"
        assert server3.env == {"TEST_VAR": "test_value"}

    def test_load_config_missing_file(self, monkeypatch):
        """Test handling of missing config file."""
        monkeypatch.setenv("MCP_SERVERS_CONFIG_PATH", "/nonexistent/file.json")
        
        config = Config()
        
        # Should not raise exception, but return empty servers list
        assert config.servers == []

    def test_load_config_invalid_json(self, monkeypatch):
        """Test handling of invalid JSON config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            monkeypatch.setenv("MCP_SERVERS_CONFIG_PATH", temp_path)
            
            config = Config()
            
            # Should not raise exception, but return empty servers list
            assert config.servers == []
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_config_empty_mcpservers(self, monkeypatch):
        """Test handling of config file with empty mcpServers."""
        config_data = {"mcpServers": {}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            monkeypatch.setenv("MCP_SERVERS_CONFIG_PATH", temp_path)
            
            config = Config()
            
            assert config.servers == []
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_config_server_missing_command_and_url(self, monkeypatch):
        """Test handling of server config missing both command and url."""
        config_data = {
            "mcpServers": {
                "invalid-server": {
                    "args": ["test"]
                },
                "valid-server": {
                    "command": "echo",
                    "args": ["test"]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            monkeypatch.setenv("MCP_SERVERS_CONFIG_PATH", temp_path)
            
            config = Config()
            
            # Should only load the valid server
            assert len(config.servers) == 1
            assert config.servers[0].name == "valid-server"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_get_config_path_with_default(self):
        """Test getting config path with default value."""
        config = Config()
        path = config._get_config_path("NONEXISTENT_ENV_VAR", "./default.json")
        
        # Path object normalizes "./default.json" to "default.json"
        assert str(path) == "default.json"

    def test_get_config_path_with_env_var(self, monkeypatch):
        """Test getting config path from environment variable."""
        test_path = "/custom/path/config.json"
        monkeypatch.setenv("TEST_CONFIG_PATH", test_path)
        
        config = Config()
        path = config._get_config_path("TEST_CONFIG_PATH", "./default.json")
        
        assert str(path) == test_path

    def test_load_config_unexpected_exception(self, monkeypatch):
        """Test handling of unexpected exceptions during config loading."""
        # Create a valid file path but mock open to raise an unexpected exception
        temp_path = "/tmp/test_config.json"
        monkeypatch.setenv("MCP_SERVERS_CONFIG_PATH", temp_path)
        
        # Mock open to raise a different exception than FileNotFoundError or JSONDecodeError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            config = Config()
            
            # Should handle the exception gracefully and return empty servers list
            assert config.servers == []

    def test_load_config_with_url_server(self, monkeypatch):
        """Test loading server configuration with URL (SSE connection)."""
        config_data = {
            "mcpServers": {
                "sse-server": {
                    "url": "http://localhost:8080/sse",
                    "env": {"API_KEY": "secret"}
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            monkeypatch.setenv("MCP_SERVERS_CONFIG_PATH", temp_path)
            
            config = Config()
            
            assert len(config.servers) == 1
            server = config.servers[0]
            assert server.name == "sse-server"
            assert server.url == "http://localhost:8080/sse"
            assert server.command is None
            assert server.env == {"API_KEY": "secret"}
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_config_mixed_server_types(self, monkeypatch):
        """Test loading configuration with mixed server types (stdio and SSE)."""
        config_data = {
            "mcpServers": {
                "stdio-server": {
                    "command": "python",
                    "args": ["-m", "mcp_server"]
                },
                "sse-server": {
                    "url": "http://localhost:9000/mcp"
                },
                "invalid-server": {
                    "args": ["test"]  # Missing both command and url
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            monkeypatch.setenv("MCP_SERVERS_CONFIG_PATH", temp_path)
            
            config = Config()
            
            # Should load only valid servers
            assert len(config.servers) == 2
            
            stdio_server = next(s for s in config.servers if s.name == "stdio-server")
            assert stdio_server.command == "python"
            assert stdio_server.args == ["-m", "mcp_server"]
            
            sse_server = next(s for s in config.servers if s.name == "sse-server")
            assert sse_server.url == "http://localhost:9000/mcp"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_config_server_with_all_fields(self, monkeypatch):
        """Test loading server configuration with all possible fields."""
        config_data = {
            "mcpServers": {
                "full-server": {
                    "command": "node",
                    "args": ["server.js", "--port", "3000"],
                    "env": {
                        "NODE_ENV": "production",
                        "DEBUG": "true"
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            monkeypatch.setenv("MCP_SERVERS_CONFIG_PATH", temp_path)
            
            config = Config()
            
            assert len(config.servers) == 1
            server = config.servers[0]
            assert server.name == "full-server"
            assert server.command == "node"
            assert server.args == ["server.js", "--port", "3000"]
            assert server.env == {"NODE_ENV": "production", "DEBUG": "true"}
            assert server.url is None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_config_no_mcpservers_key(self, monkeypatch):
        """Test loading configuration file without mcpServers key."""
        config_data = {
            "otherData": {"someKey": "someValue"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            monkeypatch.setenv("MCP_SERVERS_CONFIG_PATH", temp_path)
            
            config = Config()
            
            # Should return empty list when mcpServers key is missing
            assert config.servers == []
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_servers_property(self, monkeypatch):
        """Test that servers property returns the loaded servers list."""
        config_data = {
            "mcpServers": {
                "test-server": {
                    "command": "echo",
                    "args": ["test"]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            monkeypatch.setenv("MCP_SERVERS_CONFIG_PATH", temp_path)
            
            config = Config()
            
            # servers should contain the loaded configuration
            assert isinstance(config.servers, list)
            assert len(config.servers) == 1
            assert config.servers[0].name == "test-server"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_setup_logging_function(self):
        """Test the setup_logging function."""
        from src.config import setup_logging
        import logging
        
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Call setup_logging
        setup_logging()
        
        # Verify that handlers were added
        assert len(root_logger.handlers) == 2
        
        # Check handler types
        handler_types = [type(handler).__name__ for handler in root_logger.handlers]
        assert "StreamHandler" in handler_types

    def test_info_filter(self):
        """Test the InfoFilter class."""
        from src.config import InfoFilter
        import logging
        
        filter_obj = InfoFilter()
        
        # Create mock log records
        info_record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test info", args=(), exc_info=None
        )
        error_record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="test error", args=(), exc_info=None
        )
        
        # InfoFilter should allow INFO but block ERROR
        assert filter_obj.filter(info_record) is True
        assert filter_obj.filter(error_record) is False

    def test_config_with_env_vars_and_proxy_url(self, monkeypatch):
        """Test config with all environment variables including proxy URL."""
        monkeypatch.setenv("HOST", "127.0.0.1")
        monkeypatch.setenv("PORT", "3000")
        monkeypatch.setenv("MCP_COMPOSER_PROXY_URL", "https://proxy.example.com:3000")
        
        config = Config()
        
        assert config.host == "127.0.0.1"
        assert config.port == 3000
        assert config.mcp_composer_proxy_url == "https://proxy.example.com:3000"

    def test_config_manager_integration(self, monkeypatch):
        """Test that Config properly integrates with ConfigurationManager."""
        config_data = {
            "mcpServers": {
                "integration-server": {
                    "command": "node",
                    "args": ["server.js"],
                    "env": {"NODE_ENV": "test"}
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            monkeypatch.setenv("MCP_SERVERS_CONFIG_PATH", temp_path)
            
            config = Config()
            
            # Verify config manager was created with correct path
            assert config.config_manager is not None
            assert str(config.config_manager.config_path) == temp_path
            
            # Verify servers were loaded through config manager
            assert len(config.servers) == 1
            server = config.servers[0]
            assert server.name == "integration-server"
            assert server.command == "node"
            assert server.args == ["server.js"]
            assert server.env == {"NODE_ENV": "test"}
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
