"""Simple test to verify pytest is working."""


def test_simple_addition():
    """Test that pytest is working with a simple test."""
    assert 1 + 1 == 2


def test_simple_string():
    """Test string operations."""
    assert "hello" + " world" == "hello world"


class TestBasic:
    """Basic test class."""
        
    def test_list_operations(self):
        """Test list operations."""
        test_list = [1, 2, 3]
        assert len(test_list) == 3
        assert test_list[0] == 1
