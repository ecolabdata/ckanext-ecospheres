import datetime
import json

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

