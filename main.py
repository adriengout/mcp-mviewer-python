from shared import mcp

import tools.load_xml
import tools.list_all_layers
import tools.list_layers_by_theme
import tools.list_themes
import tools.get_metadata
import tools.spatial_query
import tools.get_bbox
import tools.mviewer_check

try:
    import tools.bbox_to_mviewer_url
    print("[startup] ✅ bbox_to_mviewer_url importé")
except Exception as e:
    print(f"[startup] ❌ ERREUR import bbox_to_mviewer_url: {e}")

import asyncio
import traceback

import playground  # registers /mcp/mviewer/playground routes


async def _debug_mcp_protocol():
    """Appelle list_tools() exactement comme le protocole MCP le ferait."""
    # Essai 1 : méthode list_tools() du tool_manager
    try:
        result = await mcp._tool_manager.list_tools()
        names = [t.name for t in result]
        print(f"[MCP protocol] tools/list retourne ({len(names)}) : {names}")
        return
    except Exception as e:
        print(f"[MCP protocol] list_tools() async échoué : {e}")

    # Essai 2 : version synchrone
    try:
        result = mcp._tool_manager.list_tools()
        names = [t.name for t in result]
        print(f"[MCP protocol] tools/list (sync) retourne ({len(names)}) : {names}")
        return
    except Exception as e:
        print(f"[MCP protocol] list_tools() sync échoué : {e}")

    # Essai 3 : générer le schéma outil par outil pour trouver lequel échoue
    try:
        tools = mcp._tool_manager._tools
        for name, tool in tools.items():
            try:
                _ = tool.parameters
                print(f"[schéma] {name} : OK")
            except Exception as e:
                print(f"[schéma] {name} : ERREUR → {e}")
                traceback.print_exc()
    except Exception as e:
        print(f"[schéma] Impossible d'itérer les outils : {e}")


def _list_registered_tools() -> list[str]:
    # MCP SDK 1.x : _tool_manager._tools (dict privé)
    try:
        return list(mcp._tool_manager._tools.keys())
    except AttributeError:
        pass
    # Variante sans underscore
    try:
        return list(mcp._tool_manager.tools.keys())
    except AttributeError:
        pass
    # FastMCP standalone 2.x
    try:
        return list(mcp._tools.keys())
    except AttributeError:
        pass
    # Fallback : affiche tous les attributs "tool" du mcp pour diagnostiquer
    tool_attrs = [
        f"{a} ({type(getattr(mcp, a)).__name__})"
        for a in dir(mcp)
        if "tool" in a.lower() and not a.startswith("__")
    ]
    print(f"  [debug] attributs tool sur mcp : {tool_attrs}")
    return ["(API FastMCP inconnue — voir debug ci-dessus)"]


def _print_banner():
    host = mcp.settings.host
    port = mcp.settings.port
    base = f"http://{host}:{port}"
    sep = "-" * 52
    registered = _list_registered_tools()
    print(f"\n{sep}")
    print(f"  MCP mviewer")
    print(sep)
    print(f"  MCP endpoint  {base}/mcp/mviewer")
    print(f"  Playground    {base}/mcp/mviewer/playground")
    print(sep)
    print(f"  Outils enregistrés ({len(registered)}) :")
    for name in registered:
        print(f"    - {name}")
    print(sep)
    print(f"  (depuis l'hote Docker : remplacer 0.0.0.0 par localhost)")
    print(f"{sep}\n", flush=True)


if __name__ == "__main__":
    _print_banner()
    asyncio.run(_debug_mcp_protocol())
    mcp.run(transport="streamable-http")