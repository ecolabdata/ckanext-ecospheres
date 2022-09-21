#!/usr/bin/env python3
import click
import logging
from os.path import exists
from pathlib import Path
from ckanext.ecospheres.vocabulary.loader import load_vocab as load_all_vocab

log = logging.getLogger(__name__)


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

@click.group()
def ecospherefr():
    """
        empty
    """
    pass

def get_commands():
    return [ecospherefr]


@ecospherefr.command()
def load_vocab():
    log.info("Loading vocabularies...")
    load_all_vocab()



@ecospherefr.command()
@click.pass_context
def test(ctx):
    click.secho('Loading vocabularies...', fg=u"green")
    load_all_vocab()
    

@ecospherefr.command()
@click.option('-f', "--filename", required=False, help='Path to a file', type=str)
def load_file(filename):
    print("filename: ",filename)
    