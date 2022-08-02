

# TODO: à remplacer par de vraies fonctions opérationnelles...

def is_known_uri(vocabulary, uri):
    """Is the URI registered in given vocabulary ?

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    uri : str
        Some URI to test.
    
    Returns
    -------
    bool
        ``True`` if the vocabulary exists, is available and
        contains the URI, else ``False``.
    
    """
    return False
    
def get_uri_from_label(vocabulary, label):
    """Get one URI with matching label in given vocabulary, if any.

    This function will consider most RDF properties used for labels, 
    names, titles, notations, etc.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    label : str
        Some label to look up.
    
    Returns
    -------
    str or None
        The first matching URI. ``None`` if the vocabulary
        doesn't exist, is not available or there was
        no match for the label.
    
    """
    # IMPORTANT : skos:notation should be considered (usefull for
    # eu_language at least) !
    return None

def get_uri_from_identifier(vocabulary, identifier):
    """Get the base URI for the vocabulary, if any.
    
    This function will try to build the URI from
    the base URI of the vocabulary (if defined) and the
    identifier, then check if this URI is registered

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    identifier : str
        Presumed identifier of some vocabulary item.
    
    Returns
    -------
    str or None
        The URI if the vocabulary exists, is
        available, has a base URI (ie a ``base_uri``
        property in ``vocabularies.yaml``) and the resulting
        URI was registered in the vocabulary. Else ``None``.
    
    """
    return None

