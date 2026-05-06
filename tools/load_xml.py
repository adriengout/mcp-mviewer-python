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
    """
    Charge une config XML mviewer et indexe ses couches/thèmes en mémoire.
    Point d'entrée obligatoire de toute session.

    Appeler list_themes juste après pour présenter les catégories à l'utilisateur.
    Ne pas recharger si un contexte est déjà actif (vérifier avec list_themes).

    PARAM url : URL du config.xml fournie par l'utilisateur. Ne pas inventer.
    """
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
        
    return f"{len(layers)} couches chargées"