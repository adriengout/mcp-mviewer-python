---
name: spatial_query
description: |
  Workflow d'interrogation spatiale de données géographiques. À charger
  dès que l'utilisateur veut savoir "ce qu'il y a à un endroit", "obtenir
  des informations sur une zone", "interroger une ou plusieurs couches
  sur un secteur". Couvre les 4 cas : 1 couche + zone, N couches + zone,
  zone seule, couche seule.
---

# Skill : Interrogation spatiale

Cette skill structure le workflow pour répondre aux demandes d'information
géographique sur une zone donnée. Quatre cas d'usage sont prévus selon
ce que l'utilisateur fournit.

## Identification du cas

Avant toute action, classifier la demande de l'utilisateur dans l'un des
quatre cas suivants :

| Cas | Couche(s) fournie(s) | Zone fournie | Action principale       |
|-----|----------------------|--------------|-------------------------|
|  A  | Une                  | Oui          | Interrogation directe   |
|  B  | Plusieurs            | Oui          | Interrogation multi     |
|  C  | Aucune               | Oui          | Synthèse exploratoire   |
|  D  | Une (ou plusieurs)   | Non          | Demander la localisation|

Si la classification est ambiguë, poser une question avant d'agir.

---

## Cas A — Une couche, une zone

Exemple type : *"montre-moi les PLUi dans la baie de Lannion"*

### Procédure

1. Vérifier que `context["layers"]` existe (sinon : `load_xml` requis).
2. Identifier la couche dans le contexte. Si l'utilisateur l'a nommée
   approximativement, la résoudre via `list_all_layers` ou
   `list_layers_by_theme`. NE PAS inventer un layer_id.
3. Appeler `get_metadata(layer_id)` pour résoudre l'URL WFS et lire
   l'abstract.
4. Si `obsolete == True` : avertir l'utilisateur, proposer de chercher
   une alternative, mais ne pas bloquer s'il insiste.
5. Construire la bbox au format `[lon_min, lat_min, lon_max, lat_max]`
   en EPSG:4326 (voir section "Construction de bbox").
6. Appeler `spatial_query(bbox, [layer_id])`.
7. Synthétiser la réponse selon "Format de restitution".

---

## Cas B — Plusieurs couches, une zone

Exemple type : *"compare les PLU et les zones humides autour de Trégastel"*

### Procédure

1. Identifier toutes les couches mentionnées (idem cas A étape 2).
2. Appeler `get_metadata` sur CHAQUE layer_id, séquentiellement.
   Mémoriser les couches obsolètes pour les signaler en bloc à la fin.
3. Construire la bbox unique (toutes les couches partageront la même).
4. Appeler `spatial_query(bbox, [layer_id_1, layer_id_2, ...])` en un
   seul appel : le tool regroupe automatiquement par service WFS.
5. Restituer couche par couche, puis ajouter une synthèse croisée si
   pertinent (intersections, complémentarités, contradictions
   éventuelles).

---

## Cas C — Zone seule, sans couche précisée

Exemple type : *"qu'est-ce qu'il y a d'intéressant à Lannion ?"*
ou *"donne-moi les infos importantes sur cette zone : [bbox]"*

C'est le cas le plus exigeant. L'utilisateur attend une **synthèse
informative**, pas un dump exhaustif.

### Procédure

1. Si aucun thème n'a encore été présenté à l'utilisateur dans la
   conversation : appeler `list_themes` pour avoir la vue d'ensemble.
2. Sélectionner les thèmes pertinents pour une "fiche de zone"
   généraliste. Par défaut, viser les thèmes qui apportent de
   l'information actionnable :
   - Limites administratives / découpages
   - Urbanisme et planification
   - Risques (naturels, technologiques)
   - Environnement et patrimoine naturel
   - Équipements et services
3. Pour chaque thème retenu, appeler `list_layers_by_theme` et
   sélectionner **1 à 3 couches phares** par thème (privilégier les
   couches non-obsolètes, aux titres explicites). NE PAS interroger
   toutes les couches : viser 5 à 10 couches au total maximum.
4. Appeler `get_metadata` sur chaque couche retenue.
5. Construire un appel `spatial_query` unique avec la liste complète
   des layer_id et la bbox fournie.
