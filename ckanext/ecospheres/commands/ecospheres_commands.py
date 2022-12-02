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
@click.option('--vocab', required=False, help=f'Nom du vocablaire à charger')

def load_vocab(vocab):
    click.secho('Loading vocabularies...', fg=u"green")
    load_all_vocab(vocab)
    click.secho('Vocabularies loaded', fg=u"green")
    


    