from mcp.server import *
from pyproj import Transformer
import xml.etree.ElementTree as ET
import requests
from shapely.geometry import shape
from shapely.ops import transform

mcp = FastMCP("mcpWFS")

transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)


@mcp.tool()
def charger_xml(url_xml: str):
    """Outil pour charger un xml dans la conversation, te permet d'avoir accès a du xml"""

    xml_data = requests.get(url_xml)
    xml_data.encoding = 'utf-8'
    xml_texte = xml_data.text
    root = ET.fromstring(xml_texte)

    noms_themes = {}

    for themes in root.iter("themes"):
        for theme in themes:
            nom_theme = theme.attrib.get('name', "ce thème n'a pas de nom")
            noms_themes[nom_theme] = 0
            for layer in theme:
                noms_themes[nom_theme] += 1

            
    
    return noms_themes
    


@mcp.tool()
def get_data_par_commune (code_insee: str):
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

    api_url = f"https://geo.api.gouv.fr/communes/{code_insee}?format=geojson&geometry=contour"
    res = requests.get(api_url)
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





if __name__ == "__main__":
    #print(charger_xml("https://geobretagne.fr/apps/viz/config.xml"))
    mcp.run()