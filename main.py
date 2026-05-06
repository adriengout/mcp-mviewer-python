from shared import mcp

import tools.load_xml
import tools.list_all_layers
import tools.list_layers_by_theme
import tools.list_themes
import tools.get_metadata
import tools.spatial_query
import tools.get_bbox
import tools.mviewer_check

import playground  # registers /mcp/mviewer/playground routes


def _print_banner():
    host = mcp.settings.host
    port = mcp.settings.port
    base = f"http://{host}:{port}"
    sep = "-" * 52
    print(f"\n{sep}")
    print(f"  MCP mviewer")
    print(sep)
    print(f"  MCP endpoint  {base}/mcp/mviewer")
    print(f"  Playground    {base}/mcp/mviewer/playground")
    print(sep)
    print(f"  (depuis l'hote Docker : remplacer 0.0.0.0 par localhost)")
    print(f"{sep}\n", flush=True)


if __name__ == "__main__":
    _print_banner()
    mcp.run(transport="streamable-http")