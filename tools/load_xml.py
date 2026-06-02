import re
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


def _resolve_config_url(url: str) -> str:
    """Transforme une URL de carte MViewer en URL de config.
    Ex: geobretagne.fr/app/lorient/ → geobretagne.fr/app/lorient/apps/default
    Les URLs déjà pointant vers un fichier de config sont retournées telles quelles.
    """
    clean = url.rstrip('/').split('?')[0].split('#')[0]
    if re.search(r'/app/[\w_-]+$', clean):
        return clean + '/apps/default.xml'
    return url


@mcp.tool()
def load_xml(url: str):
    """Charge un config.xml mviewer et indexe données/thèmes en mémoire. Accepte une URL de config (.xml) ou une URL de carte (/app/<nom>/) — la conversion est automatique. Retourne le nombre de données chargées."""
    url = _resolve_config_url(url)
    response = httpx.get(url)
    response.raise_for_status()
    data = xmltodict.parse(response.text)

    config = data['config']
    themes = to_list(config["themes"]["theme"])

    layers = []
    for theme in themes: #liste de thèmes
        for group in to_list(theme.get("group")):
            if isinstance(group, str):
                continue
            for layer in to_list(group.get("layer")):
                if isinstance(layer, str) or not layer.get("@metadata-csw"):
                    continue
                layers.append({
                    "id": layer.get("@id"),
                    "name": layer.get("@name"),
                    "url": layer.get("@url"),
                    "metadata-csw": layer.get("@metadata-csw"),
                    "theme": theme.get("@name"),
                    "group": group.get("@name"),
                })
        for layer in to_list(theme.get("layer")):
            if isinstance(layer, str) or not layer.get("@metadata-csw"):
                continue
            layers.append({
                "id": layer.get("@id"),
                "name": layer.get("@name"),
                "url": layer.get("@url"),
                "metadata-csw": layer.get("@metadata-csw"),
                "theme": theme.get("@name"),
                "group": None,
            })
    context["layers"] = layers
    context["themes"] = [t.get("@name") for t in themes if t.get("@name")]
    context["title"] = config["application"].get("@title")
        
    return f"{len(layers)} données chargées"