import anyio
import click
import logging
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route

# Import local modules
from .api_client import PearlApiClient
from .config import Config
from .resources import register_resources
from .tools import register_tools
from .prompts import register_prompts

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(api_key: str) -> FastMCP:
    """Create and configure the MCP server application"""
    # Initialize configuration
    Config.initialize(api_key=api_key)
    
    # Initialize Pearl API client
    pearl_api_client = PearlApiClient(
        api_key=Config.PEARL_API_KEY,
        base_url=Config.PEARL_API_BASE_URL
    )
    
    # Create server instance using FastMCP
    app = FastMCP("pearlapi")
    
    # Register all components
    register_resources(app)
    register_tools(app, pearl_api_client)
    register_prompts(app)
    
    logger.info(f"Pearl MCP server initialized with name: {app.name}")
    return app

@click.command()
@click.option("--api-key", required=True, help="Pearl API key")
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(api_key: str, port: int, transport: str) -> int:
    """Main entry point for the MCP server"""
    try:
        app = create_app(api_key)
        
        if transport == "sse":
            # Set up SSE transport
            sse = SseServerTransport("/messages/")

            async def handle_sse(request):
                async with sse.connect_sse(
                    request.scope, request.receive, request._send
                ) as streams:
                    await app._mcp_server.run(
                        streams[0], streams[1], app._mcp_server.create_initialization_options()
                    )
                return Response()

            # Create Starlette app with SSE routes
            starlette_app = Starlette(
                debug=True,
                routes=[
                    Route("/sse", endpoint=handle_sse, methods=["GET"]),
                    Mount("/messages/", app=sse.handle_post_message),
                ],
            )

            # Run with uvicorn
            import uvicorn
            uvicorn.run(starlette_app, host="0.0.0.0", port=port)
        else:
            # Run with stdio transport
            async def arun():
                async with stdio_server() as streams:
                    await app._mcp_server.run(
                        streams[0], streams[1], app._mcp_server.create_initialization_options()
                    )
            anyio.run(arun)

        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    main()