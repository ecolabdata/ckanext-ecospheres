import datetime
import logging
import json
import re

from dateutil.parser import parse, ParserError

import ckan.model as model
from ckan.lib.helpers import lang
from ckan.lib.helpers import *
from ckan.lib.formatters import localised_nice_date

import ckan.plugins.toolkit as toolkit

from ckanext.ecospheres.vocabulary.reader import VocabularyReader
from ckanext.ecospheres.vocabulary.search import search_label
from ckanext.ecospheres.maps import TYPE_ADMINISTRATION

logger = logging.getLogger(__name__)

LANGUAGES = {'fr', 'en'}
TERRITORY = 'Territoire'

def validate_dateformat(date_string, date_format):
    try:
        date = datetime.datetime.strptime(date_string, date_format)
        return date
    except ValueError:
        logger.debug('Incorrect date format {0} for date string {1}'.format(date_format, date_string))
        return None

def json_string_to_object_aggregated_ressources(json_string): 
    try:
        data= json.loads(json_string)
        return data["data"]
    except:
        print('Unrecognized JSON')
        return None

def aggregated_package_name_to_title(row_data):
    name=row_data["identifier"]
    package = model.Package.by_name(name)
    if package is not None:
        if package.title is not None:
            return package.title
        return name
    return None

def get_localized_value_from_dict(value, lang_code, default=''):
    """localizes language dict and
    returns value if it is not a language dict"""
    if not isinstance(value, dict):
        return value
    elif not LANGUAGES.issubset(set(value.keys())):
        return value
    desired_lang_value = value.get(lang_code)
    if desired_lang_value:
        return desired_lang_value
    return localize_by_language_order(value, default)

def get_localized_value_for_display(value):
    lang_code = lang()
    if isinstance(value, dict):
        return get_localized_value_from_dict(value, lang_code)
    try:
        value = json.loads(value)
        return get_localized_value_from_dict(value, lang_code)
    except ValueError:
        return value

def localize_by_language_order(multi_language_field, default=''):
    """localizes language dict if no language is specified"""
    if multi_language_field.get('fr'):
        return multi_language_field['fr']
    elif multi_language_field.get('en'):
        return multi_language_field['en']
    else:
        return default

def get_localized_date(date_string):
    """
    Take a date string and return a localized date, e.g. '24. Juni 2020'.
    `parse` should be able to handle various date formats, including
    DD.MM.YYYY, DD.MM.YYY (necessary for collections with pre-1000 temporals)
    and DD.MM.YY (in this case, it assumes the century isn't specified and
    the year is between 50 years ago and 49 years in the future. This means
    that '01.01.60' => 01.01.2060, and '01.01.90' => 01.01.1990).
    """
    try:
        dt = parse(date_string, dayfirst=True)
        return localised_nice_date(dt, show_date=True, with_hours=False)
    except (TypeError, ParserError):
        return ''

def parse_territories(raw_territories):
    """Take a JSON-encoded list of territories and return a Python list.

    Parameters
    ----------
    raw_territories : str or None
        Presumably a JSON-encoded list of territories.
    
    Returns
    -------
    list
        The parsed list of territories. This will be an
        empty list if the parsing failed for some reason.
    
    """
    if not raw_territories:
        return []
    if isinstance(raw_territories, list):
        return raw_territories
    res = re.match(r'{(.*)}', raw_territories)
    if res:
        resultats = res.group(1)
        return resultats.split(',')
    try:
        territories = json.loads(raw_territories)
    except Exception as e:
        logger.error(
            'Failed to parse territories "{0}". {1}'.format(
                raw_territories, str(e)
            )
        )
        return []
    if isinstance(territories, list):
        return territories
    else:
        return []

def get_territories_label(raw_territories, lang=None):
    territory_codes = parse_territories(raw_territories)
    territory_labels = []
    for territory_code in territory_codes:
        label = VocabularyReader.get_label(
            'ecospheres_territory', uri=territory_code, language=lang
        )
        if label:
            territory_labels.append(label)
    return territory_labels

def get_type_adminstration_label_by_acronym(acronym):
    label = TYPE_ADMINISTRATION.get(acronym, '')
    if not label:
        logger.warning(f'Unknown organization code "{acronym}"')
    return label

def get_vocabulary_label_by_uri(vocabulary,uri,lang=None):
    # TODO: to delete [LL-2023.02.09]
    # use ecospheres_get_vocabulary_label (URI and field name) or
    # VocabularyReader.get_label (URI and vocabulary name) instead
    try:
        label = VocabularyReader.get_label(
            vocabulary=vocabulary, uri=uri, language=lang
        )
        if label:
            return label
        raise ValueError(f'no label available for URI "{uri}"')
    except Exception as e:
        logger.error(f"erreur lors de la recuperation du label du vocabulaire: {vocabulary} -> {str(e)}")
        return None

def get_vocabulairies_for_given_repeating_subfields(data,subfield):
    # TODO: to delete [LL-2023.02.09]

    if repeating_subfields_dict:=data.get("repeating_subfields",None):
        

        subfields_as_dict={
            item["field_name"]: item for item in repeating_subfields_dict
        }

        if field_dict:=subfields_as_dict.get(subfield,None):
            return field_dict.get("vocabularies",None)
    return None

def get_vocabulairies_for_given_fields(data):
    # TODO: to delete [LL-2023.02.09]

    if vocabularies:=data.get("vocabularies",None):
        return vocabularies

