"""Unit tests for Config class."""
import os
import json
import tempfile
from pathlib import Path
import pytest

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
