from shared import mcp, context


@mcp.tool()
def list_all_layers():
    """
    Liste exhaustive de toutes les couches indexées, tous thèmes
    confondus. Vue plate.

    QUAND UTILISER :
    - Quand l'utilisateur demande explicitement "tout", "la liste
      complète", "toutes les couches".
    - Pour une recherche par mot-clé dans les titres quand le thème
      n'est pas évident a priori.
    - Pour vérifier si un layer_id mentionné par l'utilisateur existe
      bien dans le contexte chargé.

    QUAND NE PAS UTILISER :
    - Comme premier réflexe d'exploration : préférer la séquence
      list_themes → list_layers_by_theme, plus lisible et moins
      coûteuse en tokens sur des configs volumineuses.

    PRÉCONDITION : load_xml doit avoir été appelé.

    RETOUR : pour chaque couche, une ligne avec id, titre, URL CSW.
    """
    if not context["layers"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"
    layers = context["layers"]
    lines = []
    for layer in layers:
        lines.append(f"id : {layer['id']}, titre : {layer['name']}, métadonnées : {layer['metadata-csw']}")
    return "\n".join(lines)