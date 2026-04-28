from shared import mcp, context

@mcp.tool()
def list_themes():
    """
    Liste les thèmes (catégories thématiques de haut niveau) présents
    dans la configuration chargée. Sert à orienter l'utilisateur vers
    le bon domaine de données.

    QUAND UTILISER :
    - Systématiquement juste après load_xml.
    - Quand l'utilisateur demande "qu'est-ce qu'il y a", "quels sujets",
      "quelles thématiques", "que peux-tu m'apprendre sur cette zone".
    - Quand un nom de thème fourni à list_layers_by_theme renvoie une
      liste vide : revenir à list_themes pour vérifier l'orthographe.

    QUAND NE PAS UTILISER :
    - Pour lister des couches précises (utiliser list_layers_by_theme
      ou list_all_layers).

    PRÉCONDITION : load_xml doit avoir été appelé.

    RETOUR : liste de noms de thèmes, par exemple
    ["Environnement", "Risques", "Patrimoine"].
    """
    if not context["themes"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"
    return context["themes"]