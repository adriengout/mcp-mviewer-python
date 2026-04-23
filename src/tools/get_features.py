from shared import mcp, context

def derive_wfs_url(wms_url: str) -> str:
    if not wms_url:
        return None
    
    if "/gwc/service/wms" in wms_url:
        return wms_url.replace("/gwc/service/wms", "/wfs")
    
    if "data.geopf.fr" in wms_url:
        return None
    
    if "/wms" in wms_url:
        return wms_url.replace("/wms", "/wfs")
    
    return None

@mcp.tools()
def get_features():
    if not context["layers"]:
        return "Aucun contexte chargé, appelle load_xml d'abord"
    
