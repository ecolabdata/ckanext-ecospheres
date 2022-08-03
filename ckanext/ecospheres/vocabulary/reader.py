
import re

from rdflib import (
    Graph, URIRef, Literal, BNode, SKOS, RDFS, DCTERMS as DCT, FOAF
)

LABEL_PROPERTIES = [
    SKOS.prefLabel, DCT.title, RDFS.label, FOAF.name,
    SKOS.altLabel, DCT.identifier, SKOS.notation
]
"""Ordered list of properties that might provide a label.

The order of the list is the order the properties
will be considered when getting an item label, looking for
an item matching a label, etc.

"""

def fetch_vocabulary_graph(vocabulary):
    """Provide a vocabulary graph from its name.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    
    Returns
    -------
    rdflib.graph.Graph or None
        The expected graph. ``None`` if the vocabulary
        doesn't exist or is not available.

    """
    # TODO: to be written...
    # The following code is some basic placeholder,
    # to allow testing of the rest of the module.

    t = """
        @prefix skos: <http://www.w3.org/2004/02/skos/core#> .

        <http://publications.europa.eu/resource/authority/language/FRA> a skos:Concept ;
            skos:inScheme <http://publications.europa.eu/resource/authority/language> ;
            skos:notation "fr"^^<http://publications.europa.eu/ontology/euvoc#ISO_639_1> ;
            skos:notation "fra"^^<http://publications.europa.eu/ontology/euvoc#ISO_639_2T> ;
            skos:prefLabel "French"@en,
                "français"@fr .

        <http://publications.europa.eu/resource/authority/language/ENG> a skos:Concept ;
            skos:inScheme <http://publications.europa.eu/resource/authority/language> ;
            skos:prefLabel "English"@en,
                "anglais"@fr .

        <http://publications.europa.eu/resource/authority/language/DEU> a skos:Concept ;
            skos:inScheme <http://publications.europa.eu/resource/authority/language> ;
            skos:prefLabel "German"@en,
                "allemand"@fr .
        """
    return Graph().parse(data=t, format='turtle')

def is_known_uri(vocabulary, uri):
    """Is the URI registered in given vocabulary ?

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    uri : rdflib.term.URIRef or str
        Some URI to test.
    
    Returns
    -------
    bool
        ``True`` if the vocabulary exists, is available and
        contains the URI, else ``False``.
    
    """
    if not vocabulary or not uri:
        return False
    
    vocabulary_graph = fetch_vocabulary_graph(vocabulary)
    if not vocabulary_graph:
        return False
    
    return (URIRef(uri), None, None) in vocabulary_graph

def get_uri_from_label(vocabulary, label, as_rdflib_terms=False,
    case_sensitive=False):
    """Get one URI with matching label in given vocabulary, if any.

    This function will consider most RDF properties used for labels, 
    names, titles, notations, etc.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    label : rdflib.term.Literal or str
        Some label to look up. If provided as a 
        :py:class:`rdflib.term.Literal` object, the
        function will look for an exact match, 
        with the same data type and language. Else
        labels are compared as strings and language
        is not considered.
    as_rdflib_terms : bool, default False
        If ``True``, a :py:class:`rdflib.term.URIRef`
        is returned, else the URI is casted as a string.
    case_sensitive : bool, default False
        If ``True``, the case will be considered when
        testing the labels. This parameter is ignored if the 
        label is provided as a :py:class:`rdflib.term.Literal`
        object.

    Returns
    -------
    str or rdflib.term.URIRef or None
        The first matching URI. ``None`` if the vocabulary
        doesn't exist, is not available or there was
        no match for the label.
    
    """
    if not vocabulary or not label:
        return
    
    vocabulary_graph = fetch_vocabulary_graph(vocabulary)
    if not vocabulary_graph:
        return

    for predicate in LABEL_PROPERTIES:
        if isinstance(label, Literal):
            uris = vocabulary_graph.subjects(predicate, label)
            # to make sure not to return some blank node:
            uris = [u for u in uris if isinstance(u, URIRef)]
            if uris:
                return uris[0] if as_rdflib_terms else str(uris[0])
        else:
            for uri, p, xlabel in vocabulary_graph.triples((None, predicate, None)):
                if (case_sensitive and str(xlabel) == str(label) \
                    or not case_sensitive and str(xlabel).lower() == str(label).lower()) \
                    and isinstance(uri, URIRef):
                    return uri if as_rdflib_terms else str(uri)

