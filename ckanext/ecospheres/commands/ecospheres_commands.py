#!/usr/bin/env python3
import click
from ckanext.ecospheres.vocabulary.loader import load_vocab as load_all_vocab


@click.group()
def ecospherefr():
    """
        empty
    """
    pass

def get_commands():
    return [ecospherefr]


'''

Chargement des vocabulaires en base de données:

`ckan -c ckan.ini ecospherefr load-vocab`

'''
@ecospherefr.command()
def load_vocab():
    click.secho('Loading vocabularies...', fg=u"green")
    load_all_vocab()
    click.secho('Vocabularies loaded', fg=u"green")
    

    