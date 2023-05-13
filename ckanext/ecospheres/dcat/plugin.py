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
from ckanext.ecospheres.vocabulary.reader import VocabularyReader
from ckanext.ecospheres.vocabulary.loader import load_vocab as load_all_vocab
from ckanext.ecospheres.views import organizations_by_admin_type


#TODO: use blanket to declare validators, helpers, etc.
# https://docs.ckan.org/en/latest/extensions/plugins-toolkit.html#ckan.plugins.toolkit.ckan.plugins.toolkit.blanket
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
                'fr_dcat_json_string_to_object_aggregated_ressources': helpers.json_string_to_object_aggregated_ressources,
                'fr_dcat_aggregated_package_name_to_title': helpers.aggregated_package_name_to_title,
                'get_localized_value_for_display': helpers.get_localized_value_for_display,
                'get_localized_date': helpers.get_localized_date,
                'get_territories_label': helpers.get_territories_label,
                'get_type_adminstration_label_by_acronym': helpers.get_type_adminstration_label_by_acronym,
                'get_vocabulary_label_by_uri': helpers.get_vocabulary_label_by_uri,
                'get_vocabulairies_for_given_repeating_subfields': helpers.get_vocabulairies_for_given_repeating_subfields,
                'get_vocabulairies_for_given_fields': helpers.get_vocabulairies_for_given_fields,
                'get_vocab_label_by_uri_from_list_of_vocabularies': helpers.get_vocab_label_by_uri_from_list_of_vocabularies,
                'ecospheres_get_vocabulary_label_from_field': helpers.ecospheres_get_vocabulary_label_from_field,
                'ecospheres_is_empty': helpers.ecospheres_is_empty,
                'ecospheres_retrieve_uri_subfield': helpers.ecospheres_retrieve_uri_subfield,
                'ecospheres_get_package_title': helpers.ecospheres_get_package_title,
                'ecospheres_get_field_dict': helpers.ecospheres_get_field_dict,
                'ecospheres_get_format': helpers.ecospheres_get_format
                }

    # ------------- IValidators ---------------#

    def get_validators(self):
        return {
            'timestamp_to_datetime': v.timestamp_to_datetime,
            'multilingual_text_output': v.multilingual_text_output,
            'ecospheres_email': v.ecospheres_email,
            'ecospheres_email_output': v.ecospheres_email_output,
            'ecospheres_phone': v.ecospheres_phone,
            'ecospheres_phone_output': v.ecospheres_phone_output
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
        
        if categories:=validated_dict.get("category"):
            search_data["category"]=[categorie["uri"] for categorie in categories]
    
        if territory:=validated_dict.get("territory"):
            search_data["territory"]=[ter['uri'] for ter in territory]

        # TODO: Ce n'est pas une méthode fiable pour supprimer le fuseau horaire !
        # [LL-2023.02.24]
        if modified:=validated_dict.get("modified"):
            search_data["modified"]=modified.replace("+00:00",'')

        if restricted_access:=validated_dict.get("restricted_access"):
            search_data["restricted_access"]=restricted_access

        if created:=validated_dict.get("created"):
            search_data["created"]=created.replace("+00:00",'')

        if issued:=validated_dict.get("issued"):
            search_data["issued"]=issued.replace("+00:00",'')

        # Bricolage pour ne pas indexer des choses qui ne plairont pas à Solr
        # TODO: indexer proprement ce qui doit l'être! [LL-2023.02.02]
        for field_name in [
            'temporal', 'contact_point', 'publisher', 'creator',
            'rights_holder', 'qualified_attribution', 'in_series', 'series_member',
            'landing_page', 'attributes_page', 'page', 'free_tags', 
            'bbox', 'territory_full', 'access_rights', 'restricted_access', 'crs',
            'conforms_to', 'accrual_periodicity', 'status', 'language', 'provenance',
            'version', 'version_notes', 'temporal_resolution', 'spatial_resolution',
            'equivalent_scale', 'as_inspire_xml', 'as_dcat_rdf', 'ckan_api_show',
            'spatial_coverage', 'themes', 'record_in_catalog', 'record_contact_point',
            'record_language'
        ]:
            if field_name in search_data:
                del search_data[field_name]
        if extras:=search_data.get('extras'):
            extras.clear()

        return search_data
    
    def before_search(self, search_params):
        """
        Cette fonction permet d'intercepter la reqûete avant de faire une
        recherche pour ajouter/modifier/enrichir les paramètres de recherche.
        """
        fq_in = search_params.get('fq')
        extras = search_params.get('extras')
        fq_out = []

        if fq_in:
            # Filtre par organization
            # - Union (OR) des valeurs.
            organizations, fq_in = _extract_pattern(r'\+?organization\s*:\s*"([^"]*)"', fq_in)
            if organizations:
                fq_out.append(_solr_or('organization', organizations))

            # Filtre par territoires
            # - Union (OR) des valeurs.
            # - Les labels sont remplacés par les URI correspondants.
            # - Ajout des subdivisions si include_subdivision == true.
            #
            # TODO: Voir s'il est possible d'utiliser un output validator
            # pour avoir dès le départ les URI dans l'URL ? [LL-2023.01.16]
            territories, fq_in = _extract_pattern(r'\+?territory\s*:\s*"([^"]*)"', fq_in)
            if territories:
                get_children = extras and extras.get('ext_include_subdivision', False)
                territories_uris = _map_to_uris(territories, 'ecospheres_territory', get_children)
                fq_out.append(_solr_or('territory', territories_uris))

            # Filtre par thème Ecosphères
            # - Union (OR) des valeurs.
            # - Les labels sont remplacés par les URI correspondants.
            #
            # TODO: Voir s'il est possible d'utiliser un output validator
            # pour avoir dès le départ les URI dans l'URL ? [LL-2023.01.16]
            categories, fq_in = _extract_pattern(r'\+?category\s*:\s*"([^"]*)"', fq_in)
            if categories:
                categories_uris = _map_to_uris(categories, 'ecospheres_theme')
                fq_out.append(_solr_or('category', categories_uris))

        if extras:
            # Filtre par date de mise à jour
            # - Date is ISO: 2022-07-20T11:48:38.540Z
            start_date = extras.get('ext_startdate')
            end_date = extras.get('ext_enddate')
            if start_date or end_date:
                fq_out.append(f'+modified:[{start_date or "*"} TO {end_date or "NOW"}]')

            # Filtre par données à accès resteint
            restricted_access = extras.get("ext_restricted_access")
            if restricted_access:
                fq_out.append(f'extras_restricted_access:{restricted_access}')

        search_params['fq'] = f'{fq_in} {" ".join(fq_out)}'.strip()

        # FIXME: Sert à quoi ?
        #q = search_params.get('q', '')
        #search_params['q'] = re.sub(":\s", " ", q)

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

            if territory := _dict.get('territory'):
                for item in territory:
                    if uri := item.get('uri'):
                        if label := VocabularyReader.get_label(
                            vocabulary='ecospheres_territory', uri=uri, language=lang_code
                        ):
                            territories.append(label)
            _dict['territory'] = territories

            # TODO: comprendre pourquoi ces deux vocabulaires
            # sont utilisés alors qu'ils correspondent à deux champs
            # différents, "category" et "theme" [LL-2023.02.29]
            if theme:=_dict.get('theme'):
                for item in theme:
                    if uri:=item.get('uri'):
                        if label := VocabularyReader.get_label(
                            vocabulary='ecospheres_theme', uri=uri, language=lang_code
                        ):
                            themes.append(label)
                        if label := VocabularyReader.get_label(
                            vocabulary='eu_theme', uri=uri, language=lang_code
                        ):
                            themes.append(label)
            _dict['theme'] = themes

            # TODO: not sure what's going on here either...
            # [LL-2023.02.29]
            _dict_resources = _dict.get('resources')
            for resource in _dict_resources:
                if uri := resource.get('format'):
                    if label := VocabularyReader.get_label(
                            vocabulary='iana_media_type', uri=uri, language=lang_code
                    ):
                        resource['format'] = label

        return search_results





    # ------------- IBlueprint ---------------#
    
    def _get_territoires(self):
        return {
            'territoires': VocabularyReader.fetch_labels(
                vocabulary='ecospheres_territory',
                add_count=True
            )
        }
               
    def _get_themes(self):
        return VocabularyReader.fetch_hierarchized_data(
            vocabulary='ecospheres_theme',
            children_alias='child'
        )
    
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
            ('/api/territoires', 'get_territoires', self._get_territoires),
        #     ('/api/territoires_hierarchy', 'get_territoires_hierarchy', self._get_territoires_hierarchy),
            ('/api/themes', 'get_themes', self._get_themes),
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

def _extract_pattern(pattern, string):
    # TODO: single pass?
    matches = re.findall(pattern, string)
    out = re.sub(pattern, '', string).strip() if matches else string
    return matches, out

def _map_to_uris(values, vocab, get_children=False):
    uris = []
    for val in values:
        label = parse.unquote_plus(val)
        uri = VocabularyReader.get_uri_from_label(vocabulary=vocab, label=label)
        if uri:
            uris.append(uri)
    if get_children:
        uris += VocabularyReader.get_children(vocabulary=vocab, uri=uris)
    return uris

def _solr_or(field, values):
    quoted = [f'"{v}"' for v in values]
    val = ' OR '.join(quoted)
    if len(quoted) > 1:
        val = f'({val})'
    query = f'+{field}:{val}'
    return query
