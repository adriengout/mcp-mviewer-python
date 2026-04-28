from shared import mcp, context
import httpx


@mcp.tool()
def spatial_query(layers: list[str], bbox: list[float] = None):
    """
    Interroge des couches WFS sur une emprise rectangulaire.
    À appeler en bout de chaîne, après get_metadata sur chaque couche.

    PARAMS :
    - bbox : [lon_min, lat_min, lon_max, lat_max] EPSG:4326
      (issue de get_bbox ou fournie par l'utilisateur).
    - layers : liste de layer_id (PAS de wfs_name brut).

    LIMITES : 50 features max par couche, timeout 30s. Si total_matched
    > count, signaler la troncature à l'utilisateur.

    RETOUR : {layer_id: {count, total_matched, features:[{id, properties}]}}.
    En cas d'erreur sur une couche : {"error": "..."} sans interrompre
    les autres.
    """

    if bbox:
        bbox_txt = ",".join(str(n) for n in bbox) + ",EPSG:4326"
    
    results = {}
    

    for layer in layers:

        layer_info = next((l for l in context["layers"] if l["id"] == layer), None)
        if layer_info is None or not layer_info.get("wfs_url"):
            results[layer] = {"error": "wfs_url non disponible, appeler get_metadata d'abord"}
            continue
        lien_wfs = layer_info["wfs_url"]

        params = {
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAMES": layer,
            "outputFormat": "application/json",
            "COUNT": 50,
            "BBOX": bbox_txt,
        }
        
        try:
            response = httpx.get(lien_wfs, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            features = data.get("features", [])
            
            results[layer] = {
                "count": len(features),
                "total_matched": data.get("totalFeatures") or data.get("numberMatched"),
                "features": [
                    {
                        "id": f.get("id"),
                        "properties": f.get("properties", {}),
                    }
                    for f in features
                ],
            }
        except httpx.TimeoutException as e:
            results[layer] = {"error": "timeout"}
        except httpx.RequestError as e:
            results[layer] = {"error": f"requete: {e}"}
        except ValueError:
            results[layer] = {"error": "reponse non-JSON"}
    
    return results