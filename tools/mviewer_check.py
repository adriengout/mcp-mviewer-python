from shared import mcp
import httpx
import xmltodict


def _to_list(val):
    if val is None:
        return []
    if isinstance(val, dict):
        return [val]
    return val


@mcp.tool()
def check_mviewer(url: str) -> dict:
    """
    Vérifie qu'une URL pointe vers une configuration mviewer valide.
    À appeler AVANT load_xml pour valider une URL fournie par l'utilisateur.

    Critères bloquants :
    - URL accessible et XML parsable
    - Racine <config>
    - Présence de <application> et <themes>
    - Au moins une couche définie

    PARAM url : URL du config.xml.

    RETOUR : {valid, errors, warnings, summary}.
    Si valid=True → load_xml peut être appelé en confiance.
    """
    errors = []
    warnings = []

    # 1. Téléchargement
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as e:
        return {
            "valid": False,
            "errors": [f"Téléchargement échoué : {e}"],
            "warnings": [],
            "summary": None,
        }

    # Indice secondaire : content-type
    ct = response.headers.get("content-type", "").lower()
    if "xml" not in ct:
        warnings.append(f"Content-Type inhabituel : '{ct}' (attendu : xml)")

    # 2. Parsing XML
    try:
        data = xmltodict.parse(response.text)
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"XML invalide : {e}"],
            "warnings": warnings,
            "summary": None,
        }

    # 3. Racine doit être <config>
    root_tag = next(iter(data.keys()), None)
    if root_tag != "config":
        return {
            "valid": False,
            "errors": [f"Racine attendue <config>, trouvée <{root_tag}>"],
            "warnings": warnings,
            "summary": None,
        }

    config = data["config"]
    if not isinstance(config, dict):
        return {
            "valid": False,
            "errors": ["Élément <config> mal formé"],
            "warnings": warnings,
            "summary": None,
        }

    # 4. Enfants requis
    if "application" not in config:
        errors.append("Élément <application> manquant")
    if "themes" not in config:
        errors.append("Élément <themes> manquant")

    # Enfants recommandés (warnings seulement)
    for child in ("mapoptions", "baselayers"):
        if child not in config:
            warnings.append(f"<{child}> absent (recommandé)")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "summary": None}

    # 5. Au moins un thème
    themes_node = config.get("themes")
    if not isinstance(themes_node, dict) or "theme" not in themes_node:
        return {
            "valid": False,
            "errors": ["<themes> ne contient aucun <theme>"],
            "warnings": warnings,
            "summary": None,
        }

    themes = _to_list(themes_node["theme"])

    # 6. Compter les couches valides
    layers_count = 0
    themes_without_layers = []
    layers_without_id = 0

    for t in themes:
        if not isinstance(t, dict):
            continue
        theme_layers = []
        for group in _to_list(t.get("group")):
            if isinstance(group, dict):
                theme_layers.extend(_to_list(group.get("layer")))
        theme_layers.extend(_to_list(t.get("layer")))

        # Filtrer les éléments mal formés
        valid_layers = [l for l in theme_layers if isinstance(l, dict)]
        layers_without_id += sum(1 for l in valid_layers if not l.get("@id"))

        layers_count += len(valid_layers)
        if not valid_layers:
            themes_without_layers.append(t.get("@name", "(sans nom)"))

    if layers_count == 0:
        return {
            "valid": False,
            "errors": ["Aucune couche détectée dans les thèmes"],
            "warnings": warnings,
            "summary": None,
        }

    if themes_without_layers:
        warnings.append(f"Thèmes sans couches : {', '.join(themes_without_layers)}")
    if layers_without_id:
        warnings.append(f"{layers_without_id} couche(s) sans attribut @id")

    # 7. Résumé
    app = config.get("application", {})
    title = app.get("@title") if isinstance(app, dict) else None

    return {
        "valid": True,
        "errors": [],
        "warnings": warnings,
        "summary": {
            "title": title,
            "themes_count": len(themes),
            "layers_count": layers_count,
        },
    }