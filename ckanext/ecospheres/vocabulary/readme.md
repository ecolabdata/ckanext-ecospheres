## Gestion des vocabulaires




## Exposition des vocabulaires



| Vocabulaire   |      Endpoint      |  Method  |Format   |
|----------|:-------------:|------:|------:|
| Territoires |  /api/territoires | GET |JSON |
| Territoires par hierarchie |  /api/territoires_hierarchy | GET |JSON |
| Thèmes |    /api/themes   |   GET |JSON |
| Organizations | /api/organizations |    GET |JSON |


<br>

### **/api/organizations**

```json
{
  "Directions d\u00e9partementales": [
    {
      "Courriel": "ddt@indre-et-loire.gouv.fr", 
      "Site internet": "https://www.indre-et-loire.gouv.fr/Services-de-l-Etat/Agriculture-environnement-amenagement-et-logement/Direction-departementale-des-territoires", 
      "Territoire": "{D37}", 
      "Type": "DD", 
      "T\u00e9l\u00e9phone": "02 47 70 80 90", 
      "created": "Thu, 08 Sep 2022 14:47:55 GMT", 
      "description": "## Direction d\u00e9partementale des territoires - Indre-et-Loire.\n\nService d\u00e9concentr\u00e9 de l'\u00c9tat d\u00e9pendant du minist\u00e8re de l'int\u00e9rieur et plac\u00e9 sous l'autorit\u00e9 du .....", 
      "image_url": "https://raw.githubusercontent.com/ecolabdata/guichetdonnees-public/main/organisations/logos/ddt-37261-01.jpg", 
      "name": "ddt-37261-01", 
      "title": "DDT 37"
    }
  ], 
  "Directions interr\u00e9gionales et interd\u00e9partementales": [
    {
      "Courriel": "dir-est@developpement-durable.gouv.fr", 
      "Site internet": "http://www.dir.est.developpement-durable.gouv.fr", 
      "Territoire": "{D25,D39,D51,D52,D54,D55,D57,D70,D88,D90}", 
      "Type": "DIRID", 
      "T\u00e9l\u00e9phone": "03 83 50 96 00", 
      "created": "Thu, 08 Sep 2022 15:22:44 GMT", 
      "description": "## Direction interd\u00e9partementale des routes - Est.\n\nLa DIR Est est le service d\u00e9concentr\u00e9....", 
      "image_url": "https://raw.githubusercontent.com/ecolabdata/guichetdonnees-public/main/organisations/logos/did_routes.png", 
      "name": "did_routes-54395-01", 
      "title": "DIR Est"
    }
    
  ], 
 
}
``` 
<br>

### **/api/themes**

```json
{
  "Am\u00e9nagement et urbanisme": {
    "altlabel": [
      "amenagement-urbanisme"
    ], 
    "child": [
      {
        "altlabel": [
          "amenagement_urbanisme/n_assiette_servitude"
        ], 
        "label": "Servitudes d'utilit\u00e9 publique", 
        "language": "fr", 
        "uri": "http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/servitudes-d-utilite-publique"
      }, 
      {
        "altlabel": [
          "Am\u00e9nagement Urbanisme/Zonages \u00c9tude"
        ], 
        "label": "\u00c9tudes", 
        "language": "fr", 
        "uri": "http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/etudes"
      }, 
      {
        "altlabel": [
          "ZONAGES PLANIFICATION"
        ], 
        "label": "Planification", 
        "language": "fr", 
        "uri": "http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/planification"
      }, 
      {
        "altlabel": [
          "Am\u00e9nagement Urbanisme/Politique europ\u00e9enne"
        ], 
        "label": "Politique europ\u00e9enne d'am\u00e9nagement", 
        "language": "fr", 
        "uri": "http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/politique-europeenne-d-amenagement"
      }, 
      {
        "altlabel": [
          "zonages-zonages-amenagement"
        ], 
        "label": "Zonages d'am\u00e9nagement", 
        "language": "fr", 
        "uri": "http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/zonages-d-amenagement"
      }
    ], 
    "label": "Am\u00e9nagement et urbanisme", 
    "language": "fr", 
    "uri": "http://registre.data.developpement-durable.gouv.fr/ecospheres/themes-ecospheres/amenagement-et-urbanisme"
  }, 
  "Climat": {
    .....
  }
``` 
<br>

### **/api/organizations**

```json
{
  "territoires": [
    {
      "label": "Zone maritime des Terres australes et antarctiques fran\u00e7aises (TAAF)", 
      "language": "fr", 
      "uri": "ZM-ATF"
    }, 
    {
      "label": "Zone maritime de La R\u00e9union", 
      "language": "fr", 
      "uri": "ZM-REU"
    }, 
    {
      "label": "Zone maritime de Mayotte", 
      "language": "fr", 
      "uri": "ZM-MYT"
    }, 
    {
      "label": "Zone maritime de Nouvelle Cal\u00e9donie", 
      "language": "fr", 
      "uri": "ZM-NCL"
    }, 
    {
      "label": "m\u00e9tropole - zone Atlantique", 
      "language": "fr", 
      "uri": "ZM-FX-Atl"
    }, 
    {
      "label": "Zone maritime de St Pierre et Miquelon", 
      "language": "fr", 
      "uri": "ZM-SPM"
    }, 
    {
      "label": "Zone maritime de Martinique", 
      "language": "fr", 
      "uri": "ZM-MTQ"
    },...
}
``` 