#!/usr/bin/env python3
import click

from ckanext.ecospheres.vocabulary.loader import load_vocab
from ckanext.ecospheres.vocabulary.reader import VocabularyReader

@click.group(short_help=u'Vocabulary administration commands.')
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
