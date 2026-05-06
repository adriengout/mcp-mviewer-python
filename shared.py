from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcpWFS",
              host="0.0.0.0",
              port=8000)

mcp.settings.streamable_http_path = "/mcp/mviewer"

context = {
    "layers": [],
    "themes": [],
    "title": None,
}

