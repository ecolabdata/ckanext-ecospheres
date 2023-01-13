#!/usr/bin/env python3
import click
from ckanext.ecospheres.vocabulary.loader import load_vocab

@click.group(short_help=u"ckanext-ecospheres commands")
def ecospheres():
    pass

def get_commands():
    return [ecospheres]

@ecospheres.command()
@click.option('name', required=False)
def load_vocab(name):
    '''Load vocabularies into CKAN database.

        >>> ckan -c ckan.ini ecospherefr load-vocab
    
    Parameters
    ----------
    name : str, optional
        Name of one vocabulary to load into the database, ie its
        ``name`` property in ``vocabularies.yaml``.
        If not provided, all available vocabularies are loaded.

    '''
    click.secho('Loading vocabularies...', fg=u"green")
    load_vocab(vocab_list=name)
    click.secho('Vocabularies loaded', fg=u"green")
