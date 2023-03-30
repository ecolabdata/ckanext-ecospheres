# encoding: utf-8

from datetime import datetime
from lxml import etree
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.model.package import Package
from ckan.lib.helpers import json

from ckanext.spatial.interfaces import ISpatialHarvester
from ckanext.harvest.harvesters.base import HarvesterBase

from ckanext.ecospheres.spatial.utils import (
    build_dataset_dict_from_schema, bbox_geojson_from_coordinates,
    bbox_wkt_from_coordinates, build_attributes_page_url,
    build_catalog_page_url, extract_scheme_and_identifier,
    getrecordbyid_request, ISO_NAMESPACES
)
from ckanext.ecospheres.spatial.base import MAIN_LANGUAGE
from ckanext.ecospheres.maps import (
    ISO_639_2, DCAT_ENDPOINT_FORMATS, RIGHTS_STATEMENT_MAP,
    LICENSE_MAP, RESTRICTED_ACCESS_URIS, DATA_SERVICES_URIS
)
from ckanext.ecospheres.vocabulary.reader import VocabularyReader
from ckanext.ecospheres.vocabulary.search import (
    search_uri, search_territory
)
from ckanext.ecospheres.helpers import get_org_territories

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = 'fr'
# TODO: la langue par défaut de la fiche de métadonnées devrait plutôt
# être un paramètre de configuration du moissonnage [LL-2023.03.30]

