from shared import mcp, context
import httpx
import xmltodict
from urllib.parse import urlparse, parse_qs


def _to_list(val):
    """Normalise None/dict/list en liste."""
    if val is None:
        return []
    if isinstance(val, dict):
        return [val]
    return val


def _extract_uri(uris, protocol):
    """Cherche une URI par protocole (WFS, WMS, ...). Retourne (url, name) ou (None, None).

    Gère deux cas fréquents dans les CSW de geobretagne.fr et autres :
    1. @protocol renseigné exactement (ex: "OGC:WFS")
    2. @protocol vide mais URL se terminant par /wfs ou contenant SERVICE=WFS
    """
    # Cas 1 : correspondance exacte sur le protocole
    for uri in uris:
        if uri.get("@protocol") == protocol:
            url = uri.get("#text")
            if url and "?" in url:
                url = url.split("?")[0]
            return url, uri.get("@name")

    # Cas 2 (fallback WFS) : protocole absent mais URL identifiable
    if protocol == "OGC:WFS":
        # URL de endpoint WFS direct (ex: .../wfs sans paramètres)
        for uri in uris:
            url = (uri.get("#text") or "").rstrip("/")
            if url.lower().endswith("/wfs"):
                return url, uri.get("@name")
        # URL avec SERVICE=WFS dans la query string (ex: GetFeature avec typename=...)
        for uri in uris:
            url = uri.get("#text") or ""
            if "SERVICE=WFS" in url.upper():
                base_url = url.split("?")[0]
                name = uri.get("@name") or ""
                # Si @name n'est pas un TypeName valide, l'extraire de la query string
                if ":" not in name and "TYPENAME" not in name.upper():
                    qs = parse_qs(urlparse(url).query, keep_blank_values=False)
                    for key in ("TYPENAME", "TYPENAMES", "typename", "typenames"):
                        if key in qs:
                            name = qs[key][0]
                            break
                return base_url, name or None

    return None, None


@mcp.tool()
def get_metadata(layer_id: str):
    """
    Récupère les métadonnées CSW d'une couche et résout son URL WFS dans
    le contexte. OBLIGATOIRE avant tout spatial_query.

    PARAM layer_id : id exact issu de list_layers_by_theme/list_all_layers.
    Ne jamais inventer.

    RETOUR : title, abstract, date, wfs_url, wfs_name, obsolete (bool).
    Si wfs_url=null : la couche n'a pas de service WFS, spatial_query impossible.
    Si obsolete=True : avertir l'utilisateur avant utilisation.
    """
    if not context['layers']:
        return "Contexte vide, exécuter load_xml avant"

    layer = next((l for l in context['layers'] if l['id'] == layer_id), None)
    if layer is None:
        return f"Aucune couche trouvée avec l'id '{layer_id}'"

    csw_url = layer['metadata-csw']

    try:
        response = httpx.get(csw_url, timeout=30)
        response.raise_for_status()
        data = xmltodict.parse(response.text)
    except httpx.TimeoutException:
        layer['wfs_url'] = None
        return {"layer_id": layer_id, "error": "Serveur CSW inaccessible (timeout)", "wfs_url": None}
    except httpx.HTTPStatusError as e:
        layer['wfs_url'] = None
        return {"layer_id": layer_id, "error": f"Erreur HTTP CSW: {e.response.status_code}", "wfs_url": None}
    except httpx.RequestError as e:
        layer['wfs_url'] = None
        return {"layer_id": layer_id, "error": f"Erreur réseau CSW: {e}", "wfs_url": None}
    except Exception as e:
        layer['wfs_url'] = None
        return {"layer_id": layer_id, "error": f"XML CSW invalide: {e}", "wfs_url": None}

    # Supporte le format Dublin Core (csw:Record) et ISO 19115 (gmd:MD_Metadata)
    resp = data.get('csw:GetRecordByIdResponse', {})
    record = resp.get('csw:Record')
    if record is None:
        layer['wfs_url'] = None
        return {"layer_id": layer_id, "error": "Format CSW non supporté (pas de csw:Record)", "wfs_url": None}

    uris = _to_list(record.get('dc:URI'))
    wfs_url, wfs_name = _extract_uri(uris, "OGC:WFS")

    title = record.get('dc:title', '')
    abstract = record.get('dct:abstract', '')

    obsolete = (
        'OBSOLETE' in title.upper()
        or 'SERA SUPPRIME' in abstract.upper()
        or 'SERA SUPPRIMÉ' in abstract.upper()
    )

    layer['wfs_url'] = wfs_url
    layer['wfs_name'] = wfs_name
    layer['obsolete'] = obsolete

    return {
        "layer_id": layer_id,
        "title": title,
        "abstract": abstract[:1000] + ("..." if len(abstract) > 1000 else ""),
        "date": record.get('dc:date'),
        "wfs_url": wfs_url,
        "wfs_name": wfs_name,
        "obsolete": obsolete,
    }