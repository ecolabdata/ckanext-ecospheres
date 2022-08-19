"""Utilitary functions for vocabulary parsing."""

import requests
from rdflib import (
    Graph, URIRef, Literal, SKOS, RDF, RDFS,
    DCTERMS as DCT, FOAF
)

LABELS_ARE_VALUES_OF = [
    SKOS.prefLabel, DCT.title, RDFS.label, FOAF.name,
    SKOS.altLabel, DCT.identifier, SKOS.notation
]
"""Ordered list of RDF properties that might provide a label.

The order of the list is the order the properties
will be considered when the vocabulary is parsed. Once one
of these was found, the value is used as label, any other
would provide an alternative label. 

"""

CONCEPTS_ARE_SUBJECTS_OF = (
    SKOS.inScheme, SKOS.topConceptOf, SKOS.broader, SKOS.narrower
)
"""RDF properties whose subjects are concepts.

An URI will be identified as a skos:Concept if it is the subject
of a triple whose predicate is one of these properties.

"""

CONCEPTS_ARE_OBJECTS_OF = (
    SKOS.broader, SKOS.narrower, SKOS.hasTopConcept
)
"""RDF properties whose objects are concepts.

An URI will be identified as a skos:Concept if it is the
object of a triple whose predicate is one of these properties.

"""

def fetch_data(url, format='json', **kwargs):
        """Uses the requests module to get some data.

        This function will raise any possible HTTP error,
        JSON parsing error, etc. so the vocabulary parser can
        either:

        * Log the error (as a critical failure or not).

        * Be assured that some proper data has been
          returned.

        For instance, if getting the data is required
        for the parsing to succeed:

            >>> result = VocabularyParsingResult()
            >>> try:
            ...     data = fetch_data(some_url)
            ... except Exception as error:
            ...     result.exit(error)
            ...     return result

        If the parser has a work around, the error
        will just be logged:

            >>> result = VocabularyParsingResult()
            >>> try:
            ...     data = fetch_data(some_url)
            ... except Exception as error:
            ...     result.log_error(error)

        Parameters
        ----------
        url : str
            The URL to request to.
        format : {'json', 'text', 'bytes'}, optional
            The expected format for the result.
        **kwargs
            Any nammed parameter to pass to the
            :py:func:`requests.get` function.

        Returns
        -------
        dict or list or str or bytes
            The type of the result depends on the
            `format` parameter.

        """
        clean_kwargs = {
            key: value for key, value in kwargs.items()
            if key in (
                'params', 'data', 'json', 'headers', 'cookies',
                'files', 'auth', 'timeout', 'allow_redirects',
                'proxies', 'verify', 'stream', 'cert'
            )
        }

        response = requests.get(url, **clean_kwargs)
        response.raise_for_status()

        if format == 'text':
            return response.text
        
        if format == 'bytes':
            return response.content
        
        return response.json()

class VocabularyGraph(Graph):
    """RDF graph holding vocabulary data."""

    def find_vocabulary_items(self, schemes=None, rdf_types=None):
        """Return a list of all vocabulary items' URIs found in the given graph.
        
        When neither `schemes` nor `rdf_types` is provided,
        the function will consider as a vocabulary item any URI 
        typed as ``skos:Concept``, object of a property listed
        by :py:data:`CONCEPTS_ARE_OBJECTS_OF` or subject of a
        property listed by :py:data:`CONCEPTS_ARE_SUBJECTS_OF`.

        Parameters
        ----------
        graph : rdflib.graph.Graph
            Some RDF graph.
        schemes : list(str or rdflib.term.URIRef), optional
            A list of schemes' URIs. If provided, only the
            concepts from the listed schemes are considered.
        rdf_types : list(str or rdflib.term.URIRef), optional
            A list of RDF classes URIs. If provided, items
            typed as an object of one of those classes will
            be considered as vocabulary items and only them.

        Returns
        -------
        list(rdflib.term.URIRef)

        """
        uris = []
        for uri, p, obj in self:
            if isinstance(uri, URIRef) and not uri in uris and (
                schemes and any(
                    (uri, SKOS.inScheme, URIRef(scheme)) in self
                    for scheme in schemes
                ) and (
                    not rdf_types or any(
                        (uri, RDF.type, URIRef(rdf_type)) in self
                        for rdf_type in rdf_types
                    )
                )
                or not schemes and (
                    not rdf_types and (
                        (uri, RDF.type, SKOS.Concept) in self
                        or any(
                            (uri, predicate, None) in self
                            for predicate in CONCEPTS_ARE_SUBJECTS_OF
                        )
                    )
                    or rdf_types and any(
                        (uri, RDF.type, URIRef(rdf_type)) in self
                        for rdf_type in rdf_types
                    )
                ) 
            ):
                uris.append(uri)
            elif (
                isinstance(obj, URIRef) and not obj in uris and not schemes
                and not rdf_types and any(
                    (None, predicate, obj) in self
                    for predicate in CONCEPTS_ARE_OBJECTS_OF
                )
            ):
                uris.append(obj)
        return uris

    def find_labels(self, uri, languages=None):
        """Return all available labels for given URI.

        Labels are ordered according to the index of the
        properties defining them in the list
        :py:data:`LABELS_ARE_VALUES_OF`.

        Parameters
        ----------
        uri : str or rdflib.term.URIRef
            URI of a vocabulary item.
        languages : list(str or None), optional
            A list of allowed languages for labels. If 
            provided, only labels explicitely tagged with one
            of the languages from the list will be considered.
            To accept labels without a language tag, ``None``
            should be added to the list.

        Returns
        -------
        list(rdflib.term.Literal)

        """
        labels = []
        uri = URIRef(uri)
        for property in LABELS_ARE_VALUES_OF:
            for label in self.objects(uri, property):
                if isinstance(label, Literal) and (
                    not languages or label.language in languages 
                ):
                    labels.append(label)
        return labels

    def find_parents(self, uri):
        """Return all broader concepts for the given URI.
        
        Parameters
        ----------
        uri : str or rdflib.term.URIRef
            URI of a vocabulary item.
        
        Returns
        -------
        list(rdflib.term.URIRef)

        """
        parents = []
        uri = URIRef(uri)
        for parent in self.subjects(SKOS.narrower, uri):
            if isinstance(parent, URIRef) and not parent in parents:
                parents.append(parent)
        for parent in self.objects(uri, SKOS.broader):
            if isinstance(parent, URIRef) and not parent in parents:
                parents.append(parent)
        return parents

