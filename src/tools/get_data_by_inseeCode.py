from pyproj import Transformer
import requests
from shapely.geometry import shape
from shapely.ops import transform
from shared import mcp, context


transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)

@mcp.tool()
def get_data_by_inseeCode (code_insee: str):
    """
    Outil indispensable pour récupérer les dossiers d'évaluation environnementale ('cas par cas') d'une commune en Bretagne.
    
    QUAND UTILISER CET OUTIL :
    - Dès que l'utilisateur pose une question sur des projets d'aménagement, d'urbanisme, d'infrastructures ou des études d'impact environnemental (ex: parcs éoliens, lotissements, routes, zones industrielles).
    - Uniquement lorsque la demande concerne une commune située dans la région Bretagne (départements 22, 29, 35, 56).
    
    RÈGLES D'UTILISATION (IMPORTANT) :
    - Le paramètre attendu est le code INSEE, qui est STRICTEMENT DIFFÉRENT du code postal.
    - Si l'utilisateur fournit un nom de ville ou un code postal, tu dois impérativement trouver par toi-même son code INSEE officiel à 5 chiffres avant d'appeler cet outil.
    
    :param code_insee: (string) Une chaîne de 5 caractères correspondant au code géographique officiel (INSEE) de la commune (ex: "35024" pour Betton, "35238" pour Rennes). NE JAMAIS UTILISER DE CODE POSTAL.
    :return: Un objet JSON (FeatureCollection) contenant la liste des projets environnementaux et leurs emprises géographiques, strictement délimités aux frontières de la commune.
    """

    if not context["layers"]:
        return "Appele d'abord l'outil load_xml"

    api_url = f"https://geo.api.gouv.fr/communes/{code_insee}?format=geojson&geometry=contour"
    res = requests.get(api_url)
    res.raise_for_status()
    geojson = res.json()

    geom_wgs84 = shape(geojson['geometry']) #converti l'objet en Shapely et enlève l'entête

    geom_2154 = transform(transformer.transform, geom_wgs84)
    wkt_geometry = geom_2154.wkt


    wfs_url = "https://geobretagne.fr/geoserver/dreal_b/wfs"
    
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": "dreal_b:ae_casparcas",
        "outputFormat": "application/json",
        "srsName": "EPSG:2154",
        "cql_filter": f"INTERSECTS(the_geom, {wkt_geometry})"
    }

    reponse_wfs = requests.post(wfs_url, data=params)
    
    reponse_wfs.raise_for_status()

    return reponse_wfs.json()





