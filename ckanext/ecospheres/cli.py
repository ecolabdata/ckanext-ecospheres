#!/usr/bin/env python3
import click
from ckanext.ecospheres.vocabulary.loader import load_vocab

@click.group(short_help=u"Vocabulary administration commands")
def vocabulary():
    pass

def get_commands():
    return [vocabulary]

@vocabulary.command()
@click.argument('name', required=False)
def load(name=None):
    '''Load vocabularies into CKAN database.

    To load all vocabularies:

        >>> ckan -c ckan.ini vocabulary load
    
    To load one vocabulary:

        >>> ckan -c ckan.ini vocabulary load ecospheres_theme
    
    Parameters
    ----------
    name : str, optional
        Name of one vocabulary to load into the database, ie its
        ``name`` property in ``vocabularies.yaml``.
        If not provided, all available vocabularies are loaded.

    '''
    click.secho('Loading vocabularies...', fg=u'green')
    report = load_vocab(vocab_list=name)
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
