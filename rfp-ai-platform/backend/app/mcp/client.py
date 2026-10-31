"""
MCP Client & LangChain Tool Adapter
Bridges custom and standard MCP servers to LangChain and LangGraph agent runtimes.
"""

import inspect
import functools
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool, StructuredTool

from app.mcp.rfp_document_server import mcp as doc_mcp
from app.mcp.knowledge_base_server import mcp as kb_mcp
from app.mcp.compliance_server import mcp as comp_mcp
from app.mcp.proposal_server import mcp as prop_mcp

SERVERS = {
    "document": doc_mcp,
    "knowledge_base": kb_mcp,
    "compliance": comp_mcp,
    "proposal": prop_mcp
}


def _adapt_fastmcp_tool(tool_def) -> BaseTool:
    """Wraps a FastMCP tool definition into a robust LangChain StructuredTool."""
    fn = tool_def.fn
    name = tool_def.name
    description = tool_def.description or (fn.__doc__ or f"Execute {name}")
    
    # Safe wrapper with signature preservation and error interceptor
    @functools.wraps(fn)
    def safe_wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            return {"error": f"Tool execution failed for {name}: {str(e)}", "success": False}
            
    # Wrap with Pydantic signature from function
    tool = StructuredTool.from_function(
        func=safe_wrapper,
        name=name,
        description=description,
        return_direct=False
    )
    return tool


class MCPClientManager:
    """Central manager for discovering, configuring, and invoking MCP tools."""
    
    def __init__(self):
        self._tools_cache: Dict[str, BaseTool] = {}
        self._refresh_tools()
        
    def _refresh_tools(self):
        for s_name, server in SERVERS.items():
            for t_def in server._tool_manager.list_tools():
                adapted = _adapt_fastmcp_tool(t_def)
                self._tools_cache[t_def.name] = adapted
                
    def get_all_tools(self) -> List[BaseTool]:
        """Returns all registered MCP tools across all servers."""
        return list(self._tools_cache.values())
        
    def get_tools_for_server(self, server_name: str) -> List[BaseTool]:
        """Returns tools belonging to a specific MCP server (e.g., 'compliance')."""
        server = SERVERS.get(server_name)
        if not server:
            return []
        tool_names = [t.name for t in server._tool_manager.list_tools()]
        return [self._tools_cache[name] for name in tool_names if name in self._tools_cache]
        
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Fetch a specific tool by name."""
        return self._tools_cache.get(tool_name)


# Singleton Client Instance
mcp_client = MCPClientManager()
