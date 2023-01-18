#!/usr/bin/env python3
import click

from ckanext.ecospheres.vocabulary.loader import load_vocab
from ckanext.ecospheres.vocabulary.reader import VocabularyReader

@click.group(short_help=u'Vocabulary administration commands')
def vocabulary():
    pass

def get_commands():
    return [vocabulary]

@vocabulary.command()
def list():
    '''List all known vocabularies, if any.

    '''
    vocabularies = VocabularyReader.list_vocabularies()
    if vocabularies:
        click.secho('\n'.join(vocabularies), fg=u'green')

@vocabulary.command()
@click.argument('name', required=False)
@click.option('--include', multiple=True, help='another vocabulary to load')
@click.option('--exclude', multiple=True, help='a vocabulary not to load')
def load(name=None, include=None, exclude=None):
    '''Load vocabularies into CKAN database.

    To load all vocabularies:

        >>> ckan -c ckan.ini vocabulary load
    
    To load one vocabulary:

        >>> ckan -c ckan.ini vocabulary load ecospheres_theme

    To load several vocabularies:

        >>> ckan -c ckan.ini vocabulary load ecospheres_theme --include ecospheres_territory --include adms_publisher_type
    
    To load all vocabularies but two:

         >>> ckan -c ckan.ini vocabulary load --exclude insee_official_geographic_code --exclude ogc_epsg

    Parameters
    ----------
    name : str, optional
        Name of one vocabulary to load into the database, ie its
        ``name`` property in ``vocabularies.yaml``.
        If not provided, all available vocabularies are loaded.
    include : list(str), optional
        Names of the vocabularies to load. If `name` and
        `include` are used, both will be considered.
    exclude : list(str), optional
        Names of the vocabularies that shall not be loaded.
        If `exclude` is used simultaneously with `name` or
        `include`, it will exclude vocabularies from their
        list.

    '''
    click.secho('Loading vocabularies...', fg=u'green')
    if include:
        include = list(include)
        if name and not name in include:
            include.append(name)
    if exclude:
        exclude = list(exclude)
    report = load_vocab(vocab_list=include or name, exclude=exclude)
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