class FrSpatialHarvester(plugins.SingletonPlugin):
    '''Customization of spatial metadata harvest.
    
    See :py:class:`ckanext.spatial.harvesters.base.SpatialHarvester`.
    
    '''

    plugins.implements(ISpatialHarvester, inherit=True)
    
    def get_package_dict(self, context, data_dict):
        '''Add some usefull informations to package metadata dictionnary.
        
        :param context: contains a reference to the model, eg to
            perform DB queries, and the user name used for
            authorization.
        :type context: dict
        :param data_dict: available data. Contains four keys:
            * `package_dict`
               The default package_dict generated by the harvester. Modify this
               or create a brand new one.
            * `iso_values`
               The parsed ISO XML document values. These contain more fields
               that are not added by default to the ``package_dict``.
            * `xml_tree`
               The full XML etree object. If some values not present in
               ``iso_values`` are needed, these can be extracted via xpath.
            * `harvest_object`
               A ``HarvestObject`` domain object which contains a reference
               to the original metadata document (``harvest_object.content``)
               and the harvest source (``harvest_object.source``).
        :type data_dict: dict
        
        :returns: a dataset dict ready to be used by ``package_create`` or
                  ``package_update``
        :rtype: dict
        
        See :py:func:`ckanext.spatial.harvesters.base.SpatialHarvester.get_package_dict`
        and :py:func:`ckanext.spatial.interface.ISpatialHarvester.get_package_dict`.
        
        '''
        package_dict = data_dict['package_dict']
        iso_values = data_dict['iso_values'] 
        xml_tree = data_dict['xml_tree']
        harvest_object = data_dict['harvest_object']

        user_dict = toolkit.get_action('get_site_user')({'ignore_auth': True})
        user = user_dict['name']

        language = iso_values.get('metadata-language') or DEFAULT_LANGUAGE
        if len(language) > 2:
            # if possible (and as expected), the RDF language tag
            # will use the 2 letters ISO language codes instead of
            # the 3 letters ones
            language=ISO_639_2.get(language, language)
        
        dataset_dict = build_dataset_dict_from_schema('dataset', main_language=language)

        # --- various metadata to pick up from package_dict ---
        # < owner_org >
        for target_field, package_field in {
            # dataset_dict key -> package_dict key
            'owner_org': 'owner_org'
        }.items():
            dataset_dict.set_value(target_field, package_dict.get(package_field))

        # --- various metadata to pick up from package_dict's extras ---
        # < graphic_preview >
        extras_map = {
            # ckanext-spatial extras key -> dataset_dict key
            'graphic-preview-file': 'graphic_preview'   
        }
        for elem in package_dict['extras']:
            if elem['key'] in extras_map:
                dataset_dict.set_value(extras_map[elem['key']], elem['value'])

        # --- various metadata to pick up from iso_values ---
        # < name >, < title >, < notes >, < provenance > and < identifier >
        for target_field, iso_field in {
            # dataset_dict key -> iso_values key
            'title_translated': 'title',
            'notes_translated': 'abstract',
            'name': 'guid',
            'provenance': 'lineage',
            'provenance': 'maintenance-note', # TODO: provenance or version_info ? 
            'provenance': 'purpose',
            'identifier': 'unique-resource-identifier'
        }.items():
            dataset_dict.set_value(target_field, iso_values.get(iso_field))
        # NB: package name should always be its guid, for easier
        # handling of packages relationships and duplicate removal

        name = dataset_dict.get('name')
        owner_org = dataset_dict.get('owner_org')

        if not dataset_dict.get_values('title_translated'):
            dataset_dict.set_value(
                'title_translated',
                iso_values.get('alternate-title') or name
            )
        
        dataset_dict.set_value(
            'title',
            dataset_dict.get_values('title_translated', language=MAIN_LANGUAGE) 
        )
        dataset_dict.set_value(
            'notes',
            dataset_dict.get_values('notes_translated', language=MAIN_LANGUAGE) 
        )

        # --- dates ----
        # < created >, < issued >, < modified >
        if iso_values.get('dataset-reference-date'):
            type_date_map = {
                # ISO CI_DateTypeCode -> dataset_dict key
                'creation': 'created',
                'publication': 'issued',
                'revision': 'modified',
            }
            for date_object in iso_values['dataset-reference-date']:
                if (
                    not isinstance(date_object, dict)
                    or not 'type' in date_object
                    or not 'value' in date_object
                ):
                    continue
                if date_object['type'] in type_date_map:
                    dataset_dict.set_value(type_date_map[date_object['type']], date_object['value'])
        
        # < temporal >
        if iso_values.get('temporal-extent-begin') or iso_values.get('temporal-extent-end'):
            temporal_dict = dataset_dict.new_item('temporal')
            temporal_dict.set_value('start_date', iso_values.get('temporal-extent-begin'))
            temporal_dict.set_value('end_date', iso_values.get('temporal-extent-end'))

        # --- organizations ---
        # < rights_holder >, < publisher >, < creator >, < contact_point >
        # and < qualified_attribution >
        if iso_values.get('responsible-organisation'):
            base_role_map = {
                # ISO CI_RoleCode -> dataset_dict key
                'owner': 'rights_holder',
                'publisher': 'publisher',
                'author': 'creator',
                'pointOfContact': 'contact_point'
                }
            org_couples = []
            for org_object in iso_values['responsible-organisation']:
                if not isinstance(org_object, dict):
                    continue
                org_role = org_object.get('role')
                org_name = org_object.get('organisation-name')
                if not org_role or not org_name or (org_role, org_name) in org_couples:
                    continue
                if org_role in base_role_map:
                    org_dict = dataset_dict.new_item(base_role_map[org_role])
                else:
                    continue # TODO: à rendre opérationnel ! [LL-2023.02.28]
                    # erreur : "Only lists of dicts can be placed against subschema
                    # ('qualified_attribution', 0, 'had_role', 0, 'uri')"
                    role_uri = search_uri(
                        ('qualified_attribution', 'had_role'),
                        org_role
                    )
                    if role_uri:
                        qa_dict = dataset_dict.new_item('qualified_attribution')
                        qa_dict.set_value('had_role', role_uri)
                        org_dict = qa_dict.new_item('agent')
                    else:
                        continue
                org_dict.set_value('name', org_name)
                org_couples.append((org_role, org_name))
                contact_info = org_object.get('contact-info')
                if isinstance(contact_info, dict):
                    org_dict.set_value('email', contact_info.get('email'))
                    online_resource = contact_info.get('online-resource')
                    if isinstance(online_resource, dict):
                        org_dict.set_value('url', online_resource.get('url'))
        
        # --- metadata's metadata ---
        # < record_harvested >, < record_modified > and < record_identifier >
        dataset_dict.set_value('record_harvested', datetime.now().astimezone().isoformat())
        dataset_dict.set_value('record_modified', iso_values.get('metadata-date'))
        dataset_dict.set_value('record_identifier', name)

        # < record_language >
        meta_language = iso_values.get('metadata-language')
        if meta_language:
            meta_language_uri =  search_uri('record_language', meta_language)
            if meta_language_uri:
                dataset_dict.set_value('record_language', meta_language_uri)

        # < record_contact_point >
        if iso_values.get('metadata-point-of-contact'):
            for org_object in iso_values['metadata-point-of-contact']:
                if not isinstance(org_object, dict):
                    continue
                org_dict = dataset_dict.new_item('record_contact_point')
                contact_info = org_object.get('contact-info')
                if isinstance(contact_info, dict):
                    org_dict.set_value('email', contact_info.get('email'))
                    online_resource = contact_info.get('online-resource')
                    if isinstance(online_resource, dict):
                        org_dict.set_value('url', online_resource.get('url'))
                    # TODO: le numéro de téléphone n'est pas récupéré dans 'contact-info',
                    # "gmd:phone/gmd:CI_Telephone/gmd:voice/gco:CharacterString/text()"

        # < record_in_catalog >
        catalog_dict = dataset_dict.new_item('record_in_catalog')

        for elem in package_dict['extras']:
        # the following are "default extras" from the
        # harvest source, not harvested metadata
            if elem['key'] == 'catalog_title':
                catalog_dict.set_value('title', elem['value'])

            elif elem['key'] == 'catalog_homepage':
                catalog_dict.set_value('homepage', elem['value'])
        
        # --- references / documentation ---
            # < landing_page >, < attributes_page > and < uri >
            elif elem['key'] == 'catalog_base_url' and name:
                landing_page = build_catalog_page_url(elem['value'], name)
                if landing_page:
                    dataset_dict.set_value('landing_page', landing_page)
                    dataset_dict.set_value('uri', landing_page)
            
            elif elem['key'] == 'attributes_base_url' and name:
                attributes_page = build_attributes_page_url(
                    elem['value'], name
                )
                if attributes_page:
                    dataset_dict.set_value('attributes_page', attributes_page)
        
        # < page >
        # TODO

        # --- themes and keywords ---
        # < category >, < theme > and < free_tags >
        iso_categories = (
            iso_values.get('topic-category', [])
        )
        if iso_categories:
            for iso_category in iso_categories:
                theme_uri =  search_uri('theme', iso_category)
                if theme_uri:
                    dataset_dict.set_value('theme', theme_uri)

        iso_themes = (
            iso_values.get('keyword-inspire-theme', [])
        )
        if iso_themes:
            for iso_theme in iso_themes:
                theme_uri =  search_uri('theme', iso_theme, warn_if_not_found=False)
                if theme_uri:
                    dataset_dict.set_value('theme', theme_uri)
        
        for iso_keyword in iso_values.get('keywords', []):
            if isinstance(iso_keyword, dict):
                dataset_dict.set_value('free_tags', iso_keyword.get('keyword'))

        words = (
            iso_themes + iso_categories
            + dataset_dict.get_values('free_tags')
            + dataset_dict.get_values('title_translated')
        )
        for word in words:
            category_uri = search_uri(
                'category', word, check_regexp=False, warn_if_not_found=False
            )
            # NB: regular expression search is done separately, to retrieve all
            # matches instead of one
            if category_uri:
                dataset_dict.set_value('category', category_uri)                
        category_uris = VocabularyReader.get_uris_from_regexp(
            'ecospheres_theme', words
        )
        if category_uris:
            dataset_dict.set_value('category', category_uris)
        for category_uri in category_uris:
            parent_category_uri = VocabularyReader.get_parents(
                'ecospheres_theme', category_uri
            )
            if parent_category_uri:
                dataset_dict.set_value('category', parent_category_uri)
        # NB: the method makes sure no value is listed
        # more than once, hence not test is necessary here

        # --- spatial coverage ---
        # < bbox > and < spatial >
        iso_bboxes = iso_values.get('bbox', [])
        for iso_bbox in iso_bboxes:
            if isinstance(iso_bbox, dict):
                coordinates = (
                    iso_bbox.get('west'),
                    iso_bbox.get('east'),
                    iso_bbox.get('south'),
                    iso_bbox.get('north')
                )
                if all(coordinate is not None for coordinate in coordinates):
                    wkt = bbox_wkt_from_coordinates(*coordinates)
                    dataset_dict.set_value('bbox', wkt)
                    geojson = bbox_geojson_from_coordinates(*coordinates)
                    dataset_dict.set_value('spatial', geojson)
                    break # other bboxes will be lost

        # < spatial_coverage > and < territory >
        iso_extents = (
            iso_values.get('extent-free-text', [])
            + iso_values.get('extent-controlled', [])
        )
        # extent-controlled is defined in ckanext-spatial's model, but
        # doesn't have any associated search path for now. It's added
        # here in case future updates put it to use.
        
        for iso_extent in iso_extents:

            spatial_coverage_uri = search_uri(
                'spatial_coverage', iso_extent, warn_if_not_found=False
                )
            if spatial_coverage_uri:
                spatial_coverage_dict = dataset_dict.new_item('spatial_coverage')
                spatial_coverage_dict.set_value('uri', spatial_coverage_uri)
                territory = search_territory(spatial_coverage_uri)
                dataset_dict.set_value('territory', territory)
                continue

            extent_scheme, extent_id = extract_scheme_and_identifier(iso_extent)
            if extent_scheme:
                if extent_scheme_uri := search_uri(
                    ('spatial_coverage', 'in_scheme'),
                    extent_scheme
                ):
                    spatial_coverage_dict = dataset_dict.new_item('spatial_coverage')
                    spatial_coverage_dict.set_value('in_scheme', extent_scheme_uri)
                    spatial_coverage_dict.set_value('identifier', extent_id)
                    continue

            # whatever it is, it's not an URI, so should hopefully be readable
            # by a human being.
            spatial_coverage_dict = dataset_dict.new_item('spatial_coverage')
            spatial_coverage_dict.set_value('label', extent_id or iso_extent)

        if not dataset_dict.get_values('territory'):
            # get the territories from the organization
            dataset_dict.set_value(
                'territory',
                get_org_territories(owner_org)
            )

        # --- relations ---
        # < series_member > and < in_series >
        children = iso_values.get('aggregation-info', [])
        children_names = [
            child['aggregate-dataset-identifier']
            for child in children 
            if isinstance(child, dict) and child.get('aggregate-dataset-identifier')
        ]
        if not children_names:
            children_names = xml_tree.xpath(
                'gmd:identificationInfo/gmd:MD_DataIdentification/'
                'gmd:aggregationInfo/gmd:MD_AggregateInformation/'
                'gmd:aggregateDataSetIdentifier/gmd:MD_Identifier/'
                'gmd:code/gco:CharacterString/text()',
                namespaces=ISO_NAMESPACES
            )
        for child_name in children_names:
            # search for the child (which needs to be harvested first,
            # or it won't be possible to update it)
            try:
                child_info = toolkit.get_action('package_show')(None, {'id': child_name})
                child_in_series = child_info.get('in_series', [])
                child_in_series.append({'name': name})
                logger.debug(f'Register series member "{child_name}"')
                toolkit.get_action('package_patch')(
                    {'user': user}, {'id': child_name, 'in_series': child_in_series}
                )
            except Exception as e:
                logger.warning(f'Failed to update series member "{child_name}". {str(e)}')
            series_member = dataset_dict.new_item('series_member')
            series_member.set_value('name', child_name)

        # --- encoded metadata ---
        # < ckan_api_show >
        dataset_dict.set_value(
            'ckan_api_show', toolkit.url_for(
                'api.action', ver=3, logic_function='package_show',
                id=name, _external=True
            )
        )
        # < as_inspire_xml >
        dataset_dict.set_value(
            'as_inspire_xml', getrecordbyid_request(
                harvest_object.source.url,
                name
            )
        )
        # < as_dcat_rdf >
        for dcat_endpoint_format, dcat_endpoint_extension in DCAT_ENDPOINT_FORMATS.items():
            endpoint_dict = dataset_dict.new_item('as_dcat_rdf')
            endpoint_dict.set_value(
                'download_url',
                '{0}.{1}'.format(
                    toolkit.url_for('dataset.read', id=name, _external=True),
                    dcat_endpoint_extension
                )
            )
            format_endpoint_dict = endpoint_dict.new_item('format')
            format_endpoint_dict.set_value('uri', dcat_endpoint_format)

        # --- etc. ---
        # < accrual_periodicity >
        frequency = iso_values.get('frequency-of-update')
        # might either be a code or some label, but codes are
        # stored as alternative labels, so get_uri_from_label
        # will work in both cases
        if frequency_uri := search_uri('accrual_periodicity', frequency):
            dataset_dict.set_value('accrual_periodicity', frequency_uri)

        # < status >
        states = iso_values.get('progress', [])
        # apparently admits more than one value, when DCAT does not
        # only the last valid value will be stored
        for state in states:
            if state_uri := search_uri('status', state):
                dataset_dict.set_value('status', state_uri)

        # < crs >
        crs = iso_values.get('spatial-reference-system')
        if not crs:
            crss = xml_tree.xpath(
                'gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/'
                'gmd:referenceSystemIdentifier/gmd:RS_Identifier/'
                'gmd:code/gmx:Anchor/@xlink:href',
                namespaces=ISO_NAMESPACES
            )
        else:
            crss = crs if isinstance(crs, list) else [crs]
        for crs in crss:
            if crs_uri := search_uri('crs', crs):
                dataset_dict.set_value('crs', crs_uri)

        # < language >
        data_languages = iso_values.get('dataset-language', [])
        if not data_languages:
            data_languages = xml_tree.xpath(
                'gmd:identificationInfo/gmd:MD_DataIdentification/'
                'gmd:language/gco:CharacterString/text()',
                namespaces=ISO_NAMESPACES
            )
        for data_language in data_languages:
            data_language_uri = search_uri('language', data_language)
            dataset_dict.set_value('language', data_language_uri)

        # < access_rights >, < rights >, < restricted_access >
        # and < license_title >
        # theorically, "use-constraints" should match "licences" and "rights",
        # "limitations-on-public-access" and "access-constraints" should
        # match "access_rights", but it's simply not the case. Everything
        # is mixed up.
        resource_license_uri = None
        resource_license_label = None
        restricted_access = False
        registered = False

        rights_statements = (
            iso_values.get('limitations-on-public-access', [])
            + iso_values.get('access-constraints', [])
            + iso_values.get('use-constraints', [])
            + xml_tree.xpath(
                'gmd:identificationInfo/gmd:MD_DataIdentification/'
                'gmd:resourceConstraints/gmd:MD_LegalConstraints/'
                'gmd:useLimitation/gco:CharacterString/text()',
                namespaces=ISO_NAMESPACES
            )
            + xml_tree.xpath(
                'gmd:identificationInfo/gmd:MD_DataIdentification/'
                'gmd:resourceConstraints/*/*/gmx:Anchor/@xlink:href',
                namespaces=ISO_NAMESPACES
            )
        )
        for rights_statement in rights_statements:
            if access_rights_uri := search_uri(
                'access_rights', rights_statement, warn_if_not_found=False
            ):
                access_rights = dataset_dict.new_item('access_rights')
                access_rights.set_value('uri', access_rights_uri)
                registered = True
                if access_rights_uri in RESTRICTED_ACCESS_URIS:
                    restricted_access = True
                break
            elif not resource_license_uri:
                if license_uri := search_uri(
                    'license', rights_statement, warn_if_not_found=False,
                    map=LICENSE_MAP, map_type='all'
                ):
                    dataset_dict.set_value('license', license_uri)
                    resource_license_uri = license_uri
                    registered = True
                    break

            for statement_terms, field in RIGHTS_STATEMENT_MAP.items():
                if all(
                    statement_term.lower() in rights_statement.lower()
                    for statement_term in statement_terms
                ):
                    if field == 'access_rights':
                        access_rights = dataset_dict.new_item('access_rights')
                        access_rights.set_value('label', rights_statement)
                        registered = True
                    elif (
                        field == 'license'
                        and not resource_license_uri
                        and not resource_license_label
                    ):
                        resource_license_label = rights_statement
                        registered = True
                    break
            if not registered:
                dataset_dict.set_value('rights', rights_statement)
            
        dataset_dict.set_value('restricted_access', restricted_access)

        # < conforms_to >
        # ...

        # --- resources ---
        resources_formats = iso_values.get('data-format')
        resources_media_type_uris = []
        resources_format_uris = []
        resources_format_labels = []
        if resources_formats:
            for resource_format in resources_formats:
                if not isinstance(resource_format, dict):
                    continue
                if resource_format_name := resource_format.get('name'):
                    if resource_media_type_uri := search_uri(
                        ('resource', 'media_type'), resource_format_name,
                        warn_if_not_found=False
                    ):
                        resources_media_type_uris.append(resource_media_type_uri)
                    elif resource_format_uri := search_uri(
                        ('resource', 'other_format'), resource_format_name
                    ):
                        resources_format_uris.append(resource_format_uri)
                    else:
                        resources_format_labels.append(resource_format_name)

        for resource_dict in package_dict.get('resources', []):
            # TODO: à compléter ! [LL-2023.02.28]
            resource_url = resource_dict.get('url')
            resource_name = resource_dict.get('name', '')
            if not resource_url:
                continue

            # ATOM
            if 'atom' in resource_url or 'atom' in resource_name:
                atom_resources = []
                atom_uri = search_uri(
                    ('resource', 'service_conforms_to'), DATA_SERVICES_URIS.get('atom')
                )

                for resource_media_type_uri in resources_media_type_uris:
                    resource = dataset_dict.new_resource()
                    resource.set_value('media_type', resource_media_type_uri)
                    atom_resources.append(resource)
                
                for resource_format_uri in resources_format_uris:
                    resource = dataset_dict.new_resource()
                    resource_format = resource.new_item('other_format')
                    resource_format.set_value('uri', resource_format_uri)
                    atom_resources.append(resource)
                
                for resource_format_label in resources_format_labels:
                    resource = dataset_dict.new_resource()
                    resource_format = resource.new_item('other_format')
                    resource_format.set_value('label', resource_format_label)
                    atom_resources.append(resource)
                    
                for resource in atom_resources:
                    resource.set_value('url', resource_url)
                    resource.set_value('download_url', resource_url)
                    resource.set_value('name', resource_name or '?')
                    resource_service = resource.new_item('service_conforms_to')
                    resource_service.set_value('uri', atom_uri)
                    if resource_license_uri or resource_license_label:
                        resource_license = resource.new_item('license')
                        resource_license.set_value('uri', resource_license_uri)
                        resource_license.set_value('label', resource_license_label)

        return dataset_dict.flat()

        # OLD : to be deleted


        # more accommodating resource format identification
        # and droping every 'Unnamed resource'
        format_map = {
            ('wfs', 'wms'): 'WxS',
            ('wxs',): 'WxS',
            ('wfs',): 'WFS',
            ('wms',): 'WMS',
            ('atom',): 'ZIP',
            ('html',): 'HTML',
            ('xml',): 'XML'
            }
        format_map_url = {
            ('mapservwfs?',): 'WFS',
            ('mapserv?',): 'WMS',
            ('atomdataset',): 'ZIP',
            ('atomarchive',): 'ZIP',
            }
        for resource in package_dict['resources'].copy():
            if resource['name'] == toolkit._('Unnamed resource'):
                package_dict['resources'].remove(resource)
                continue
            if not resource['format']:
                for keywords, format_name in format_map.items() :
                    if all(w in resource['name'].lower() for w in keywords):
                        resource['format'] = format_name
                        break
            if not resource['format']:
                for keywords, format_name in format_map_url.items() :
                    if all(w in resource['url'].lower() for w in keywords):
                        resource['format'] = format_name
                        break
        # if len(aggregate_parsed)>0:
        print("package_dict: ",package_dict)
        return package_dict
        

