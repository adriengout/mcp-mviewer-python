import xmltodict
import httpx
from shared import mcp, context


def to_list(val):
    """Convertit en liste : None→[], dict→[dict], list→list"""
    if val is None:
        return []
    if isinstance(val, dict):
        return [val]
    return val

@mcp.tool()
def load_xml(url: str):
    """Outil pour charger un xml dans la conversation"""
    response = httpx.get(url)
    response.raise_for_status()
    data = xmltodict.parse(response.text)

    config = data['config']
    themes = to_list(config["themes"]["theme"])

    layers = []
    for theme in themes:
        for group in to_list(theme.get("group")):
            if isinstance(group, str):
                continue
            for layer in to_list(group.get("layer")):
                if isinstance(layer, str):
                    continue
                layers.append({
                    "id": layer.get("@id"),
                    "url": layer.get("@url"),
                    "theme": theme.get("@name"),
                    "group": group.get("@name"),
                })
        for layer in to_list(theme.get("layer")):
            if isinstance(layer, str):
                continue
            layers.append({
                "id": layer.get("@id"),
                "url": layer.get("@url"),
                "theme": theme.get("@name"),
                "group": None,
            })
    context["layers"] = layers   # ← stocke en mémoire
    context["title"] = config["application"].get("@title")
        
    return f"{len(layers)} couches chargées"