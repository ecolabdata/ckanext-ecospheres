
from ckanext.ecospheres.models.territories import Territories
from ckanext.ecospheres.models.themes import Themes,Subthemes
from ckanext.ecospheres.registre_loader.themes_rdf_parser import RDFThemesCGDDparser
import logging
log = logging.getLogger(__name__)
from pathlib import Path
from os.path import exists
import json

# Cette classe permet de ne créer qu'une seule instance de la classe qui l'etend
class MetaSingleton(type):
    __instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in MetaSingleton.__instances:
            MetaSingleton.__instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return MetaSingleton.__instances[cls]


class Loader(metaclass=MetaSingleton):
    def __init__(self,
                yml_path="/srv/app/src_extensions/ckanext-ecospheres/ckanext/ecospheres/registre_loader/registres.yml",
                force=False):
        self.force=force
        self.__config=self.yaml_reader(yml_path)
        self.__common_config=self.__get_config_dict_by_key("common")
        self.__load()


    def __load(self):
        self.__load_territories_from_db()
        self.__load_themes_from_db()
        self.__load_languages_from_db()

    

    # On verifie si la table Territories -> on recupere les données 
    # Si on creer la table et on charge les données selon les paramtres du fichier registres.yml
    def __load_territories_from_db(self):
        log.info("Chargement du référentiel des territoires...........")
        t=Territories.__table__
        __new=False
        if not t.exists():
            __new=True
            log.info("La Table Territories n'existe pas")
            log.info("Création de la table Territories....")
            try:
                t.create()
            except Exception as e:
                log.error(f"Erreur lors de la création de la table  {t.name}",exc_info=True)
        
        #si la table est nouvelle ou bien le parametre force est à true, on recharge le referentiel
        if __new or self.force:
            log.info("Chargement du referentiel")
            territoire_config=self.__get_element_config_by_key("territoires")
            data_file=self.__get_data_file(territoire_config)
            self.load_territorie_from_file_to_db(data_file)
            log.info("Référentiel des territoires chargé")
        self.__territoires= Territories.get_territories()

        



    def __load_themes_from_db(self):
        """_summary_
        Chargement des themes depuis la base de données
        Raises:
            Exception: _description_
        """
        log.info("Chargement du référentiel des themes.....")
        __new=False
        t_themes=Themes.__table__
        t_subthmes=Subthemes.__table__
        for t in (
            t_themes,
            t_subthmes
        ):
            if not t.exists():
                __new=True
                log.info(f"Création de la table {t.name}.......")
                t.create()
                log.info(f"Table {t.name} créé")

        if  __new or self.force:
            log.info("Chargement du référentiel des themes et sous-themes")
            themes_config=self.__get_element_config_by_key("themes")
            data_file=self.__get_data_file(themes_config)
            self.load_themes_from_file_to_db(data_file)
            log.info("Référentiel des themes chargé.")
        self.__themes=Themes.get_theme()

    
    def __get_data_file(self,territoire_config):
        """_summary_
        Téléchargement du fichier: soit depuis l'url ou bien depuis un fichier local
        Args:
            territoire_config (_type_): _description_
        """
        filedata=None
        # telachargement du fichier depuis un serveur distant
        #TODO
        url=territoire_config["url"]

        #si le téléchargement depuis le serveur distant échoue, on charge le registre depuis le fichier local
        if not filedata:
            filedata=self.__get_file_from_disk(territoire_config["src"])
        return filedata



    def __load_languages_from_db(self):
        #TODO
        self.__languages=[]
        log.info("chargement du referentiel langues à partir de la base de données")
    



    def __get_element_config_by_key(self,key_config):
        return self.__common_config[key_config] if key_config in self.__common_config else None

    def __get_config_dict_by_key(self,key):
        for __conf in self.__config:
            if list(__conf.keys())[0]== key:
                return __conf[key]



    ################# GETTERS ####################

    @property
    def territoires(self):
        return self.__territoires

    @property
    def themes(self):
        return self.__themes
    
    @property
    def languages(self):
        return self.__languages

    

    def get_territorie_by_code_region(self,code_region):
        for territoire in self.__territoires:
            if territoire["codeRegion"]==code_region:
                return territoire


                
    ################# DATABASE OPERATIONS ####################

    def load_themes_from_file_to_db(self,data_file):
        """_summary_
        
        Chargement du referentiel Themes et sous-Themes en base de données

        Args:
            data_file (_type_): _description_
        """
        parser=RDFThemesCGDDparser()
        parser.parse(data_file,_format="jsonld")
        themes_parsed=parser._get_themes_as_list()
        Subthemes.delete_all()
        Themes.delete_all()
        for theme in themes_parsed:
            prefLabel=theme.get("prefLabel",None)
            uri=theme.get("uri",None)
            Themes.from_data(
                uri=theme.get("uri",None),
                pref_label=theme.get("prefLabel",None),
                alt_label=theme.get("altLabel",None),
                change_note=theme.get("changeNote",None),
                definition=theme.get("definition",None),
            )
            
            if subthemes_list:=theme.get("narrower",None):
                for subtheme in subthemes_list:
                    Subthemes.from_data(
                        pref_label=subtheme.get("prefLabel",None),
                        uri=subtheme.get("uri",None),
                        broader=subtheme.get("broader",None),
                        definition=subtheme.get("definition",None),
                        alt_label=subtheme.get("altLabel",None),
                        regexp=subtheme.get("regexp",None),
                        theme_id=theme.get("prefLabel",None)
                    )


    
    def load_territorie_from_file_to_db(self,data_file):
        """_summary_
        Chargement du referentiel Territoires en base de données

        Args:
            data_file (_type_): _description_

        Returns:
            _type_: _description_
        """
        try:
            Territories.delete_all()

            json_file=json.loads(data_file)
            types_regions=['régions-métrople', 'départements-métropole', 'outre-mer', 'zones-maritimes']
            for type_region in types_regions:
                for code_region in json_file[type_region].keys():
                    region_dict=json_file[type_region][code_region]
                    uriUE=region_dict.get("uriUE",None)
                    name=region_dict.get("name",None)
                    if spatial:=region_dict.get("spatial",None):
                        westlimit=spatial.get("westlimit",None)
                        southlimit=spatial.get("southlimit",None)
                        eastlimit=spatial.get("eastlimit",None)
                        northlimit=spatial.get("northlimit",None)
                    Territories.from_data(type_region=type_region,
                            name=name or None,
                            codeRegion=code_region or None,
                            uriUE=uriUE or None,
                            westlimit=westlimit or None,
                            southlimit=southlimit or None,
                            eastlimit=eastlimit or None,
                            northlimit=northlimit or None) 
            return True
        except Exception as e:
            log.error("Erreur lors du chargement des données en base de données",exc_info=True)
            return False

    def __get_file_from_disk(self,filename):
        """_summary_
            Chargement d'un fichier à partir du disque local
        Args:
            filename (_type_): _description_

        Raises:
            Exception: _description_

        Returns:
            _type_: _description_
        """
        try:
            path =  Path(filename)
            file_exists = exists(path)
            if not file_exists:
                return None
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            raise Exception("Erreur lors de la lecture du fichier json des themes")

    def yaml_reader(self,yaml_path):
        """_summary_
        chargement d'un fichier yaml depuis le disque local
        Args:
            yaml_path (_type_): _description_

        Returns:
            _type_: _description_
        """
        import yaml
        with open(yaml_path, 'r') as stream:
            try:
                parsed_yaml=yaml.safe_load(stream)
                return parsed_yaml
            except yaml.YAMLError as exc:
                print(exc)
                raise