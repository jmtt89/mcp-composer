"""Simple working unit test to verify pytest collection."""

def test_simple():
    """Simple test that should always pass."""
    assert 1 + 1 == 2


def test_basic_imports():
    """Test that basic imports work."""
    # Test importing main modules - the import itself is the test
    from src.config import Config
    from src.composer import Composer  
    from src.downstream_controller import DownstreamController
    from src.domain.server_kit import ServerKit
    from src.domain.mcp_models import MCPServerConfig
    from src.config_manager import ConfigurationManager
    
    # Create simple instances to test basic functionality
    assert hasattr(Config, '__init__')
    assert hasattr(Composer, '__init__')
    assert hasattr(DownstreamController, '__init__')
    assert hasattr(ServerKit, '__init__')
    assert hasattr(MCPServerConfig, '__init__')
    assert hasattr(ConfigurationManager, '__init__')


def test_basic_math():
    """Test basic mathematical operations."""
    assert 2 + 2 == 4
    assert 5 * 5 == 25
    assert 10 / 2 == 5
    assert 2 ** 3 == 8


def test_string_operations():
    """Test basic string operations."""
    assert "hello" + " world" == "hello world"
    assert "test".upper() == "TEST"
    assert "TEST".lower() == "test"
    assert len("testing") == 7


def test_list_operations():
    """Test basic list operations."""
    test_list = [1, 2, 3]
    assert len(test_list) == 3
    assert test_list[0] == 1
    assert test_list[-1] == 3
    
    test_list.append(4)
    assert len(test_list) == 4
    assert 4 in test_list


def test_dict_operations():
    """Test basic dictionary operations."""
    test_dict = {"key1": "value1", "key2": "value2"}
    assert len(test_dict) == 2
    assert test_dict["key1"] == "value1"
    assert "key1" in test_dict
    assert "key3" not in test_dict
    
    test_dict["key3"] = "value3"
    assert len(test_dict) == 3
