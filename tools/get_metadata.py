from shared import mcp, context
import httpx
import xmltodict


def _to_list(val):
    """Normalise None/dict/list en liste."""
    if val is None:
        return []
    if isinstance(val, dict):
        return [val]
    return val


def _extract_uri(uris, protocol):
    """Cherche une URI par protocole (WFS, WMS, ...). Retourne (url, name) ou (None, None)."""
    for uri in uris:
        if uri.get("@protocol") == protocol:
            url = uri.get("#text")
            if url and "?" in url:
                url = url.split("?")[0]
            return url, uri.get("@name")
    return None, None


@mcp.tool()
def get_metadata(layer_id: str):
    """
    Récupère les métadonnées CSW d'une couche et résout son URL WFS dans
    le contexte. OBLIGATOIRE avant tout spatial_query.

    PARAM layer_id : id exact issu de list_layers_by_theme/list_all_layers.
    Ne jamais inventer.

    RETOUR : title, abstract, date, wfs_url, wfs_name, obsolete (bool).
    Si obsolete=True : avertir l'utilisateur avant utilisation.
    """
    if not context['layers']:
        return "Contexte vide, exécuter load_xml avant"

    layer = next((l for l in context['layers'] if l['id'] == layer_id), None)
    if layer is None:
        return f"Aucune couche trouvée avec l'id '{layer_id}'"

    url = layer['metadata-csw']
    
    response = httpx.get(url, timeout=30)
    response.raise_for_status()


    data = xmltodict.parse(response.text)
    record = data['csw:GetRecordByIdResponse']['csw:Record']

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