#!/usr/bin/env python3
"""
Graphiti MCP Server - Exposes Graphiti functionality through the Model Context Protocol (MCP)
"""

import asyncio
import anyio

from .mcp_server import MCPServer, is_mcp_initialized
from .clients import GraphitiClient, is_graphiti_initialized
from .mcp_server.stateful_fastmcp import StatefulFastMCP
from .mcp_server.instructions import GRAPHITI_MCP_INSTRUCTIONS
from utils import logger


class GraphitiMCPServer:

    @staticmethod
    async def initialize():
        """Create and start the Graphiti MCP server"""
        if not is_graphiti_initialized():
            await GraphitiClient.initialize()
        if not is_mcp_initialized():
            await MCPServer.initialize()

    @staticmethod
    async def start():
        """Start the Graphiti MCP server"""
        if not GraphitiMCPServer.is_initialized():
            await GraphitiMCPServer.initialize()

        await MCPServer.start()

    @staticmethod
    async def stop():
        """Stop the Graphiti MCP server"""
        await MCPServer.stop()
        await GraphitiClient.cleanup()

    @staticmethod
    async def restart():
        """Restart the Graphiti MCP server"""
        await GraphitiClient.cleanup()
        await GraphitiClient.initialize()
        await MCPServer.restart()

    @staticmethod
    def is_initialized() -> bool:
        """Check if the server is initialized"""
        return is_graphiti_initialized() and is_mcp_initialized()


async def run_mcp_server():
    """Run the Graphiti MCP server with streamable-http transport"""
    await GraphitiMCPServer.initialize()
    await GraphitiMCPServer.start()


def run_mcp_stdio_server():
    """Run the Graphiti MCP server with stdio transport (for testing without Neo4j)"""
    try:
        # Skip Graphiti client initialization for testing
        logger.info("🔧 Running in test mode - skipping Graphiti client initialization")

        # Create FastMCP instance
        mcp = StatefulFastMCP(
            'Graphiti Agent Memory',
            instructions=GRAPHITI_MCP_INSTRUCTIONS,
        )

        # Import helpers directly to avoid issues
        from graphiti_pro_core.mcp_server import helpers

        # Initialize various components
        helpers.initialize_network(mcp)
        helpers.add_custom_routes(mcp)
        helpers.add_tools(mcp)  # This registers all tools
        helpers.add_resources(mcp)

        # Skip integration and task manager initialization for now
        logger.info("⚠️ Skipping integration and task manager initialization for testing")

        logger.info("🚀 Starting Graphiti MCP server with stdio transport...")
        logger.info("⚠️ Note: This is running in test mode. Tools that require Graphiti client will fail until Neo4j is configured.")
        mcp.run(transport="stdio")

    except Exception as e:
        logger.error(f'❌ Error running Graphiti MCP server: {str(e)}')
        raise


async def graceful_stop_mcp_server():
    """Gracefully stop the Graphiti MCP server"""
    await GraphitiMCPServer.stop()


if __name__ == '__main__':
    asyncio.run(run_mcp_server())