#!/usr/bin/env python3
import click
import logging
from  ckanext.ecospheres.commands.territories import load_data_from_file_to_db
from  ckanext.ecospheres.commands.themes import load_themes_from_file_to_db
from  ckanext.ecospheres.commands.administrations_refentiel import load_data_admin
from  ckanext.ecospheres.commands.organisations import load_organizations
from os.path import exists
from pathlib import Path
from ckanext.ecospheres.models.themes import Themes,Subthemes
from ckanext.ecospheres.models.territories import Territories
from ckan.model import Session, meta
from sqlalchemy import Column, Date, Integer, Text, create_engine, inspect
log = logging.getLogger(__name__)


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

# @click.group()
def ecospherefr():
    """
        empty
    """
    pass

def get_commands():
    return [ecospherefr]


# @ecospherefr.command()
def initdb():
    from ckanext.ecospheres.models import setup_db
    created = setup_db()
    if created:
        click.secho('DCATAPIT DB tables created', fg=u"green")
    else:
        click.secho('DCATAPIT DB tables not created', fg=u"yellow")

# @ecospherefr.command()
# @click.pass_context
def test(ctx):
    click.secho('Commande de teste', fg=u"green")
    

# @ecospherefr.command()
# @click.option('-f', "--filename", required=False, help='Path to a file', type=str)
# @click.option('-t', "--type", required=False, help='[territories]', type=str)
def load_file(filename,type):
    if type == "territory":
        load_data_from_file_to_db()
    if type == "themes":
        load_themes_from_file_to_db()
    


