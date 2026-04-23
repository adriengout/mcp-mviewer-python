from shared import mcp, context
import httpx


@mcp.tool
def get_metadata(layer_id: str):
    
    csw_url = layer.get()
    reponse = httpx.get()