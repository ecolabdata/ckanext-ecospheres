
![CKAN GUICHET DE DONNEES](https://img.shields.io/badge/CKAN%20Guichet%20de%20de%20données-2.0.0%20%20développement%20-success.svg)
![Ahmed boukerram](https://img.shields.io/badge/mise%20à%20jour%20-Août%202022-red)

- [1- Installation de l'environnement de développement docker pour CKAN](#installation-de-l-environnement-de-developpement-docker)
    - [1.1- Moissonner des données](#moissonner-des-données)
      - [1.1.1- Ajouter une source de moissonnage](#ajouter-une-source-de-moissonnage)
      - [1.1.2- Lancer un  moissonnage](#lancer-un-moissonnage)
      - [1.1.3- Purger les jeux de données](#purger-les-jeux-de-données)
    - [1.2- Ajouter une extension](#ajouter-une_extension)
      
- [2- Ajouter d'un utilisteur admin](#ajouter-un-utilisateur-admin)


- [3- Lancement des tests unitaires](#lancement-des-tests-unitaires)
  
- [4- Avancement des développpements](#avancement-des-développements)
    - [4.1- Moissonnage](#moissonnage)
    - [4.2- Exposition](#exposition)
    - [4.3- Développements back/front](#developpements-back/front)
    - [4.4- Gestion des vocabulaires ](#gestion-des-vocabulaires )
    
<br>

## 1- Installation de l'environnement de développement docker
Tout d'abord, il faut disposer de [docker](https://docs.docker.com/engine/install/ubuntu/) et [docker-compose](https://docs.docker.com/compose/install/) sur sa machine. 

```bash
# Se placer à la racine du répertoire ckan-dev/
cd ckan-dev/
# Lancer la construction de l'image docker mtes/ckan-dev:2.9
# On installera dans cette image toutes les extensions dont on aura besoin : harvest, scheming, dcat, spatial, ect...
docker build -t mtes/ckan-dev:2.9  -f   2.9/Dockerfile . 

# Une fois la constuire de l'image terminée, il faut lancer le docker-compose.
# Note: on ajoute '-d' pour lancer les services dockers en arrière plan
docker-compose -f docker-compose.dev.yml  up -d

# pour suivre les logs docker-compose -f docker-compose.dev.yml  logs -f nom_du_service_docker
docker-compose -f docker-compose.dev.yml  logs -f ckan-dev

#Executer une commande linux dans un conteneur 
docker-compose -f docker-compose.dev.yml  exec ckan-dev command_linux

#Démarrrer un terminal interactif avec un conteneur
# 1- pour avoir la liste des conteneurs actifs et leur id 
docker ps 

# 2- démarrer un terminal interactif
docker exec -ti id_conteneur sh



```

A noter que vous pourriez rencontrer différents problèmes lors du lancement du docker-compose, dans ces cas, vous pourriez effécter l'une/ces action(s): 
```bash

# stopper tous les conteneurs (services)
docker-compose -f docker-compose.dev.yml  down

# supprimer et reconstuire toutes les images
# 1- supprimer toutes les images
docker rmi -f $(docker images -aq)
# 2- rééxecuter les commandes décrites au paragraphe précedent.

#supprimer les volumes
docker volume prune

```
## **1-1- Moissonner des données**
### **1.1.1- Ajouter une source de moissonnage**
<br>
L'ajout d'une source de moissonnage se faire via l'insterface graphique sur l'url suivante <i>http://ckan-dev:5000/harvest/</i>

> A note qu'il faut être admin afin de pouvoir ajouter une source de moissonnage 

<br>


### **1.1.2- Lancer un moissonnage**
 Pour lancer un moissonnage, il faudra dans un premier temps récupérer l'id de la source de moissonnage, comment l'obtenir ?
 ```shell
docker-compose -f docker-compose.dev.yml exec ckan-dev ckan -c ckan.ini harvester sources
 ```

 Une fois l'id de la source de moissonnage récupéré, on peut lancer un moissonnage avec la commande suivante: 
 
 ```bash 
 docker-compose -f docker-compose.dev.yml exec ckan-dev ckan -c ckan.ini harvester run-test id_source_moissonnage

 ```



<br>

### **1.1.3- Purger les jeux de données**

 ```bash 
 docker-compose -f docker-compose.dev.yml exec ckan-dev ckan -c ckan.ini harvester source clear id_source_moissonnage

 ```

<br>

## **1.2- Ajouter une extension**
---
- La commande suivante permet de **créer** une extension:

```bash
"le code source de l'extension sera généré dans le répertoire src/"
docker-compose -f docker-compose.dev.yml exec ckan-dev /bin/bash -c "ckan generate extension --output-dir /srv/app/src_extensions"
```
Ensuite pour activer l'extension, il faurdra ajouter le nom de l'extension à la liste des extensions que CKAN doit charger à son lancement. Pour se faire, il fait ajouter le nom de la nouvelle extension à la variable **CKAN__PLUGINS** dans le ficher **<i>.env</i>** comme suit:
> CKAN__PLUGINS="nom_de_mon_extnsion_plugin ......autres extensions"
---
<br>
 Pour installer une extension existante à partir d'un repos github:

Prenons l'**<u>Extension ecosphere</u>** sur laquelle on travaille actuellement:
```bash
# on se place danle le répertoire src/
export EXT_ECOS_GIT="https://github.com/ecolabdata/ckanext-ecospheres.git"
git clone EXT_ECOS_GIT
```
On Ajoute les plugins suivants à la liste des plugins que CKAN doit charger:
> CKAN__PLUGINS="ecospheres  dcat_ecospheres_harvester dcat_ecospheres_plugin ....autres extensions"
        
<br>

>**Remarques**:<br>
Il faut redémarrer le service <i>ckan-dev</i> dans les cas suivants:
>- Ajout d'un plugin (Example: le cas décrit précédement)
>- Modification du ficjer Scheming

# **2- Ajouter un utilisateur admin**
Toute d'abord, il faut créer un compte utilisateur à partir de l'interface graphique.

```
docker-compose -f docker-compose.dev.yml exec ckan-dev ckan -c ckan.ini sysadmin add user_admin
```

# **3- Lancement des tests unitaires** 
> **Remarque**: Lorsqu'on modifie du code et fait tester, il n'est pas necessaire de redémarrer le service ckan-dev pour que les modification soient prises en compte?


### **3.1- Test moissonnage (parse_dataset)**
``` 
docker-compose -f docker-compose.dev.yml exec ckan-dev  pytest  -v -s  -c src_extensions/ckanext-ecospheres/test.ini src_extensions/ckanext-ecospheres/ckanext/ecospheres/tests/test_parser_french_profile.py --disable-pytest-warnings 
``` 


### **3.2- Test exposition (serializer)**
``` 
docker-compose -f docker-compose.dev.yml exec ckan-dev  pytest  -v -s  -c src_extensions/ckanext-ecospheres/test.ini src_extensions/ckanext-ecospheres/ckanext/ecospheres/tests/test_serializer_french_profile.py --disable-pytest-warnings 
ings 
``` 

> **Pour ajouter des tests**: il faut ajouter un fichier python **test_<i>nom_fichier</i>**.py dans le repertoire test/ et lancer la commande suivante:<br> <br>
docker-compose -f docker-compose.dev.yml exec ckan-dev  pytest  -v -s  -c src_extensions/ckanext-ecospheres/test.ini src_extensions/ckanext-ecospheres/ckanext/ecospheres/tests/**test_<i>nom_fichier</i>**.py --disable-pytest-warnings 
ings 



# **4- Avancement des développpements**


## **4.1- Moissonnage**
- Le script de moissonnage est localisé dans le module <i>ckanext-ecospheres\ckanext\ecospheres\dcat\profiles\dataset</i> et les tests associés dans le fichier <i>src\ckanext-ecospheres\ckanext\ecospheres\tests\test_parser_french_profile.py</i>
   - le fichier **<i>parse_dataset.py</i>** contient la fonction pricipale de parsing **parse_dataset** (qui est la fonction redéfie)
   - le fichier <i>**_function.py**</i> contient des les fonctions unitaires de parsing 

- Toutes les metadonnées spécifiées dans le fichier scheming sont parsées et testées 
- Les métadonnées relatives aux thèmes et sous-thèmes ne sont pas testées à date (tests à faire)
- Le mapping des thèmes se fait suivant l'algorithme préconisé par Benoît. (CF. ckanext-ecospheres\ckanext\ecospheres\dcat\profiles\dataset\_functions.py. L49)
- L'alimentation du champ territoire se fait ( à date) de manière suivante:
    - Une fois que la fonction **<i>parse_dataset.py</i>** ait renvoyé son resultat, on verifie si le champ **spatial** est présent.
    - On ne fait rien si le champ **spatial** est présent
    - Dans le cas contraire, on récupére les informations relatives à l'organisation liée à la source de  moissonnage et les informations sur la localisation et coordonnées et on calcule le champ **spatial**
    - A date, le champ **spatial** n'est pas calculé ( A faire) 
- Le mapping des formats des ressorces se fait (à date ) au moment du moissonnage. Cette méthode ne me semble pas pertinente vu qu'il se pourrait qu'il y ait de nouveaux formats à ajouter. Donc il serait plus pertinent de on va gérer ce <i>mapping</i> comme un vocabulaire externalisé et le mapping des foramts de ressources se fera au moment de la restitution de l'ecran à l'utilisateur

- Les dévelopements réalisés à date sont en attente de relecture et de validation. 





## **4.2- Exposition**
- Le script d'exposition est localisé dans le module <i>src\ckanext-ecospheres\ckanext\ecospheres\dcat\profiles\graph</i> et les tests associés dans le fichier <i>test_serializer_french_catalog.py</i>
   - le fichier **<i>graph_from_dataset.py</i>** contient la fonction pricipale de parsing **parse_dataset**
   - le fichier <i>**_function.py**</i> contient des les fonctions unitaires de serialisation 

- Toutes les métadonnées specifiées comme <i>exposables</i> sont exposées et testées excepté les métadonnées relatives aux thèmes et sous-thèmes
- Les dévelopements réalisés à date sont en attente de relecture et de validation. 

<br><br>

## **4.3- Développements back/front**
<br>

- **3.1- Filtres page d'accueil** :

| Filtre |        Native                | Développement          |
|--------:|:--------------------:|:------------------|
| **Organisation**       |   oui                   |    Selection multiple à développer               |
| **Thèmatique**        |       Non                | Fait          |
| **Sous-Thèmatique**       |      Non                 |  Fait                 |
|   **Territoire**      |Non |        Fait   | 


- Il faudra prevoir aussi d'un job qui calculera le nombre de jeux de données par 
    - Organisation
    - Thèmatique
    - Sous-Thèmatique
    - type d'administration
    
Le calcul interviendra après chaque phase de moissonnage, on attendra que tous les moissonnages aient fini pour lancer le job de calcul, le resultat sera stocké en base de donnnées et exposé à travers un API ou fonction ( à voir ce qui plus pertinent) afin d'être consommé par le front.   
<br>

- **3.2- Filtres page de jeux de données** :

| Filtre |        Native                | Développement          |
|--------:|:--------------------:|:------------------|
| **Organisation**       |   oui                   |    Selection multiple à développer               |
| **Thèmatique**        |       Non                | Fait          |
| **Sous-Thèmatique**       |      Non                 |  Fait                 |
|   **Territoire**      |Non |        Fait   | 
|   **Inclusion des subdivision**      |Non |        A faire   | 
|   **Inclusion des données à accès restreint**      |Non |        A faire   | 
|   **Filtrer par date de mise à jour**      |Non |        Fait. Exemple de requêtes: [1]   | 

<br>

- **Filtres page organisations** :

| Filtre |        Native                | Développement          |
|--------:|:--------------------:|:------------------|
| **Type d'organisation**       |   Non                  |    Développement au niveau du front (le tri  se fera côté client)               |
| **Territoire de compétence**       |   Non                  |    Développement au niveau du front (le tri se fera côté client)               |

- **Exposition des API:**
    - Lister les types d'adminstration et leurs organisations associées et leur nombre de jeux de données (<u>A faire</u>)
    - Lister les territoires et leur nombre de jeux de données (<u>Fait</u>)
    - Lister les thèmes et sous-thèmes et leur nombre de jeux de données (<u>fait</u>)


<br>

## **4.5- Gestion des vocabulaires**
 
- L'ingestion et le stockage en base de données des  vocabulaires Territoires et thèmes sont développés, et utilisés notamment pour le mapping des thèmes et des territoires lors du moissonnage. Cependant, après un atelier de travail avec Lislie le mercredi 3 août et vu le nombre de vocabulaires à traiter, on va etre amené à modifier et faire evoluer cette fonctionnalité pour le rendre plus générique.
- Par conséquent, Leslie s'occupera du parsing des vocabulaires, et de mon côté, je m'occuperai de la partie mise en base.
- Pour Actionner la mise à jour manuelle d'un/des vocabulaire(s), j'ai prévu de d'exposer un API dans ce but. 
- Il faut penser à mettre en place un vocabulaire de licences (ouvertes et restreintes)




# 
[1]  
``` bash
 "filter les jeux de données par date de mise à jour de ext_startdate à ext_enddate"
# /dataset/?q=&ext_startdate=2022-07-20T11:48:38.540Z&ext_enddate=2023-07-20T11:48:38.540Z

 "filter les jeux de données par date de mise à jour à partir de  ext_startdate "
# /dataset/?q=&ext_startdate=2022-07-20T11:48:38.540Z

 "filter les jeux de données par date de mise à jour jusqu'à ext_enddate"
# /dataset/?q=&ext_enddate=2022-07-20T11:48:38.540Z

```