from shared import mcp
import httpx, math


@mcp.tool()
def get_bbox(commune: str, tampon_km: float = 2.0):
    """
    Calcule une bbox carrée centrée sur une commune française via
    geo.api.gouv.fr. À utiliser avant spatial_query quand l'utilisateur
    désigne une zone par un nom de commune.

    PARAMS :
    - commune : nom (sensible aux accents)
    - tampon_km : demi-côté en km, défaut 2.0 (= bbox de 4 km de côté).
      Ajuster selon l'échelle souhaitée (1-2 km centre-ville, 5-10 km
      agglo).

    RETOUR : [lon_min, lat_min, lon_max, lat_max] EPSG:4326, ou dict
    d'erreur si commune introuvable.
    """

    
    data = httpx.get(
        f"https://geo.api.gouv.fr/communes?nom={commune}&fields=nom,centre&format=json"
    )
    data.raise_for_status()
    results = data.json()
    if not results:
        return {"error": f"Commune '{commune}' non trouvée"}
    
    lon, lat = results[0]["centre"]["coordinates"]
    
    delta_lat = tampon_km / 111.0
    delta_lon = tampon_km / (111.0 * math.cos(math.radians(lat)))
    
    return [
        lon - delta_lon,
        lat - delta_lat,
        lon + delta_lon,
        lat + delta_lat,
    ]