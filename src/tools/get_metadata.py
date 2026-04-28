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
    Récupère les métadonnées descriptives d'une couche via son service
    CSW et enrichit le contexte avec son URL WFS pour permettre les
    requêtes spatiales ultérieures.

    QUAND UTILISER :
    - OBLIGATOIRE avant tout spatial_query sur une couche : c'est
      cette étape qui résout l'URL WFS et la stocke dans le contexte.
    - Quand l'utilisateur demande des informations sur une couche
      ("c'est quoi cette donnée", "qui la produit", "à quelle date").

    QUAND NE PAS UTILISER :
    - Sur un layer_id qui n'a pas été retourné par list_layers_by_theme
      ou list_all_layers : NE JAMAIS inventer ni deviner un id.

    PARAMÈTRE :
    - layer_id : id exact de la couche, tel que retourné par les tools
      de listing (champ "id"). Sensible à la casse.

    PRÉCONDITION : load_xml doit avoir été appelé et la couche doit
    exister dans le contexte.

    EFFET DE BORD : enrichit context["layers"] avec wfs_url, wfs_name
    et obsolete pour la couche concernée. spatial_query utilisera
    ensuite ces champs automatiquement.

    RETOUR : dict avec
    - title : titre lisible de la couche
    - abstract : description (tronquée à 1000 caractères)
    - date : date de publication des métadonnées
    - wfs_url : URL de base du service WFS
    - wfs_name : identifiant qualifié de la couche WFS (ex: "dreal_b:l_plui")
    - obsolete : True si la couche est marquée comme obsolète. Dans ce
      cas, l'agent DOIT prévenir l'utilisateur avant de l'utiliser et
      proposer de chercher une alternative à jour.
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