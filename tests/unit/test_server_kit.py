"""Unit tests for ServerKit domain model."""
import pytest
from src.domain.server_kit import ServerKit


class TestServerKit:
    """Test cases for ServerKit domain model."""

    def test_new_server_kit_creation(self):
        """Test creating a new server kit."""
        kit = ServerKit.new_server_kit("test-kit")
        
        assert kit.name == "test-kit"
        assert kit.enabled is True
        assert kit.servers_enabled == {}
        assert kit.tools_enabled == {}
        assert kit.servers_tools_hierarchy_map == {}
        assert kit.tools_servers_map == {}

    def test_server_kit_initialization_with_data(self):
        """Test initializing server kit with existing data."""
        servers_enabled = {"server1": True, "server2": False}
        tools_enabled = {"tool1": True, "tool2": False}
        hierarchy_map = {"server1": ["tool1"], "server2": ["tool2"]}
        tools_servers_map = {"tool1": "server1", "tool2": "server2"}
        
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            servers_enabled=servers_enabled,
            tools_enabled=tools_enabled,
            servers_tools_hierarchy_map=hierarchy_map,
            tools_servers_map=tools_servers_map
        )
        
        assert kit.name == "test-kit"
        assert kit.enabled is True
        assert kit.servers_enabled == servers_enabled
        assert kit.tools_enabled == tools_enabled
        assert kit.servers_tools_hierarchy_map == hierarchy_map
        assert kit.tools_servers_map == tools_servers_map

    def test_list_enabled_tool_names_all_enabled(self):
        """Test listing enabled tool names when all are enabled."""
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            servers_enabled={"server1": True, "server2": True},
            tools_enabled={"tool1": True, "tool2": True},
            servers_tools_hierarchy_map={"server1": ["tool1"], "server2": ["tool2"]},
            tools_servers_map={"tool1": "server1", "tool2": "server2"}
        )
        
        enabled_tools = kit.list_enabled_tool_names()
        
        assert set(enabled_tools) == {"tool1", "tool2"}

    def test_list_enabled_tool_names_server_disabled(self):
        """Test listing enabled tool names when server is disabled."""
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            servers_enabled={"server1": True, "server2": False},
            tools_enabled={"tool1": True, "tool2": True},
            servers_tools_hierarchy_map={"server1": ["tool1"], "server2": ["tool2"]},
            tools_servers_map={"tool1": "server1", "tool2": "server2"}
        )
        
        enabled_tools = kit.list_enabled_tool_names()
        
        # Only tool1 should be enabled since server2 is disabled
        assert enabled_tools == ["tool1"]

    def test_list_enabled_tool_names_tool_disabled(self):
        """Test listing enabled tool names when tool is disabled."""
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            servers_enabled={"server1": True, "server2": True},
            tools_enabled={"tool1": True, "tool2": False},
            servers_tools_hierarchy_map={"server1": ["tool1"], "server2": ["tool2"]},
            tools_servers_map={"tool1": "server1", "tool2": "server2"}
        )
        
        enabled_tools = kit.list_enabled_tool_names()
        
        # Only tool1 should be enabled since tool2 is disabled
        assert enabled_tools == ["tool1"]

    def test_list_enabled_tool_names_empty(self):
        """Test listing enabled tool names when none are enabled."""
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            servers_enabled={"server1": False, "server2": False},
            tools_enabled={"tool1": True, "tool2": True},
            servers_tools_hierarchy_map={"server1": ["tool1"], "server2": ["tool2"]},
            tools_servers_map={"tool1": "server1", "tool2": "server2"}
        )
        
        enabled_tools = kit.list_enabled_tool_names()
        
        assert enabled_tools == []

    def test_disable_kit(self):
        """Test disabling a server kit."""
        kit = ServerKit.new_server_kit("test-kit")
        assert kit.enabled is True
        
        kit.disable_kit()
        
        assert kit.enabled is False

    def test_enable_kit(self):
        """Test enabling a server kit."""
        kit = ServerKit.new_server_kit("test-kit")
        kit.enabled = False
        
        kit.enable_kit()
        
        assert kit.enabled is True

    def test_disable_server(self):
        """Test disabling a server."""
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            servers_enabled={"server1": True},
            tools_enabled={},
            servers_tools_hierarchy_map={},
            tools_servers_map={}
        )
        
        kit.disable_server("server1")
        
        assert kit.servers_enabled["server1"] is False

    def test_enable_server(self):
        """Test enabling a server."""
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            servers_enabled={"server1": False},
            tools_enabled={},
            servers_tools_hierarchy_map={},
            tools_servers_map={}
        )
        
        kit.enable_server("server1")
        
        assert kit.servers_enabled["server1"] is True

    def test_disable_tool(self):
        """Test disabling a tool."""
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            servers_enabled={},
            tools_enabled={"tool1": True},
            servers_tools_hierarchy_map={},
            tools_servers_map={}
        )
        
        kit.disable_tool("tool1")
        
        assert kit.tools_enabled["tool1"] is False

    def test_enable_tool(self):
        """Test enabling a tool."""
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            servers_enabled={},
            tools_enabled={"tool1": False},
            servers_tools_hierarchy_map={},
            tools_servers_map={}
        )
        
        kit.enable_tool("tool1")
        
        assert kit.tools_enabled["tool1"] is True

    def test_complex_hierarchy_scenario(self):
        """Test complex scenario with multiple servers and tools."""
        kit = ServerKit(
            name="complex-kit",
            enabled=True,
            servers_enabled={"server1": True, "server2": False, "server3": True},
            tools_enabled={
                "server1-tool1": True,
                "server1-tool2": False,
                "server2-tool1": True,
                "server3-tool1": True
            },
            servers_tools_hierarchy_map={
                "server1": ["server1-tool1", "server1-tool2"],
                "server2": ["server2-tool1"],
                "server3": ["server3-tool1"]
            },
            tools_servers_map={
                "server1-tool1": "server1",
                "server1-tool2": "server1",
                "server2-tool1": "server2",
                "server3-tool1": "server3"
            }
        )
        
        enabled_tools = kit.list_enabled_tool_names()
        
        # Only server1-tool1 and server3-tool1 should be enabled
        # server1-tool2 is disabled, server2-tool1's server is disabled
        assert set(enabled_tools) == {"server1-tool1", "server3-tool1"}

    def test_pydantic_model_validation(self):
        """Test that ServerKit validates as a Pydantic model."""
        # Test invalid data type
        with pytest.raises(ValueError):
            ServerKit(
                name=123,  # type: ignore # Should be string - testing validation
                enabled=True,
                servers_enabled={},
                tools_enabled={},
                servers_tools_hierarchy_map={},
                tools_servers_map={}
            )

    def test_model_serialization(self):
        """Test ServerKit model serialization."""
        kit = ServerKit.new_server_kit("test-kit")
        
        # Test dict conversion
        kit_dict = kit.model_dump()
        assert kit_dict["name"] == "test-kit"
        assert kit_dict["enabled"] is True
        
        # Test JSON serialization
        kit_json = kit.model_dump_json()
        assert "test-kit" in kit_json
        assert "true" in kit_json.lower()

    # === Tests for New Assignment Functionality ===

    def test_assign_mcp_server(self):
        """Test assigning an MCP server to a ServerKit."""
        kit = ServerKit.new_server_kit("test-kit")
        
        kit.assign_mcp_server("server1")
        
        assert kit.is_server_assigned("server1")
        assert "server1" in kit.assigned_servers
        assert kit.servers_enabled["server1"] is True

    def test_assign_mcp_server_already_assigned(self):
        """Test assigning an already assigned server doesn't duplicate."""
        kit = ServerKit.new_server_kit("test-kit")
        
        kit.assign_mcp_server("server1")
        kit.assign_mcp_server("server1")  # Assign again
        
        assert kit.assigned_servers.count("server1") == 1
        assert kit.is_server_assigned("server1")

    def test_unassign_mcp_server(self):
        """Test unassigning an MCP server from a ServerKit."""
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            assigned_servers=["server1"],
            servers_enabled={"server1": True},
            tools_enabled={"server1-tool1": True, "server1-tool2": False},
            servers_tools_hierarchy_map={"server1": ["server1-tool1", "server1-tool2"]},
            tools_servers_map={"server1-tool1": "server1", "server1-tool2": "server1"}
        )
        
        kit.unassign_mcp_server("server1")
        
        assert not kit.is_server_assigned("server1")
        assert "server1" not in kit.assigned_servers
        assert "server1" not in kit.servers_enabled
        assert "server1-tool1" not in kit.tools_enabled
        assert "server1-tool2" not in kit.tools_enabled
        assert "server1-tool1" not in kit.tools_servers_map
        assert "server1-tool2" not in kit.tools_servers_map
        assert "server1" not in kit.servers_tools_hierarchy_map

    def test_unassign_mcp_server_not_assigned(self):
        """Test unassigning a server that wasn't assigned."""
        kit = ServerKit.new_server_kit("test-kit")
        
        # Should not raise error
        kit.unassign_mcp_server("nonexistent-server")
        
        assert not kit.is_server_assigned("nonexistent-server")

    def test_list_assigned_servers(self):
        """Test listing assigned servers."""
        kit = ServerKit.new_server_kit("test-kit")
        
        kit.assign_mcp_server("server1")
        kit.assign_mcp_server("server2")
        
        assigned = kit.list_assigned_servers()
        
        assert set(assigned) == {"server1", "server2"}
        # Should return a copy, not the original list
        assigned.append("server3")
        assert "server3" not in kit.assigned_servers

    def test_is_server_assigned(self):
        """Test checking if a server is assigned."""
        kit = ServerKit.new_server_kit("test-kit")
        
        assert not kit.is_server_assigned("server1")
        
        kit.assign_mcp_server("server1")
        
        assert kit.is_server_assigned("server1")
        assert not kit.is_server_assigned("server2")

    def test_list_enabled_tool_names_with_assigned_servers_filter(self):
        """Test that list_enabled_tool_names respects assigned_servers filter."""
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            assigned_servers=["server1"],  # Only server1 is assigned
            servers_enabled={"server1": True, "server2": True},
            tools_enabled={"server1-tool1": True, "server2-tool1": True},
            servers_tools_hierarchy_map={"server1": ["server1-tool1"], "server2": ["server2-tool1"]},
            tools_servers_map={"server1-tool1": "server1", "server2-tool1": "server2"}
        )
        
        enabled_tools = kit.list_enabled_tool_names()
        
        # Only tools from assigned servers should be returned
        assert enabled_tools == ["server1-tool1"]
        assert "server2-tool1" not in enabled_tools

    def test_list_enabled_tool_names_no_assigned_servers_filter(self):
        """Test that empty assigned_servers list doesn't filter anything (backward compatibility)."""
        kit = ServerKit(
            name="test-kit",
            enabled=True,
            assigned_servers=[],  # Empty list = no filtering
            servers_enabled={"server1": True, "server2": True},
            tools_enabled={"server1-tool1": True, "server2-tool1": True},
            servers_tools_hierarchy_map={"server1": ["server1-tool1"], "server2": ["server2-tool1"]},
            tools_servers_map={"server1-tool1": "server1", "server2-tool1": "server2"}
        )
        
        enabled_tools = kit.list_enabled_tool_names()
        
        # All enabled tools should be returned when no assignment filter
        assert set(enabled_tools) == {"server1-tool1", "server2-tool1"}

    def test_complex_assignment_scenario(self):
        """Test complex scenario with assignment, enabling/disabling."""
        kit = ServerKit.new_server_kit("test-kit")
        
        # Assign multiple servers
        kit.assign_mcp_server("server1")
        kit.assign_mcp_server("server2")
        
        # Add tools manually (simulating what composer does)
        kit.tools_enabled.update({
            "server1-tool1": True,
            "server1-tool2": False,
            "server2-tool1": True
        })
        kit.tools_servers_map.update({
            "server1-tool1": "server1",
            "server1-tool2": "server1", 
            "server2-tool1": "server2"
        })
        kit.servers_tools_hierarchy_map.update({
            "server1": ["server1-tool1", "server1-tool2"],
            "server2": ["server2-tool1"]
        })
        
        # Test initial state
        enabled_tools = kit.list_enabled_tool_names()
        assert set(enabled_tools) == {"server1-tool1", "server2-tool1"}
        
        # Disable server1
        kit.disable_server("server1")
        enabled_tools = kit.list_enabled_tool_names()
        assert enabled_tools == ["server2-tool1"]
        
        # Unassign server2
        kit.unassign_mcp_server("server2")
        enabled_tools = kit.list_enabled_tool_names()
        assert enabled_tools == []  # No tools should be available
