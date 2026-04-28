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
    Charge un fichier de configuration XML d'application WebSIG (mviewer)
    et indexe en mémoire toutes les couches géographiques et thèmes
    qu'il référence. Point d'entrée obligatoire de toute session.

    QUAND UTILISER :
    - Au début de la conversation, dès que l'utilisateur fournit une URL
      de config XML.
    - Si l'utilisateur change d'application ou veut "recharger".

    QUAND NE PAS UTILISER :
    - Si un contexte est déjà chargé pour la même URL et que l'utilisateur
      ne demande pas explicitement de recharger (vérifier avec list_themes
      ou list_all_layers d'abord). Recharger écrase l'état courant et fait
      perdre les wfs_url enrichis par get_metadata.

    PARAMÈTRE :
    - url : URL complète d'un fichier config.xml (commence par http:// ou
      https://). Ne pas inventer d'URL : elle doit avoir été fournie par
      l'utilisateur.

    APRÈS APPEL : appeler list_themes pour présenter les grandes
    catégories à l'utilisateur. Ne jamais répondre à une question
    "que peux-tu faire ?" sans avoir d'abord listé les thèmes.

    RETOUR : message texte indiquant le nombre de couches indexées.
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