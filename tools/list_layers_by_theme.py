from shared import mcp, context

@mcp.tool()
def list_layers_by_theme(theme: str):
    """Retourne id/titre/URL CSW des données d'un thème (nom exact issu du Contexte pré-chargé)."""
    if not context["layers"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"
    layers = context["layers"]
    lines = []
    for layer in [l for l in layers if l.get("theme") == theme]:
        lines.append(f"id_layer : {layer['id']}, titre : {layer['name']}, métadonnée : {layer['metadata-csw']}")

    return "\n".join(lines)