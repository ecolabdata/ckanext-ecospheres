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