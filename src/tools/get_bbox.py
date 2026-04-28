from shared import mcp
import httpx, math

@mcp.tool()
def get_bbox(commune: str, tampon_km: float = 2.0):
    data = httpx.get(f"https://geo.api.gouv.fr/communes?nom={commune}&fields=nom,centre&format=json&geometry=contour")
    lon, lat = data.json()[0]["centre"]["coordinates"]


    delta_lat = tampon_km / 111.0
    delta_lon = tampon_km / (111.0 * math.cos(math.radians(lat)))
    
    return [
        lon - delta_lon,
        lat - delta_lat,
        lon + delta_lon,
        lat + delta_lat,
    ]