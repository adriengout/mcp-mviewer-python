from shared import mcp, context

@mcp.tool()
def list_themes():
    """
    Liste les thèmes (catégories) disponibles dans la config chargée.

    À appeler systématiquement après load_xml, et quand l'utilisateur veut
    explorer ce qui est disponible. Précondition : load_xml.

    RETOUR : liste de noms de thèmes exacts (à passer tels quels à
    list_layers_by_theme, sensible casse/accents).
    """
    if not context["themes"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"
    return context["themes"]