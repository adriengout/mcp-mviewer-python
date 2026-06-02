from shared import mcp, context

@mcp.tool()
def list_themes():
    """Retourne la liste des thèmes du contexte chargé (noms exacts, sensibles à la casse)."""
    if not context["themes"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"
    return context["themes"]