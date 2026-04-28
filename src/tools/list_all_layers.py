from shared import mcp, context


@mcp.tool()
def list_all_layers():
    """
    Liste plate de toutes les couches, tous thèmes confondus.

    À utiliser pour une recherche transversale ou si le thème est inconnu.
    Préférer list_themes → list_layers_by_theme par défaut (moins verbeux).
    Précondition : load_xml.
    """
    if not context["layers"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"
    layers = context["layers"]
    lines = []
    for layer in layers:
        lines.append(f"id : {layer['id']}, titre : {layer['name']}, métadonnées : {layer['metadata-csw']}")
    return "\n".join(lines)