6. Synthétiser les résultats par grands thèmes (voir "Synthèse de
   zone" ci-dessous).

### Critères de sélection des couches "importantes"

Une couche est considérée comme apportant de l'information importante
sur une zone si :
- Son `obsolete` est `False`.
- Son `abstract` indique qu'elle couvre l'emprise géographique de la
  bbox demandée.
- Son titre est compréhensible par un non-spécialiste.

Si l'utilisateur n'a pas explicitement demandé l'exhaustivité, **moins
est plus** : 5 couches bien choisies valent mieux que 20 verbeuses.

---

## Cas D — Une couche, sans zone

Exemple type : *"montre-moi les zones humides"*

### Procédure

1. Identifier la couche (cas A étape 2). Si la couche est valide,
   appeler `get_metadata` pour avoir le titre et l'abstract — utile
   pour formuler une question pertinente.
2. NE PAS interroger sans bbox : un WFS sans BBOX retournerait
   potentiellement des milliers d'entités. Toujours demander une
   localisation.
3. Demander une zone à l'utilisateur, en proposant des options :

   > "Quelle zone veux-tu interroger ? Tu peux me donner :
   > - une commune ou un lieu-dit (j'estimerai l'emprise)
   > - des coordonnées (lon/lat) d'un point + un rayon
   > - une bbox directement [lon_min, lat_min, lon_max, lat_max]"

4. Si la couche en question a une emprise restreinte connue (mentionnée
   dans son abstract ou ses métadonnées), le signaler :
   "Cette couche couvre la Bretagne, la zone que tu choisis devrait
   être dans cette région."
5. Une fois la zone obtenue, basculer dans le cas A.

---

## Construction de bbox

Quand l'utilisateur donne un nom de lieu, ne pas inventer de bbox au
hasard. Procéder ainsi :

- Si l'utilisateur fournit des coordonnées : les utiliser directement.
- Si l'utilisateur donne une commune : utiliser une bbox conservatrice
  centrée sur le centre-ville (mairie), suffisamment petite pour ne pas
  déborder sur les communes voisines (typiquement 2 à 4 km de côté pour
  une commune moyenne).
- Toujours signaler à l'utilisateur l'emprise utilisée :
  "J'utilise une emprise d'environ 3 km autour du centre de [commune].
  Dis-moi si tu veux élargir ou si tu as des coordonnées plus précises."
- Format strict : `[lon_min, lat_min, lon_max, lat_max]` en EPSG:4326,
  c'est-à-dire en degrés décimaux où la longitude est en premier.

### Bbox utiles à retenir (Bretagne)

- Lannion centre : `[-3.485, 48.720, -3.440, 48.745]`
- Si l'utilisateur demande une autre commune, raisonner par analogie
  mais signaler l'incertitude.

---

## Synthèse de zone (cas C)

Pour le cas C uniquement, structurer la restitution ainsi :

```
## Synthèse de [nom de zone ou bbox]

### Contexte administratif
[résultats des couches limites administratives]

### Urbanisme et aménagement
[résultats urbanisme : PLU, PLUi, zonages]

### Risques
[résultats risques naturels et technologiques]

### Environnement
[espaces naturels, zones protégées]

### Autres éléments notables
[équipements, patrimoine, etc.]

### Couches consultées
- [titre] (id: [layer_id])
- ...

### Couches obsolètes signalées
[liste si applicable, avec recommandation]
```

Adapter les sections selon ce qui a réellement été trouvé. Ne pas
afficher de section vide. Si une couche retourne 0 feature, l'indiquer
en note ("Aucun PLU recensé sur cette emprise") plutôt que de l'omettre,
car l'absence est elle-même une information.

---

## Format de restitution (cas A et B)

- Pour chaque couche : titre lisible, nombre d'entités trouvées,
  2-3 exemples représentatifs avec leurs propriétés les plus parlantes
  (nom, code, statut, date).
- Si `count == 50` et `total_matched > 50` : signaler la troncature
  ("J'ai 50 résultats sur [total_matched]. Veux-tu que je restreigne
  la zone ?").
- Si `count == 0` : ne pas inventer. Dire "aucune entité trouvée dans
  cette zone pour [titre couche]" et proposer d'élargir la bbox ou de
  vérifier qu'elle est bien placée.
- Citer les couches sources à la fin avec leur layer_id, pour
  traçabilité.

---

## Erreurs à éviter

- Inventer un layer_id parce qu'il "ressemble à" ce que l'utilisateur
  a demandé.
- Appeler `spatial_query` sans avoir fait `get_metadata` au préalable
  sur les couches concernées (le tool retournera une erreur
  "wfs_url non disponible").
- Construire une bbox au pifomètre sans le signaler à l'utilisateur.
- Présenter les résultats d'une couche `obsolete: True` comme s'ils
  étaient à jour.
- Sur le cas C, interroger 30 couches "pour faire complet" : viser
  la pertinence, pas l'exhaustivité.
- Présenter `count: 0` comme une absence définitive de données : c'est
  peut-être juste que la bbox est mal placée. Le suggérer.
- Confondre `layer_id` (utilisé par les tools internes) et `wfs_name`
  (identifiant qualifié WFS, ex: "dreal_b:l_plui"). `spatial_query`
  attend des `layer_id`, pas des `wfs_name`.