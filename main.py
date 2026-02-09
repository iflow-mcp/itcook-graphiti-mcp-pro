#!/usr/bin/env python3
"""
Graphiti MCP Server - Exposes Graphiti functionality through the Model Context Protocol (MCP)
"""

import asyncio
import argparse
import os

from graphiti_pro_core import run_mcp_server, run_mcp_stdio_server, graceful_stop_mcp_server
from utils import setup_logging, set_library_log_level, LogLevel, logger

# Conditional import for backend server to handle different environments
try:
    # Local development environment path
    from manager.backend.app import run_backend_server
except ImportError:
    try:
        # Docker environment path
        from backend.app import run_backend_server # pyright: ignore[reportMissingImports]
    except ImportError as e:
        logger.error(f"Failed to import backend modules: {e}")
        run_backend_server = None


setup_logging()
set_library_log_level('neo4j', LogLevel.ERROR)

async def main_async():
    """Main async function to run the Graphiti MCP server."""
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Graphiti MCP Server')
        parser.add_argument('-m', '--manager', action='store_true',
                          help='Run with manager backend server')
        parser.add_argument('--stdio', action='store_true',
                          help='Run with stdio transport protocol (for testing)')
        args = parser.parse_args()

        # Check for MCP_TRANSPORT environment variable
        transport = os.environ.get('MCP_TRANSPORT', '').lower()

        if args.manager:
            # Run both MCP server and backend server concurrently
            logger.info("🚀 Starting MCP server with manager backend...")
            await asyncio.gather(
                run_mcp_server(),
                run_backend_server()
            )
        elif args.stdio or transport == 'stdio':
            # Run MCP server with stdio transport (synchronous)
            logger.info("🚀 Starting MCP server with stdio transport...")
            run_mcp_stdio_server()
        else:
            # Run only MCP server with default transport (streamable-http)
            logger.info("🚀 Starting MCP server with streamable-http transport...")
            await run_mcp_server()

    except asyncio.CancelledError:
        await graceful_stop_mcp_server()
        logger.info("🛑 Received cancellation, shutting down gracefully")
        raise
    except Exception as e:
        logger.error(f'❌ Error running Graphiti MCP server: {str(e)}')
        raise

def main():
    """Main function to run the Graphiti MCP server."""
    try:
        # Parse command line arguments to check for stdio mode
        parser = argparse.ArgumentParser(description='Graphiti MCP Server')
        parser.add_argument('-m', '--manager', action='store_true',
                          help='Run with manager backend server')
        parser.add_argument('--stdio', action='store_true',
                          help='Run with stdio transport protocol (for testing)')
        args, _ = parser.parse_known_args()

        # Check for MCP_TRANSPORT environment variable
        transport = os.environ.get('MCP_TRANSPORT', '').lower()

        if args.stdio or transport == 'stdio':
            # Run synchronously for stdio mode
            run_mcp_stdio_server()
        else:
            # Run everything in a single event loop for async mode
            asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt (Ctrl+C), shutting down gracefully")
    except Exception as e:
        logger.error(f'❌ Error running Graphiti MCP server: {str(e)}')
        raise

if __name__ == '__main__':
    main()