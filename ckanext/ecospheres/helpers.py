import datetime
import logging
import json
import re

from dateutil.parser import parse, ParserError

import ckan.model as model
from ckan.lib.helpers import lang
from ckan.lib.helpers import *
from ckan.lib.formatters import localised_nice_date

from ckanext.ecospheres.vocabulary.reader import VocabularyReader
from ckanext.ecospheres.maps import TYPE_ADMINISTRATION

logger = logging.getLogger(__name__)

LANGUAGES = {'fr', 'en'}

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
    try:
        territories = json.loads(raw_territories)
    except Exception as e:
        logger.error(
            'Failed to parse territories "{0}". {1}'.format(raw_territories, str(e))
        )
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

    if repeating_subfields_dict:=data.get("repeating_subfields",None):
        

        subfields_as_dict={
            item["field_name"]: item for item in repeating_subfields_dict
        }

        if field_dict:=subfields_as_dict.get(subfield,None):
            return field_dict.get("vocabularies",None)
    return None

def get_vocabulairies_for_given_fields(data):

    if vocabularies:=data.get("vocabularies",None):
        return vocabularies

def get_vocab_label_by_uri_from_list_of_vocabularies(vocabs,uri,lang=None):
    for voc in vocabs:
        if voc_label:=get_vocabulary_label_by_uri(voc,uri,lang=lang):
            return voc_label
    return uri

