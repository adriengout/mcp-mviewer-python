from shared import mcp, context

@mcp.tool()
def list_layers_by_theme(theme: str):
    """Retourne id/titre/URL CSW des données d'un thème (nom exact issu du Contexte pré-chargé)."""
    if not context["layers"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"

    if theme not in context["themes"]:
        available = ", ".join(context["themes"]) if context["themes"] else "aucun"
        return f"Thème '{theme}' introuvable. Thèmes disponibles : {available}"

    lines = []
    for layer in [l for l in context["layers"] if l.get("theme") == theme]:
        csw = layer["metadata-csw"] or "N/A"
        lines.append(f"id_layer : {layer['id']}, titre : {layer['name']}, métadonnée : {csw}")

    if not lines:
        return f"Le thème '{theme}' existe mais ne contient aucune donnée avec métadonnée CSW."

    return "\n".join(lines)