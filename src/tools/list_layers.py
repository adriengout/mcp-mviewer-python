from shared import mcp, context
import json

@mcp.tool()
def list_layers(theme : str|None):
    """Liste les couches déjà chargées"""
    if not context["layers"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"
    layers = context["layers"]
    if theme:
        for layer in layers[theme]:
            

    
    return lines