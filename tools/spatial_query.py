from shared import mcp
import httpx


@mcp.tool()
def spatial_query(
    layers: list[str],
    wfs_urls: list[str],
    bbox: list[float],
    wfs_names: list[str] = None,
):
    """
    Interroge des couches WFS sur une emprise rectangulaire.
    À appeler en bout de chaîne, après get_metadata sur chaque couche.

    PARAMS :
    - layers    : liste de layer_id (PAS de wfs_name brut).
    - wfs_urls  : liste d'URLs WFS, une par couche (même ordre que layers).
                  Utiliser wfs_url issu de get_metadata.
    - wfs_names : liste de typenames WFS, une par couche (même ordre que layers).
                  Utiliser wfs_name issu de get_metadata. Si absent, utilise le layer_id.
    - bbox      : [lon_min, lat_min, lon_max, lat_max] EPSG:4326 — OBLIGATOIRE.
                  Issue de get_bbox ou fournie par l'utilisateur.

    LIMITES : 50 features max par couche, timeout 30s. Si total_matched
    > count, signaler la troncature à l'utilisateur.

    RETOUR : {layer_id: {count, total_matched, features:[{id, properties}]}}.
    En cas d'erreur sur une couche : {"error": "..."} sans interrompre
    les autres.
    """
    bbox_txt = ",".join(str(n) for n in bbox) + ",EPSG:4326"

    results = {}

    for i, layer in enumerate(layers):
        if i >= len(wfs_urls) or not wfs_urls[i]:
            results[layer] = {"error": "wfs_url manquante pour cette couche"}
            continue

        lien_wfs = wfs_urls[i]
        typename = (wfs_names[i] if wfs_names and i < len(wfs_names) and wfs_names[i] else None) or layer

        params = {
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAMES": typename,
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
                        "properties": {k: v for k, v in f.get("properties", {}).items() if v is not None},
                    }
                    for f in features
                ],
            }
        except httpx.TimeoutException:
            results[layer] = {"error": "timeout"}
        except httpx.RequestError as e:
            results[layer] = {"error": f"requete: {e}"}
        except ValueError:
            results[layer] = {"error": "reponse non-JSON"}

    return results
