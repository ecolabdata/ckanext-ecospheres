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
@click.option('--name_vocab', required=False, help=f'Retained for backward compatibility')

def load_vocab(name_vocab):
    click.secho('Loading vocabularies...', fg=u"green")
    click.secho(name_vocab, fg=u"green")
    load_all_vocab(vocab_list=[])
    click.secho('Vocabularies loaded', fg=u"green")
    


    