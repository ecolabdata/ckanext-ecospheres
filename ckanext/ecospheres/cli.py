#!/usr/bin/env python3
import click

from ckanext.ecospheres.vocabulary.loader import load_vocab
from ckanext.ecospheres.vocabulary.reader import VocabularyReader

@click.group(short_help=u'Vocabulary administration commands.')
def vocabulary():
    pass

def get_commands():
    return [vocabulary]

@vocabulary.command(
    help=u'List the names of all vocabularies available in the CKAN database.',
    short_help=u'List vocabularies.'
)
def list():
    '''List all known vocabularies, if any.

    '''
    vocabularies = VocabularyReader.list_vocabularies()
    if vocabularies:
        click.secho('\n'.join(vocabularies), fg=u'green')

@vocabulary.command(
    help=u'Return a label for the URI.'
)
@click.argument(u'vocabulary')
@click.argument(u'uri')
@click.argument(u'language', required=False)
def label(vocabulary, uri, language):
    '''Return a label for the URI.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    uri : str
        A vocabulary URI.
    language : str, optional
        A language code. If specified, the command will try
        to return a label in that language.

    '''
    label = VocabularyReader.get_label(
            vocabulary, uri, language=language
    )
    click.secho(label or '< No result >', fg=u'green')

@vocabulary.command(
    help=u'Return the URI of a vocabulary item with matching label.',
    short_help=u'Label search.'
)
@click.argument(u'vocabulary')
@click.argument(u'label')
@click.argument(u'language', required=False)
@click.option(
    u'-s', u'--case-sensitive', u'case_sensitive',
    help=u'Use this flag for a case sensitive search.',
    is_flag=True, flag_value=True
)
@click.option(
    u'-a', u'--use-altlabel', u'use_altlabel',
    help=u'Use this flag to include alternative labels.',
    is_flag=True, flag_value=True
)
def lsearch(vocabulary, label, language, case_sensitive, use_altlabel):
    '''Return the URI of a vocabulary item with matching label.

    Basic usage:

        >>> ckan -c ckan.ini vocabulary lsearch ecospheres_theme "Infrastructure portuaire"

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    label : str
        Some label to look up.
    language : str, optional
        A language code. If specified, only labels in that
        specific language are considered.
    case_sensitive : bool, default False
        If ``True``, the case will be considered when
        testing the labels.
    use_altlabel : bool, default False
        Should the method search for a matching alternative
        label if there's no match with the preferred labels?
    
    '''
    uri = VocabularyReader.get_uri_from_label(
        vocabulary=vocabulary,
        label=label,
        language=language,
        case_sensitive=case_sensitive,
        use_altlabel=use_altlabel
    )
    click.secho(uri or '< No result >', fg=u'green')

@vocabulary.command(
    help=u'List the URIs of all vocabulary items whose regular expression matches any of the given terms.',
    short_help=u'Regular expression search.'
)
@click.argument(u'vocabulary')
@click.argument(u'terms', nargs=-1)
def rsearch(vocabulary, terms):
    '''List URIs of all vocabulary items whose regular expression matches any of the given terms.
    
    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.
    terms : str or list(str) or tuple(str)
        Metadata values to test against the regular
        expressions associated with the concepts.
    
    '''
    uris = VocabularyReader.get_uris_from_regexp(
        vocabulary=vocabulary, terms=terms
    )
    if uris:
        click.secho('\n'.join(uris), fg=u'green')
    else:
        click.secho('< No result >', fg=u'green')

@vocabulary.command(
    help=u'Load vocabularies into CKAN database.',
    short_help=u'Load vocabularies.'
)
@click.argument(u'name', required=False, nargs=-1)
@click.option(u'-e', u'--exclude', u'exclude', multiple=True, help=u'A vocabulary not to load.')
def load(name, exclude):
    '''Load vocabularies into CKAN database.

    To load all vocabularies:

        >>> ckan -c ckan.ini vocabulary load
    
    To load some vocabularies:

        >>> ckan -c ckan.ini vocabulary load ecospheres_theme ecospheres_territory
    
    To load all vocabularies but two:

         >>> ckan -c ckan.ini vocabulary load --exclude insee_official_geographic_code --exclude ogc_epsg

    Parameters
    ----------
    name : list(str), optional
        Names of vocabularies to load into the database, ie their
        ``name`` property in ``vocabularies.yaml``.
        If not provided, all available vocabularies are loaded.
    exclude : list(str), optional
        Names of the vocabularies that shall not be loaded.
        If `exclude` is used simultaneously with `name`, it will
        exclude vocabularies from this list.

    '''
    click.secho('Loading vocabularies...', fg=u'green')
    _exclude = []
    if exclude:
        for ex in exclude:
            _exclude.append(ex)
    report = load_vocab(vocab_list=name, exclude=_exclude)
    if not report:
        click.secho('No vocabulary has been loaded', fg=u'green')
    else:
        click.secho('{} vocabular{} been loaded: {}'.format(
                len(report),
                'ies have' if len(report) > 1 else 'y has',
                ', '.join(report)
            ),
            fg=u'green'
        )
