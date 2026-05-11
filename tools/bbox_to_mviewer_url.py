from shared import mcp
import math
from urllib.parse import quote


@mcp.tool()
def bbox_to_mviewer_url(
    bbox: list[float],
    layers: list[str],
    config: str = "https://geobretagne.fr/apps/viz/config.xml",
    mode: str = "d",
) -> str:
    """
    Convertit une bbox EPSG:4326 et une liste de layer_id en URL MViewer
    permalink prête à partager.

    Calcule le centre de la carte en EPSG:3857 et estime le niveau de zoom
    adapté à l'emprise. À appeler après spatial_query pour proposer un lien
    de visualisation.

    PARAMS :
    - bbox    : [lon_min, lat_min, lon_max, lat_max] EPSG:4326
                (retourné par get_bbox ou fourni par l'utilisateur via la carte)
    - layers  : liste de layer_id exacts issus de list_layers_by_theme ou
                list_all_layers. Format avancé : "layerid*style*filtreCQL"
    - config  : URL du config.xml MViewer
                (défaut : https://geobretagne.fr/apps/viz/config.xml)
    - mode    : "d" défaut · "s" simplifié · "u" ultra-simplifié  (défaut : "d")

    RETOUR : URL MViewer complète, encodée, prête à partager.
    """
    lon_min, lat_min, lon_max, lat_max = bbox

    center_lon = (lon_min + lon_max) / 2
    center_lat = (lat_min + lat_max) / 2

    # EPSG:4326 → EPSG:3857
    x = center_lon * 20037508.34 / 180
    y = math.log(math.tan((90 + center_lat) * math.pi / 360)) * 20037508.34 / math.pi

    config_encoded = quote(config, safe="")
    l_param = ",".join(layers)

    return (
        f"https://geobretagne.fr/mviewer/"
        f"?config={config_encoded}"
        f"&l={l_param}"
        f"&x={round(x)}"
        f"&y={round(y)}"
        f"&z=13"
        f"&mode={mode}"
    )
