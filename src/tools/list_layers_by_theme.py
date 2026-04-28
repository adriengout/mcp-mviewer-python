from shared import mcp, context

@mcp.tool()
def list_layers_by_theme(theme : str):
    """
    Liste les couches géographiques associées à un thème donné.
    Voie d'exploration normale après identification d'un thème
    pertinent via list_themes.

    QUAND UTILISER :
    - Quand l'utilisateur s'intéresse à un sujet correspondant à un
      thème connu ("montre-moi les risques", "et côté environnement ?").
    - Toujours préférer cette voie à list_all_layers, qui est plus
      verbeuse et moins structurée.

    QUAND NE PAS UTILISER :
    - Si le nom de thème ne provient pas de list_themes : NE PAS inventer
      un nom approchant. Appeler list_themes pour vérifier.
    - Pour une recherche transversale tous thèmes confondus : utiliser
      list_all_layers.

    PARAMÈTRE :
    - theme : nom EXACT du thème, tel que retourné par list_themes
      (sensible à la casse et aux accents).

    PRÉCONDITION : load_xml doit avoir été appelé.

    RETOUR : pour chaque couche du thème, une ligne avec id_layer
    (à utiliser pour get_metadata), titre lisible, et URL CSW.
    """
    if not context["layers"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"
    layers = context["layers"]
    lines = []
    for layer in [l for l in layers if l.get("theme") == theme]:
        lines.append(f"id_layer : {layer['id']}, titre : {layer['name']}, métadonnée : {layer['metadata-csw']}")

    return "\n".join(lines)