def get_vocab_label_by_uri_from_list_of_vocabularies(vocabs,uri,lang=None):
    # TODO: to delete [LL-2023.02.09]
    for voc in vocabs:
        if voc_label:=get_vocabulary_label_by_uri(voc,uri,lang=lang):
            return voc_label
    return uri

def ecospheres_get_vocabulary_label_from_field(field_dict, uri, lang=None):
    '''Get the label of a field's vocabulary term.

    Parameters
    ----------
    field_dict : dict
        Field definition.
    uri : str
        URI of a vocabulary item.
    lang : str
        Preferred language for the label.
    
    Returns
    -------
    str or None

    '''
    vocabularies = field_dict.get('vocabularies')
    known_values = field_dict.get('known_values')
    if vocabularies:
        for vocabulary in vocabularies:
            label = VocabularyReader.get_label(
                vocabulary=vocabulary, uri=uri, language=lang
            )
            if label:
                return label
        if known_values == 'require':
            logger.warning(
                'Unknown vocabulary term for field "{0}": {1}'.format(
                    field_dict.get('field_name'), uri
                )
            )
    return uri

def ecospheres_get_field_dict(field_name, schema, resource_field=False):
    '''Return a field definition from the schema.

    Parameters
    ----------
    field_name : str
        Name of a first level field. 
    schema : dict
        A ckanext-scheming's schema.
    resource_field : bool, default False
        Is the field a resource field or a
        dataset field (default)?
    
    Returns
    -------
    dict or None
        ``None`` if the field doesn't exist.
    
    '''
    if resource_field:
        fields = schema.get('resource_fields', [])
    else:
        fields = schema.get('dataset_fields', [])
    
    for field in fields:
        if field.get('field_name') == field_name:
            return field

def ecospheres_is_empty(data_dict, subfield=None):
    '''Is the subfield value empty?

    Take into account the fact that some metadata are
    stored as dictionaries of translated values.

    Parameters
    ----------
    data_dict : dict
        Metadata dictionary for a field of
        which `subfield` is presumably a subfield.
    subfield : dict, optional
        Subfield definition. If not provided, the function
        will check if `data_dict` itself is empty.

    Returns
    -------
    bool

    '''
    if subfield:
        value = data_dict.get(subfield['field_name'])
    else:
        value = data_dict
    return _is_empty(value)
    
def _is_empty(value):
    if isinstance(value, str):
        return not bool(value)
    elif isinstance(value, dict):
        return all(_is_empty(subvalue) for subvalue in value.values())
    elif isinstance(value, list):
        return all(_is_empty(subvalue) for subvalue in value)
    else:
        return value is None

def ecospheres_get_package_title(name_or_id):
    '''Return the package title if the package exists.

    Parameters
    ----------
    name_or_id : str
        Package name or identifier.
    
    Returns
    -------
    dict or None
        The dictionary holding the title translations.
        ``None`` if the package doesn't exist or (shouldn't
        happen) doesn't have a title.

    '''
    try:
        package_dict = toolkit.get_action('package_show')(
            None, {'id': name_or_id}
        )
        if title_raw := package_dict.get('title'):
            if isinstance(title_raw, str):
                return json.loads(title_raw)
            elif isinstance(title_raw, dict):
                return title_raw
    except:
        return

def ecospheres_retrieve_uri_subfield(subfields, data_dict):
    '''If there is a URI key with a value in the data, return the corresponding subfield info.

    Parameters
    ----------
    subfields : list(dict)
        List of subfields definitions.
    data_dict : dict
        Metadata dictionary, with the values of the
        subfields of said field.
    
    Returns
    -------
    dict or None
        The definition of the subfield holding an URI,
        if any.

    '''
    if 'uri' in data_dict and data_dict['uri']:
        for subfield in subfields:
            if subfield.get('field_name') == 'uri':
                return subfield

def get_org_territories(org_name_or_id):
    '''Return a list of all territories associated to the given CKAN organization.

    Parameters
    ----------
    org_name_or_id : str
        Organization's name or identifier.

    Returns
    -------
    list(str)
        List of territory codes/URIs. This will
        be an empty list if the organization doesn't
        exist or doesn't have any associated territory.

    '''
    org = toolkit.get_action('organization_show')(
        data_dict={
            'id': org_name_or_id,
            'include_extras': True
        }
    )
    if not org or not 'extras' in org:
        return []
    for extra in org['extras']:
        if extra.get('key') == TERRITORY:
            raw_territories = extra.get('value')
            return parse_territories(raw_territories) or [] 
    return []

def ecospheres_get_format(resource_dict, lang=None):
    """Return a format label from media type or other format.

    Parameters
    ----------
    resource_dict : dict
        Resource metadata.
    lang : str, optional
        Preferred language for the label.
    
    Returns
    -------
    str or None

    """
    if media_type_uri := resource_dict.get('media_type'):
        if media_type_label := search_label(
            ('resource', 'media_type'),
            media_type_uri,
            language=lang
        ):
            return media_type_label
    if format := resource_dict.get('other_format'):
        if format_uri := format[0].get('uri'):
            if format_label := search_label(
                ('resource', 'other_format'),
                format_uri,
                language=lang
            ):
                return format_label
        if format_label := format[0].get('label'):
            return format_label

