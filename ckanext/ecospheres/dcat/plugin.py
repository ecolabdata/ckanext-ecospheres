import collections
import json
import re
from urllib import parse

from flask import Blueprint

import ckan.plugins as plugins
from ckan.lib.helpers import lang

import ckanext.ecospheres.validators as v
import ckanext.ecospheres.helpers as helpers
from ckanext.ecospheres import cli
from ckanext.ecospheres.scheming.tab import get_fields_by_tab
from ckanext.ecospheres.vocabulary.reader import VocabularyReader
from ckanext.ecospheres.vocabulary.loader import load_vocab as load_all_vocab
from ckanext.ecospheres.views import organizations_by_admin_type

    


class DcatFrenchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)

    
    
    # ------------- IClick ---------------#
    def get_commands(self):
        return cli.get_commands()
    
    
    # ------------- IConfigurer ---------------#
    def get_helpers(self):

        '''
        Enregistrement des fonctions comme helpers functions utilisé dasn la partie front.
        l'appel à ses fonction se fait de la manière suivante: 

        {{ h.function_name( param1=value1,param1=value2) }}

        '''

        return {
                'fr_dcat_json_string_to_object_aggregated_ressources':helpers.json_string_to_object_aggregated_ressources,
                'fr_dcat_aggregated_package_name_to_title':helpers.aggregated_package_name_to_title,
                'get_localized_value_for_display':helpers.get_localized_value_for_display,
                'get_localized_date':helpers.get_localized_date,
                'get_territories_label':helpers.get_territories_label,
                'get_type_adminstration_label_by_acronym':helpers.get_type_adminstration_label_by_acronym,
                'get_vocabulary_label_by_uri':helpers.get_vocabulary_label_by_uri,
                'get_fields_by_tab':get_fields_by_tab,
                'get_vocabulairies_for_given_repeating_subfields':helpers.get_vocabulairies_for_given_repeating_subfields,
                'get_vocabulairies_for_given_fields':helpers.get_vocabulairies_for_given_fields,
                'get_vocab_label_by_uri_from_list_of_vocabularies':helpers.get_vocab_label_by_uri_from_list_of_vocabularies,
                }

    # ------------- IValidators ---------------#

    def get_validators(self):
        return {
            'timestamp_to_datetime': v.timestamp_to_datetime,
            'multilingual_text_output': v.multilingual_text_output,
        }


    # ------------- IFacets ---------------#

    def dataset_facets(self, facets_dict, package_type):
        """
        Cette fonction permet de specifier les filtres à appliquer aux jeux de données.
        Example:  facets_dict['category'] = plugins.toolkit._('Thématiques') -> permet d'ajouter un filtre sur le champ
        indexé "category"
        NB: On ne peut ajouter que des champ indexé par solr.

        """
        facets_dict = collections.OrderedDict()
        facets_dict['organization'] = plugins.toolkit._('Organizations')
        facets_dict['category'] = plugins.toolkit._('Category')
        facets_dict['territory'] = plugins.toolkit._('Territory')
        facets_dict['res_format'] = plugins.toolkit._('Formats')
        
        return facets_dict

    def organization_facets(
            self, facets_dict: 'OrderedDict[str, Any]', organization_type,
            package_type) -> 'OrderedDict[str, Any]':
        u'''Modify and return the ``facets_dict`` for an organization's page.

        The ``package_type`` is the type of dataset that these facets apply to.
        Plugins can provide different search facets for different types of
        dataset. See :py:class:`~ckan.plugins.interfaces.IDatasetForm`.

        The ``organization_type`` is the type of organization that these facets
        apply to.  Plugins can provide different search facets for different
        types of organization. See
        :py:class:`~ckan.plugins.interfaces.IGroupForm`.

        :param facets_dict: the search facets as currently specified
        :type facets_dict: OrderedDict

        :param organization_type: the organization type that these facets apply
                                    to
        :type organization_type: string

        :param package_type: the dataset type that these facets apply to
        :type package_type: string

        :returns: the updated ``facets_dict``
        :rtype: OrderedDict

        '''
        return facets_dict

    def before_index(self, search_data):
        """
        Cette fonction est appelée avant qu'un jeux de données ne soit indexé.
        Elle permet de modifier les données indexées par le moteur de recherche Solr.
        Pour ce faire, il faut ajouter la données à indexer dans le dictionnaire search_data
        """

        validated_dict = json.loads(search_data['validated_data_dict'])
        
        if categories:=validated_dict.get("category",None):
            search_data["category"]=[categorie["uri"] for categorie in categories]
    
        if territory:=validated_dict.get("territory",None):
            search_data["territory"]=[ter['uri'] for ter in territory]

        if modified:=validated_dict.get("modified",None):
            search_data["modified"]=modified.replace("+00:00",'')

        if restricted_access:=validated_dict.get("restricted_access",None):
            search_data["restricted_access"]=restricted_access

        if created:=validated_dict.get("created",None):
            search_data["created"]=created.replace("+00:00",'')

        if issued:=validated_dict.get("issued",None):
            search_data["issued"]=issued.replace("+00:00",'')

        return search_data


    
    def before_search(self, search_params):
        """
        Cette fonction permet d'intercepter la reqûete avant de faire une
        recherche pour ajouter/modifier/enrichir des paramètres de recherche,
        A noter, pour ajouter des paramtres extra à une requetes dans CKAN et
        les recuperer avec la clé "extras", il faut préfixer le nom du paramtres
        par "ext_"
        """

        """ Filtre par organistion 


        Par défaut, lorsqu'on veut filter les jeux de données par plus d'une
        organisation, CKAN utilise l'opération AND.
        Par consequent, comme dans notre cas Ecosphere, un jeu de données
        n'appartient qu'à une seule organisation, le moteur d'indexation
        ne remontera aucun résultat
        Donc pour récuperer les jeux de données appartenant aux organisations
        présentes dans le reqûete, il faut modifier cette reqûete qui envoyée
        au moteur Solr pour qu'il applique l'opérateur OR. 

        q=organization:"organisation_1"+organization:"organisation_2" 
        deviendra: q=organization:"organisation_1" OR organization:"organisation_2" 

        """
        fq = search_params.get('fq',None)
        extras=search_params.get("extras",None)
        if fq or extras:

            regex_orgs = r"([+]*organization\s*:\s*\"([^\"]*)\")"
            matches = re.finditer(regex_orgs, fq, re.MULTILINE)
            list_organizations=[]
            for _, match in enumerate(matches, start=1):
                list_organizations.append(match.group(2))
            if list_organizations:
                fq = re.sub(regex_orgs, "", fq, 0, re.MULTILINE)
                query=''
                op=''
                for org in list_organizations:
                    if query:
                        op='OR'
                    query=f'{query} {op} organization:"{org}"'
                if len(fq.strip()) > 0:
                    query=f'{query} OR'
                fq=f'{fq.strip()} {query.strip()}'

            """ Filtre par territoires :

            * Les labels sont remplacés par les URI correspondants.
            * On veut une union, pas une intersection.
            * Ajout des subdivisions, si ``include_subdivision`` vaut
              ``True``.

            TODO: Voir s'il est possible d'utiliser un output validator
            pour avoir dès le départ les URI dans l'URL ? [LL-2023.01.16]

            /dataset/?q=&ext_include_subdivision=true&territory=Nouvelle-Aquitaine

            """ 
            territoires = []
            regex_territory =  r"([+]*territory\s*:\s*\"([^\"]*)\")"
            matches = re.finditer(regex_territory, fq, re.MULTILINE)
            for _, match in enumerate(matches, start=1):
                territoires.append(match.group(2))
            fq = re.sub(regex_territory, "", fq, 0, re.MULTILINE)
            
            territoires_uris = []
            for territoire in territoires:
                territoire_label = parse.unquote_plus(territoire)
                territoire_uri = VocabularyReader.get_uri_from_label(
                    vocabulary='ecospheres_territory', label=territoire_label
                )
                territoires_uris.append(territoire_uri)
            if extras:=search_params.get('extras'):
                if extras.get('ext_include_subdivision'):
                    territoires_uris += VocabularyReader.get_children(
                        vocabulary='ecospheres_territory', uri=territoires_uris
                    )

            query = ' OR territory:'.join([
                '"{0}"'.format(parse.quote(territoire_uri))
                for territoire_uri in territoires_uris
            ])
            if query:
                fq = f'{fq} +(territory:{query})'

            """ 
            Filtre par thème Ecosphères :

            * Les labels sont remplacés par les URI correspondants.
            * On veut une union, pas une intersection.

            TODO: Voir s'il est possible d'utiliser un output validator
            pour avoir dès le départ les URI dans l'URL ? [LL-2023.01.16]          

            """
            categories = []
            regex_category = r"([+]*territory\s*:\s*\"([^\"]*)\")"
            matches = re.finditer(regex_category, fq, re.MULTILINE)
            for _, match in enumerate(matches, start=1):
                categories.append(match.group(2))
            fq = re.sub(regex_category, "", fq, 0, re.MULTILINE)

            categories_uris = []
            for category in categories:
                category_label = parse.unquote_plus(category)
                category_uri = VocabularyReader.get_uri_from_label(
                    vocabulary='ecospheres_theme', label=category_label
                )
                categories_uris.append(category_uri)
            query = ' OR category:'.join([
                '"{0}"'.format(parse.quote(category_uri))
                for category_uri in categories_uris
            ])
            if query:
                fq = f'{fq} +(category:{query})'

            if extras:
                """
                Le schèma de search_params est :
                    {
                        'extras': {}, 
                        'facet.field': ['organization', 'category', 'territory', 'res_format'],
                        'fq': '', 
                        'q': '', 
                        'rows': 20,
                        'start': 0,
                        'include_private': True, 
                        'df': 'text'
                    }

                Pour récuperer des paramètres supplémentaires, il faut utiliser le champ "extras". 
                pour récuperer un paramètre dans 'extras', il faut préfixer le nom du paramètre par 'ext_': 
                    exemple:   reqûete http: dataset/q=&ext_param=param_value
                            before_search: ext_param = search_params["extras"][ext_param"]
                
                """
            
                restricted_access=extras.get("ext_restricted_access",None)
                start_date=extras.get("ext_startdate",None)
                end_date=extras.get("ext_enddate",None)



                """ filter par dates de mise à jour 
                
                /dataset/?q=&ext_startdate=2022-07-20T11:48:38.540Z&ext_enddate=2023-07-20T11:48:38.540Z
                /dataset/?q=&ext_startdate=2022-07-20T11:48:38.540Z
                /dataset/?q=&ext_enddate=2022-07-20T11:48:38.540Z

                """

                if start_date or end_date:
                    
                    if not start_date :
                        start_date="*"
                    
                    if not end_date:
                        end_date="NOW"
                        
                    fq = '{fq} +modified:[{start_date} TO {end_date}]'.format(
                                            fq=fq, start_date=start_date, end_date=end_date)
                
                """ filtrer par données à accès resteint
                
                /?q=&ext_restricted_access=true
                /?q=&ext_restricted_access=false

                """
                if restricted_access is not None:
                    fq = '{fq} extras_restricted_access:{restricted_access} '.format(
                                            fq=fq, restricted_access=restricted_access)
                q = search_params.get('q', '')
                search_params['q'] = re.sub(":\s", " ", q)



            search_params['fq'] = fq
        return search_params
    

    


    def after_search(self,search_results, search_params):
        '''
        Cette fonction est appellé après qu'un resultat soit renvoyé de l'indexateur Solr.
        On peut ajouter/modifier/supprimer des données avant qu'elles ne soient transmises vers le front
        
        '''
        search_dicts = search_results.get('results', [])
        territories = []
        themes = []
        for _dict in search_dicts:
            lang_code = lang()

            if territory:=_dict.get('territory',None):
                for item in territory:
                    if uri:=item.get("uri",None):
                        labels=helpers.get_vocabulary_label_by_uri("ecospheres_territory",uri)
                        territories.append(labels)
            _dict["territory"]=territories

            if theme:=_dict.get('theme',None):
                for item in theme:
                    if uri:=item.get("uri",None):
                        if labels:=helpers.get_vocabulary_label_by_uri("ecospheres_theme",uri,lang_code):
                            themes.append(labels)
                        elif labels:=helpers.get_vocabulary_label_by_uri("eu_theme",uri,lang_code):
                            themes.append(labels)
            _dict["theme"]=themes


            _dict_resources = _dict.get('resources', None)
            for resource in _dict_resources:
                if resoueces_type:=resource["format"]:
                    label=helpers.get_vocabulary_label_by_uri("iana_media_type",resoueces_type)
                    resource["format"]=label

        return search_results





    # ------------- IBlueprint ---------------#
    
    # def _get_territoires(self):
    #     return {
    #             "territoires": VocabularyReader.labels(vocabulary="ecospheres_territory")
    #            }
               
    # def _get_themes(self):
    #     return VocabularyReader.themes()
    
    def _get_organizations(self):
        return organizations_by_admin_type()
    
    # def _get_territoires_hierarchy(self):
    #     return VocabularyReader._get_territories_by_hierarchy()

        
    def get_blueprint(self):
        """
        Exposition des APIs 

        """
        blueprint = Blueprint('dcatapfrench_custom_api', self.__module__)
        # TODO: see if this was useful in any way... [LL-2023.01.10]
        rules = [ 
        #     ('/api/territoires', 'get_territoires', self._get_territoires),
        #     ('/api/territoires_hierarchy', 'get_territoires_hierarchy', self._get_territoires_hierarchy),
        #     ('/api/themes', 'get_themes', self._get_themes),
            ('/api/organizations', 'get_organizations', self._get_organizations),
        ]
        for rule in rules:
            blueprint.add_url_rule(*rule)

        from flask import request
        @blueprint.route('/api/load-vocab', methods=["POST"])
        def _load_vocab_():
        
            import ckan.lib.base as base
            import ckan.model as model
            import ckan.logic as logic
            c = base.c


            context = {'model': model,
                'user': c.user, 'auth_user_obj': c.userobj}
            try:
                logic.check_access('sysadmin', context, {})
            except logic.NotAuthorized:
                base.abort(403, 'Need to be system administrator to administer')

            vocab = request.get_json()
            import threading

            vocab_list=vocab.get("vocab_list",[])

            class BackgroundTasks(threading.Thread):
                def run(self,*args,**kwargs):
                    load_all_vocab(vocab_list=vocab_list)

            t = BackgroundTasks()
            t.start()    
               
            if vocab_list!=[]:
                msg=f'chargement des vocabulaires: { "".join(vocab.get("vocab_list",None)) } lancé'
            else:
                msg='chargement de tous les vocabulaires lancé'
            
            return {
                "msg": msg
            
                        }
        return blueprint