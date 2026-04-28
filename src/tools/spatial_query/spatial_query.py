from shared import mcp, context
import httpx


@mcp.tool()
def spatial_query(layers: list[str], bbox: list[float] = None):
    """
    Interroge une ou plusieurs couches WFS sur une emprise rectangulaire
    et retourne les entités géographiques (features) trouvées dans cette
    zone.

    QUAND UTILISER :
    - Pour répondre à une question spatiale : "qu'y a-t-il à [zone]",
      "y a-t-il des [type] près de [lieu]", "quelles données concernent
      cette commune".
    - Toujours en bout de chaîne, après que les couches aient été
      identifiées (list_*) et que get_metadata ait été appelé sur
      chacune pour résoudre leur URL WFS.

    QUAND NE PAS UTILISER :
    - Pour explorer ce qui est disponible (utiliser les tools list_*).
    - Pour obtenir une description d'une couche (utiliser get_metadata).
    - Sans avoir d'abord appelé get_metadata sur les couches concernées :
      le tool retournera une erreur "wfs_url non disponible".
    - Avec une bbox inventée : toujours partir d'une référence géographique
      identifiée (commune, coordonnées explicites de l'utilisateur).

    PARAMÈTRES :
    - bbox : [lon_min, lat_min, lon_max, lat_max] en degrés décimaux
      EPSG:4326. Exemple Lannion centre :
      [-3.485, 48.720, -3.440, 48.745].
    - layers : liste de layer_id (PAS de wfs_name) tels que retournés
      par list_layers_by_theme. Plusieurs couches peuvent être
      interrogées en un seul appel ; elles sont regroupées par service.

    LIMITES :
    - Maximum 50 features par couche (paramètre COUNT côté serveur).
    - Timeout 30 secondes par couche.
    - Si total_matched > count, signaler explicitement à l'utilisateur
      que les résultats sont tronqués et proposer d'affiner la zone.

    RETOUR : dict {layer_id: {count, total_matched, features:[{id, properties}]}}.
    En cas d'erreur sur une couche, son entrée contient {"error": "..."}
    sans interrompre les autres couches.
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