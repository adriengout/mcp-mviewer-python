import os

from shared import mcp

import tools.load_xml
import tools.list_all_layers
import tools.list_layers_by_theme
import tools.list_themes
import tools.get_metadata
import tools.spatial_query
import tools.get_bbox
import tools.check_mviewer
import tools.spatial_analysis

import asyncio
import traceback

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
    print(sep)
    print(f"  (depuis l'hote Docker : remplacer 0.0.0.0 par localhost)")
    print(f"{sep}\n", flush=True)


def _preload_context():
    url = os.getenv("DEFAULT_CONFIG_URL", "https://geobretagne.fr/apps/viz/config.xml")
    try:
        result = tools.load_xml.load_xml(url)  # _resolve_config_url appliqué automatiquement
        print(f"[startup] ✅ Contexte pré-chargé : {result}", flush=True)
    except Exception as e:
        print(f"[startup] ⚠️  Échec pré-chargement ({url}) : {e}", flush=True)


if __name__ == "__main__":
    _preload_context()
    _print_banner()
    mcp.run(transport="streamable-http")