import json
import logging
from pathlib import Path
from typing import Dict, List, Any, TYPE_CHECKING
import asyncio

if TYPE_CHECKING:
    from .domain.downstream_server import DownstreamMCPServerConfig
    from .domain.server_kit import ServerKit
    from .domain.mcp_models import MCPServerConfig

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages reading and writing of MCP server configurations and ServerKit assignments."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._lock = asyncio.Lock()
    
    async def load_configuration(self) -> Dict[str, Any]:
        """Load the complete configuration from the JSON file."""
        async with self._lock:
            try:
                if not self.config_path.exists():
                    logger.warning(f"Configuration file not found: {self.config_path}")
                    return {"mcpServers": {}, "serverKitAssignments": {}}
                
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Ensure both sections exist
                if "mcpServers" not in data:
                    data["mcpServers"] = {}
                if "serverKitAssignments" not in data:
                    data["serverKitAssignments"] = {}
                
                return data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse configuration file: {self.config_path}. Error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error loading configuration: {e}")
                raise
    
    async def save_configuration(self, config_data: Dict[str, Any]):
        """Save the complete configuration to the JSON file."""
        async with self._lock:
            try:
                # Create backup of current file if it exists
                if self.config_path.exists():
                    backup_path = self.config_path.with_suffix('.bak')
                    self.config_path.rename(backup_path)
                
                # Write new configuration
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Configuration saved successfully to {self.config_path}")
                
            except Exception as e:
                logger.error(f"Failed to save configuration: {e}")
                # Try to restore backup if write failed
                backup_path = self.config_path.with_suffix('.bak')
                if backup_path.exists():
                    backup_path.rename(self.config_path)
                    logger.info("Restored configuration from backup")
                raise
    
    async def add_mcp_server(self, server_config):
        """Add a new MCP server to the configuration."""
        config_data = await self.load_configuration()
        
        # Check if server already exists
        if server_config.name in config_data["mcpServers"]:
            raise ValueError(f"MCP server '{server_config.name}' already exists in configuration")
        
        # Add new server
        config_data["mcpServers"][server_config.name] = {
            "command": server_config.command,
            "args": server_config.args,
        }
        
        # Add env if provided
        if server_config.env:
            config_data["mcpServers"][server_config.name]["env"] = server_config.env
        
        await self.save_configuration(config_data)
    
    async def remove_mcp_server(self, server_name: str):
        """Remove an MCP server from the configuration."""
        config_data = await self.load_configuration()
        
        # Check if server exists
        if server_name not in config_data["mcpServers"]:
            raise ValueError(f"MCP server '{server_name}' not found in configuration")
        
        # Remove server
        del config_data["mcpServers"][server_name]
        
        # Remove from all ServerKit assignments
        for kit_name, kit_config in config_data["serverKitAssignments"].items():
            if "assigned_servers" in kit_config and server_name in kit_config["assigned_servers"]:
                kit_config["assigned_servers"].remove(server_name)
            
            # Remove server from enabled servers
            if "servers_enabled" in kit_config and server_name in kit_config["servers_enabled"]:
                del kit_config["servers_enabled"][server_name]
            
            # Remove tools from this server
            if "tools_enabled" in kit_config:
                tools_to_remove = [
                    tool_name for tool_name in kit_config["tools_enabled"].keys()
                    if tool_name.startswith(f"{server_name}-")
                ]
                for tool_name in tools_to_remove:
                    del kit_config["tools_enabled"][tool_name]
        
        await self.save_configuration(config_data)
    
    async def update_server_kit_assignments(self, server_kit):
        """Update ServerKit assignments in the configuration."""
        config_data = await self.load_configuration()
        
        # Update or create ServerKit assignment data
        config_data["serverKitAssignments"][server_kit.name] = {
            "assigned_servers": server_kit.assigned_servers,
            "servers_enabled": server_kit.servers_enabled,
            "tools_enabled": server_kit.tools_enabled,
            "servers_tools_hierarchy_map": server_kit.servers_tools_hierarchy_map,
            "tools_servers_map": server_kit.tools_servers_map,
        }
        
        await self.save_configuration(config_data)
    
    async def load_server_kit_assignments(self) -> Dict[str, Dict[str, Any]]:
        """Load ServerKit assignments from configuration."""
        config_data = await self.load_configuration()
        return config_data.get("serverKitAssignments", {})
    
    async def migrate_existing_server_kits(self, server_kits_map):
        """Migrate existing ServerKits to include assigned_servers based on current state."""
        config_data = await self.load_configuration()
        assignments = config_data.get("serverKitAssignments", {})
        
        needs_save = False
        
        for kit_name, server_kit in server_kits_map.items():
            # If kit doesn't have assignment data, create it from current state
            if kit_name not in assignments:
                # For existing kits without assignment data, assign all currently enabled servers
                assigned_servers = [
                    server_name for server_name, enabled in server_kit.servers_enabled.items()
                    if enabled
                ]
                server_kit.assigned_servers = assigned_servers
                
                # Save this migration
                assignments[kit_name] = {
                    "assigned_servers": server_kit.assigned_servers,
                    "servers_enabled": server_kit.servers_enabled,
                    "tools_enabled": server_kit.tools_enabled,
                    "servers_tools_hierarchy_map": server_kit.servers_tools_hierarchy_map,
                    "tools_servers_map": server_kit.tools_servers_map,
                }
                needs_save = True
                
                logger.info(f"Migrated ServerKit '{kit_name}' with {len(assigned_servers)} assigned servers")
            else:
                # Load existing assignment data
                assignment_data = assignments[kit_name]
                server_kit.assigned_servers = assignment_data.get("assigned_servers", [])
                
                # Update other fields if they exist in config
                if "servers_enabled" in assignment_data:
                    server_kit.servers_enabled.update(assignment_data["servers_enabled"])
                if "tools_enabled" in assignment_data:
                    server_kit.tools_enabled.update(assignment_data["tools_enabled"])
                if "servers_tools_hierarchy_map" in assignment_data:
                    server_kit.servers_tools_hierarchy_map.update(assignment_data["servers_tools_hierarchy_map"])
                if "tools_servers_map" in assignment_data:
                    server_kit.tools_servers_map.update(assignment_data["tools_servers_map"])
        
        if needs_save:
            config_data["serverKitAssignments"] = assignments
            await self.save_configuration(config_data)
    
    def get_mcp_servers_for_config_loading(self):
        """Get MCP servers in the format expected by the original Config class (synchronous)."""
        try:
            # Import here to avoid circular imports
            from .domain.downstream_server import DownstreamMCPServerConfig
            
            # Use synchronous file reading for compatibility with existing startup code
            if not self.config_path.exists():
                logger.warning(f"Configuration file not found: {self.config_path}")
                return []
            
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            configs = []
            mcp_servers = data.get("mcpServers", {})
            
            for name, config_data in mcp_servers.items():
                command = config_data.get("command")
                args = config_data.get("args", [])
                env = config_data.get("env")
                url = config_data.get("url")
                
                if not command and not url:
                    logger.warning(f"Server '{name}' missing both 'command' and 'url', skipping")
                    continue
                
                config = DownstreamMCPServerConfig(
                    name=name,
                    command=command,
                    args=args,
                    env=env,
                    url=url
                )
                configs.append(config)
            
            return configs
            
        except Exception as e:
            logger.error(f"Error loading MCP servers configuration: {e}")
            return []
