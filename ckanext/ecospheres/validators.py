import datetime
import json
import re

import ckantoolkit as toolkit

def timestamp_to_datetime(value):
    """
    Returns a datetime for a given timestamp
    """
    try:
        return datetime.datetime.fromtimestamp(int(value)).isoformat()
    except ValueError:
        return False
    
def parse_json(value, default_value=None):
    try:
        return json.loads(value)
    except (ValueError, TypeError, AttributeError):
        if default_value is not None:
            return default_value
        return value

def multilingual_text_output(value):
    """
    Return stored json representation as a multilingual dict, if
    value is already a dict just pass it through.
    """
    if isinstance(value, dict):
        return value
    return parse_json(value)


date_regexp = re.compile(
        '^-?([1-9][0-9]{3,}|0[0-9]{3})'
        '-(0[1-9]|1[0-2])'
        '-(0[1-9]|[12][0-9]|3[01])'
        r'(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?$'
    )
datetime_regexp = re.compile(
        '^-?([1-9][0-9]{3,}|0[0-9]{3})'
        '-(0[1-9]|1[0-2])'
        '-(0[1-9]|[12][0-9]|3[01])'
        r'T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))'
        r'(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?$'
    )
def ecospheres_iso_date_or_datetime(value):
    '''Ensure that value is a proper date or datetime string.

    Time zone fragments are allowed, both for date and datetime.

    The validation uses the regular expressions from the
    W3C XML Schema Definition Language (XSD) 1.1 Part 2: Datatypes.

    '''
    if not value:
        return
    if isinstance(value, (datetime.date, datetime.datetime)):
        value = value.isoformat()
    else:
        value = str(value)
    if re.match(date_regexp, value) or re.match(datetime_regexp, value):
        return value
    else:
        raise toolkit.Invalid(f'Ill-formatted date or datetime object "value"')

def ecospheres_email(value):
    '''Make sure the value is stored with the email namespace.

    No validation is performed here. Use the
    :py:func:`ckan.logic.validators.email_validator` validator
    for this.

    Parameters
    ----------
    value : str
        An email, with or without the 
        ``email:`` namespace prefix.
    
    Returns
    -------
    str
        The email with the ``mailto:``
        namespace prefix.
    
    '''
    # TODO: add validation [LL-2023.04.03]
    if not value or not isinstance(value, str):
        return
    if value.startswith('mailto:'):
        return value
    return f'mailto:{value}'

def ecospheres_email_output(value):
    '''Removes the email namespace prefix.

    Parameters
    ----------
    value : str
        An email, with or without the 
        ``mailto:`` namespace prefix.
    
    Returns
    -------
    str
        The email without the ``mailto:``
        namespace prefix.

    '''
    if not value or not isinstance(value, str):
        return
    if value.startswith('mailto:'):
        return value[7:]
    return value

def ecospheres_phone(value):
    '''Make sure the value is stored with the telephone namespace.

    No validation is performed for now, though
    that would be useful.

    Parameters
    ----------
    value : str
        A phone number, with or without the 
        ``tel:`` namespace prefix.
    
    Returns
    -------
    str
        The phone number with the ``tel:``
        namespace prefix.
    
    '''
    # TODO: add validation and formatting [LL-2023.04.03]
    if not value or not isinstance(value, str):
        return
    if value.startswith('tel:'):
        return value
    return f'tel:{value}'

def ecospheres_phone_output(value):
    '''Removes the telephone namespace prefix.

    Parameters
    ----------
    value : str
        An phone number, with or without the 
        ``tel:`` namespace prefix.
    
    Returns
    -------
    str
        The phone number without the ``tel:``
        namespace prefix.

    '''
    if not value or not isinstance(value, str):
        return
    if value.startswith('tel:'):
        return value[4:]
    return value

def ecospheres_ckan_api_show(key, data, errors, context):
    '''Add the CKAN API request URL to access a dataset metadata.
    
    '''
    if not data.get(key):
        if not data.get(('name',)):
            raise toolkit.Invalid(f'No name to create an API package show request')
        data[key] = toolkit.url_for(
            'api.action', ver=3, logic_function='package_show',
            id=data[('name',)], _external=True
        )
