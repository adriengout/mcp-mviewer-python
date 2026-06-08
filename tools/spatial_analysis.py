from shared import mcp, context
import httpx
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

_MAX_CONCURRENT = 15


def _wms_to_wfs(url: str) -> str:
    """Convertit une URL WMS GeoServer en URL WFS (remplace /wms par /wfs)."""
    return url.replace("/wms", "/wfs").replace("/WMS", "/wfs")


def _check_layer(layer: dict, bbox_txt: str) -> tuple[str, str, int]:
    """Retourne un tuple (statut, layer_id, count) : 'found', 'not_found' ou 'unaccessible'."""
    if not layer.get("url"):
        return ("unaccessible", layer["id"], 0)
    wfs_url = _wms_to_wfs(layer["url"])
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": layer["id"],
        "outputFormat": "application/json",
        "resultType": "hits",
        "BBOX": bbox_txt,
    }
    try:
        response = httpx.get(wfs_url, params=params, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        count = int(root.get("numberMatched", 0))
        if count > 0:
            return ("found", layer["id"], count)
        else:
            return ("not_found", layer["id"], 0)
    except Exception:
        return ("unaccessible", layer["id"], 0)


@mcp.tool()
def spatial_analysis(bbox: list[float]) -> dict:
    """Scan toutes les couches du contexte et retourne les layer_id ayant des données dans la bbox."""
    if not context["layers"]:
        return "Contexte vide, exécuter load_xml avant"

    bbox_txt = ",".join(str(n) for n in bbox) + ",EPSG:4326"
    result = {"found": [], "not_found": [], "unaccessible": []}

    with ThreadPoolExecutor(max_workers=_MAX_CONCURRENT) as executor:
        futures = {
            executor.submit(_check_layer, layer, bbox_txt): layer["id"]
            for layer in context["layers"]
        }
        for future in as_completed(futures):
            status, layer_id, count = future.result()
            if status == "found":
                result[status].append({"id": layer_id, "count": count})
            else:
                result[status].append(layer_id)

    return result
