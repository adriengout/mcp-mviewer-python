# mcp-mviewer-python

Serveur [MCP (Model Context Protocol)](https://modelcontextprotocol.io) qui expose les configurations [mviewer](https://mviewer.netlify.app) à un agent IA. Il permet d'explorer les données géographiques, de résoudre leurs métadonnées et d'interroger les données spatiales via WFS, en langage naturel.

## Fonctionnement

```
Agent IA
   │
   ▼ MCP (streamable-http)
mcp-mviewer-python
   ├── Charge le config.xml mviewer
   ├── Indexe thèmes et données
   ├── Résout les métadonnées CSW
   └── Exécute des requêtes WFS
         │
         ├── Services WFS (données géographiques)
         ├── Services CSW (métadonnées)
         └── geo.api.gouv.fr (géocodage communes)
```

## Outils MCP exposés

| Outil | Description |
|---|---|
| `check_mviewer` | Valide qu'une URL pointe bien vers un config.xml mviewer avant de le charger |
| `load_xml` | Charge un config.xml et indexe ses données et thèmes en mémoire |
| `list_themes` | Liste les thèmes disponibles dans la config chargée |
| `list_layers_by_theme` | Liste les données d'un thème donné |
| `list_all_layers` | Liste toutes les données, tous thèmes confondus |
| `get_metadata` | Récupère les métadonnées CSW d'une donnée et résout son URL WFS |
| `get_bbox` | Calcule une emprise rectangulaire autour d'une commune française |
| `spatial_analysis` | Scanne toutes les couches du contexte sur une bbox et retourne les `layer_id` ayant des données dans la zone |
| `spatial_query` | Interroge une ou plusieurs données WFS sur une emprise géographique |
| `bbox_to_mviewer_url` | Génère un lien mviewer permalink à partir de données et d'une config xml |

### Enchaînement typique

```
check_mviewer(url)
  → load_xml(url)
    → list_themes()
      → list_layers_by_theme(theme)
        → get_bbox(commune)             ← optionnel, si zone nommée
          → spatial_analysis(bbox)      ← identifie les couches pertinentes
            → get_metadata(layer_id)    ← obligatoire avant spatial_query
              → spatial_query(layers, bbox)
                → bbox_to_mviewer_url(bbox, layers)
```

## Installation

### Prérequis

- Python 3.12+

### Local

```bash
pip install -r requirements.txt
python main.py
```

### Docker

```bash
docker compose up --build
```

## Configuration

| Variable | Obligatoire | Description |
|---|---|---|
| `DEFAULT_CONFIG_URL` | Non | URL de la config mviewer chargée au démarrage. Sans elle, le serveur démarre sans contexte. |

Copier `.env.example` en `.env` et ajuster si besoin.

## Endpoints

| URL | Description |
|---|---|
| `http://localhost:8000/mcp/mviewer` | Endpoint MCP (streamable-http) |
| `http://localhost:8000/mcp/mviewer/playground` | Interface web de test interactif |

## Dépendances

| Package | Rôle |
|---|---|
| `mcp[cli]` | Framework MCP (FastMCP) |
| `httpx` | Requêtes HTTP async (WFS, CSW, geo.api.gouv.fr) |
| `xmltodict` | Parsing des configs XML mviewer |

## Structure

```
mcp-mviewer-python/
├── main.py                    # Point d'entrée du serveur
├── shared.py                  # Config globale et contexte en mémoire
├── playground.py              # Interface web de test
├── tools/
│   ├── mviewer_check.py       # Validation d'une URL config.xml (expose `check_mviewer`)
│   ├── load_xml.py
│   ├── list_themes.py
│   ├── list_layers_by_theme.py
│   ├── list_all_layers.py
│   ├── get_metadata.py
│   ├── get_bbox.py
│   ├── spatial_analysis.py
│   ├── spatial_query.py
│   └── bbox_to_mviewer_url.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Limites

- Le contexte (config chargée) est **en mémoire** : il est réinitialisé au redémarrage et partagé entre toutes les sessions simultanées.
- `spatial_query` retourne **50 entités maximum** par donnée, avec un timeout de 30 secondes.
- `spatial_analysis` interroge toutes les couches en parallèle (15 max simultanés) avec un timeout de 15 secondes par couche.
- `get_bbox` utilise **geo.api.gouv.fr** et ne couvre que les communes françaises.
