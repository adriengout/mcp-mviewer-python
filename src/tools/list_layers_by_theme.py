from shared import mcp, context

@mcp.tool()
def list_layers_by_theme(theme : str):
    """
    Liste les couches d'un thème donné. Voie d'exploration normale après
    list_themes.

    PARAM theme : nom EXACT issu de list_themes (pas approchant).
    Si liste vide retournée, vérifier l'orthographe via list_themes.

    RETOUR : layer_id (à passer à get_metadata), titre, URL CSW.
    """
    if not context["layers"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"
    layers = context["layers"]
    lines = []
    for layer in [l for l in layers if l.get("theme") == theme]:
        lines.append(f"id_layer : {layer['id']}, titre : {layer['name']}, métadonnée : {layer['metadata-csw']}")

    return "\n".join(lines)