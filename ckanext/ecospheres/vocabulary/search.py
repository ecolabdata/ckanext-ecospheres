"""
Search functions for vocabulary labels and URIs in the
context of a metadata field.

"""

import logging

import ckan.plugins.toolkit as toolkit

from ckanext.ecospheres.vocabulary.reader import VocabularyReader


logger = logging.getLogger(__name__)

class FieldsVocabularies():
    """Access to the names of the vocabularies to be used for each of the schema's fields."""

    INDEX = {}

    @classmethod
    def load(cls, update=False):
        """Retrieve vocabulary information from the schema.

        Parameters
        ----------
        update : bool, default False
            Unless this is set to ``True``, the method
            won't load the data again if it had been
            collected before.

        """
        if update or not cls.INDEX:
            dataset_schema = toolkit.get_action(
                'scheming_dataset_schema_show'
            )(None, {'type': 'dataset'})
            for field_dict in dataset_schema.get('dataset_fields', []):
                cls._build_index(tuple(), field_dict)
            for field_dict in dataset_schema.get('resource_fields', []):
                cls._build_index(('resource',), field_dict)

    @classmethod
    def _build_index(cls, parent_path, field_dict):
        path = list(parent_path)
        if field_name := field_dict.get('field_name'):
            path.append(field_name)
            path = tuple(path)
        else:
            logger.error(f'Missing "field_name" key for a subfield of "{parent_path}"')
            return
        vocabularies = field_dict.get('vocabularies', [])
        if vocabularies:
            cls.INDEX[path] = vocabularies
        if (
            vocabularies
            and field_name == 'uri'
            and not cls.INDEX.get(parent_path)
        ):
            cls.INDEX[parent_path] = vocabularies
        for subfield in field_dict.get('repeating_subfields', []):
            cls._build_index(path, subfield)

    @classmethod
    def list(cls, field_path):
        """List the field's vocabularies, if any.

        For ``'uri'`` subfields, the vocabularies can also 
        be accessed from the parent's path. For instance, these two
        commands return the same vocabularies:

        >>> FieldsVocabularies.list('resource', 'license', 'uri')
        >>> FieldsVocabularies.list('resource', 'license')

        Parameters
        ----------
        field_path : tuple(str) or str
            The path of the field or subfield in the
            metadata schema. For resource fields, the path
            should begin with the keyword ``'resource'``.
            The ``'uri'`` element at the end of the path can
            be omitted.
            Strings are allowed for single-element paths.
        
        """
        if not field_path:
            logger.error('Missing field path')
            return []
        if isinstance(field_path, str):
            field_path = (field_path,)
        cls.load()
        return cls.INDEX.get(field_path, [])

def search_label(field_path, uri, language=None):
    """Return the preferred label for the given vocabulary URI.
    
    Parameters
    ----------
    field_path : tuple(str)
        The path of the field or subfield in the
        metadata schema. For resource fields, the path
        should begin with the keyword ``'resource'``.
        The ``'uri'`` element at the end of the path can
        be omitted.
        Strings are allowed for single-element paths.
    uri : str
        URI of a vocabulary item.
    language : str, optional
        The language the label should be written in.
    
    Returns
    -------
    str or None

    """
    if not uri:
        return
    
    vocabularies = FieldsVocabularies.list(field_path)
    if not vocabularies:
        return
    
    for vocabulary in vocabularies:
        if label := VocabularyReader.get_label(
            vocabulary, uri, language=language
        ):
            return label

def search_uri(
    field_path, value, check_synonyms=True,
    check_labels=True, check_regexp=True,
    warn_if_not_found=True
):
    """Return a valid vocabulary URI for the value. 

    Parameters
    ----------
    field_path : tuple(str)
        The path of the field or subfield in the
        metadata schema. For resource fields, the path
        should begin with the keyword ``'resource'``.
        The ``'uri'`` element at the end of the path can
        be omitted.
        Strings are allowed for single-element paths.
    value : str
        A value, presumably matching one of the 
        vocabulary items allowed for the field.
    check_synonyms : bool, default True
        If ``True`` and `value` isn't already
        a valid vocabulary URI, the function will
        check if `value` is registerd as a synonym
        URI for any vocabulary item.
    check_labels : bool, default True
        If ``True`` and `value` isn't already
        a valid vocabulary URI or a synonym, the
        function will look for a vocabulary item
        whose label matches `value`.
    check_regexp : bool, default True
        If ``True`` and `value` wasn't identified
        through any of the previous methods, the
        function will look for a match using regular
        expressions.
    warn_if_not_found : bool, default True
        If ``True``, the function will log a warning
        if `value` doesn't match any vocabulary item.
    
    Returns
    -------
    str or None
        
    """
    if not value:
        return

    vocabularies = FieldsVocabularies.list(field_path)
    if not vocabularies:
        logger.warning(
            f"Field '{field_path}' has no associated vocabulary"
        )
        return

    # URI match
    for vocabulary in vocabularies:
        if VocabularyReader.is_known_uri(
            vocabulary, value
        ):
            return value

    # synonym match
    if check_synonyms:
        for vocabulary in vocabularies:
            if uri := VocabularyReader.get_uri_from_synonym(
                vocabulary, value
            ):
                return uri
        
    # label match
    if check_labels:
        for vocabulary in vocabularies:
            if uri := VocabularyReader.get_uri_from_label(
                vocabulary, value
            ):
                return uri

    # regular expression match
    if check_regexp:
        for vocabulary in vocabularies:
            if uris := VocabularyReader.get_uris_from_regexp(
                vocabulary, [value]
            ):
                
                return uris[0]

    if warn_if_not_found:
        logger.warning(
            f"Value '{value}' doesn't match any registered "
            f'vocabulary item for field "{field_path}"'
        )

def search_territory(uri):
    """Return the territory from the ecospheres_territory vocabulary best suited to represent the given URI.

    Parameters
    ----------
    uri : str
        URI of some kind of spatial area.
    
    Returns
    -------
    str
        The identifier of a territory from the ecospheres_territory
        vocabulary.
    
    """
    if not uri:
        return
    
    vocabularies = FieldsVocabularies.list('territory')
    for vocabulary in vocabularies:
        if territory_uri := VocabularyReader.get_ecospheres_territory(
            vocabulary, uri
        ):
            return territory_uri