def get_uri_from_identifier(vocabulary, identifier, as_rdflib_terms=False,
    case_sensitive=False):
    """Get one URI from the given vocabulary using the identifier as suffix.
    
    In this context, a "suffix" may be the entire URI or
    the ending part of the URI, separated from the first part
    by ``/`` or ``:``. 

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    identifier : str
        Presumed identifier / code of some vocabulary item.
    as_rdflib_terms : bool, default False
        If ``True``, a :py:class:`rdflib.term.URIRef`
        is returned, else the URI is casted as a string.
    case_sensitive : bool, default False
        If ``True``, the case will be considered when
        testing the identifiers.
        
    Returns
    -------
    str or rdflib.term.URIRef or None
        The URI if the vocabulary exists, is
        available, has a base URI (ie a ``base_uri``
        property in ``vocabularies.yaml``) and the resulting
        URI was registered in the vocabulary. Else ``None``.
    
    """
    if not vocabulary or not identifier:
        return
    
    vocabulary_graph = fetch_vocabulary_graph(vocabulary)
    if not vocabulary_graph:
        return
    
    pattern = re.compile(
        '^(.*[/:])?{}$'.format(re.escape(identifier)),
        flags=re.IGNORECASE if not case_sensitive else 0
    )

    for uri, p, o in vocabulary_graph:
        if not isinstance(uri, URIRef):
            continue
        if pattern.search(str(uri)):
            return uri if as_rdflib_terms else str(uri)

def get_triples(vocabulary, subject=None, predicate=None, object=None):
    """List matching triples from given vocabulary.
    
    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    subject : rdflib.term.URIRef or rdflib.term.BNode or str, optional
        The subject of the triples. Strings are casted as URIs.
    predicate : rdflib.term.URIRef or str, optional
        The predicate of the triples. Strings are casted as URIs.
    object : rdflib.term.Identifier or Any, optional
        The object of the triples. Non RDFLib types values are
        brutally casted as Literals.

    Returns
    -------
    list(tuple(rdflib.term.Identifier))

    """
    if not vocabulary:
        return []

    vocabulary_graph = fetch_vocabulary_graph(vocabulary)
    if not vocabulary_graph:
        return []

    triple = (
        subject if isinstance(subject, (None, URIRef, BNode)) else URIRef(subject),
        predicate if isinstance(predicate, (None, URIRef)) else URIRef(predicate),
        object if isinstance(object, (None, URIRef, BNode, Literal)) else Literal(object),
    )

    return vocabulary_graph.triples(triple)

def get_values(vocabulary, subject=None, predicate=None, as_rdflib_terms=False):
    """List matching objects from given vocabulary.
    
    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    subject : rdflib.term.URIRef or rdflib.term.BNode or str, optional
        The subject of the triples. Strings are casted as URIs.
    predicate : rdflib.term.URIRef or str, optional
        The predicate of the triples. Strings are casted as URIs.
    as_rdflib_terms : bool, default False
        If ``True``, the matching objects are returned
        with their original type (subclass of
        :py:class:`rdflib.term.Identifier`), else they are
        casted as standard python objects.

    Returns
    -------
    list

    """
    if not vocabulary:
        return []

    vocabulary_graph = fetch_vocabulary_graph(vocabulary)
    if not vocabulary_graph:
        return []
    
    values = vocabulary_graph.objects(
        subject if isinstance(subject, (None, URIRef, BNode)) else URIRef(subject),
        predicate if isinstance(predicate, (None, URIRef)) else URIRef(predicate)
    )

    if as_rdflib_terms:
        return values
    
    return [v.toPython() for v in values]

def get_value(vocabulary, subject=None, predicate=None, as_rdflib_terms=False):
    """Provide one arbitrary matching object from given vocabulary.
    
    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    subject : rdflib.term.URIRef or rdflib.term.BNode or str, optional
        The subject of the triples. Strings are casted as URIs.
    predicate : rdflib.term.URIRef or str, optional
        The predicate of the triples. Strings are casted as URIs.
    as_rdflib_terms : bool, default False
        If ``True``, the matching object is returned
        with its original type (subclass of
        :py:class:`rdflib.term.Identifier`), else it is
        casted as standard python object.

    Returns
    -------
    Any

    """
    if not vocabulary:
        return []

    vocabulary_graph = fetch_vocabulary_graph(vocabulary)
    if not vocabulary_graph:
        return []
    
    value = vocabulary_graph.value(
        subject if isinstance(subject, (None, URIRef, BNode)) else URIRef(subject),
        predicate if isinstance(predicate, (None, URIRef)) else URIRef(predicate)
    )

    return value if as_rdflib_terms else value.toPython()
