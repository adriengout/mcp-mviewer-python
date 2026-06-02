from shared import mcp
import httpx
import xml.etree.ElementTree as ET

_XSD_NS = "{http://www.w3.org/2001/XMLSchema}"
_GEOM_KEYWORDS = (
    "geometry", "polygon", "point", "linestring", "surface",
    "curve", "ring", "multipolygon", "multipoint", "multilinestring",
    "multisurface", "multicurve",
)


def _get_geometry_fields(wfs_url: str, typename: str) -> set:
    """Retourne les noms de champs géométriques via DescribeFeatureType."""
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "DescribeFeatureType",
        "TYPENAMES": typename,
    }
    try:
        response = httpx.get(wfs_url, params=params, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.text)
    except Exception:
        return set()

    geom_fields = set()
    for elem in root.iter(f"{_XSD_NS}element"):
        field_type = elem.get("type", "")
        field_name = elem.get("name", "")
        if not field_name or not field_type.startswith("gml:"):
            continue
        local = field_type[4:].lower()
        if any(kw in local for kw in _GEOM_KEYWORDS):
            geom_fields.add(field_name)

    return geom_fields


_COMPACT_PATTERNS = (
    "nom", "name", "libelle", "titre", "title",
    "id", "code", "type", "categorie", "category",
    "surface", "area", "statut", "status", "description",
    "commune", "site", "zone", "label", "ref",
)


def _is_compact_field(key: str) -> bool:
    k = key.lower()
    return any(p in k for p in _COMPACT_PATTERNS)


def _filter_properties(props: dict, geom_fields: set, compact: bool) -> dict:
    result = {k: v for k, v in props.items()
              if v is not None and v != "" and k not in geom_fields}
    if not compact:
        return result
    filtered = {k: v for k, v in result.items() if _is_compact_field(k)}
    return filtered if filtered else result


_MAX_FEATURES = 20


@mcp.tool()
def spatial_query(
    layers: list[str],
    wfs_urls: list[str],
    bbox: list[float],
    wfs_names: list[str] = None,
    compact: bool = True,
):
    """Requête WFS sur une bbox. Retourne {layer_id: {count, total_matched, features}}.
    compact=True (défaut) : garde uniquement les champs identifiants (nom, code, type, statut…) en excluant les valeurs vides."""
    bbox_txt = ",".join(str(n) for n in bbox) + ",EPSG:4326"
    count = _MAX_FEATURES

    results = {}

    for i, layer in enumerate(layers):
        if i >= len(wfs_urls) or not wfs_urls[i]:
            results[layer] = {"error": "wfs_url manquante pour cette donnée"}
            continue

        lien_wfs = wfs_urls[i]
        typename = (wfs_names[i] if wfs_names and i < len(wfs_names) and wfs_names[i] else None) or layer

        geom_fields = _get_geometry_fields(lien_wfs, typename)

        params = {
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAMES": typename,
            "outputFormat": "application/json",
            "COUNT": count,
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
                    _filter_properties(f.get("properties", {}), geom_fields, compact)
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
