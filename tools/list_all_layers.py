from shared import mcp, context


@mcp.tool()
def list_all_layers():
    """Retourne id/titre/URL CSW de toutes les données, tous thèmes confondus."""
    if not context["layers"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"
    layers = context["layers"]
    lines = []
    for layer in layers:
        lines.append(f"id : {layer['id']}, titre : {layer['name']}, métadonnées : {layer['metadata-csw']}")
    return "\n".join(lines)