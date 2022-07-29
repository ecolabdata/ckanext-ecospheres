from os.path import exists
import json
from ckanext.ecospheres.models.type_admins import Typeadmins
from  ckanext.ecospheres.commands.utils import _get_file_from_disk
import ckan.plugins as p
from ckan import model
import click
from ckan.model import GroupExtra, Session
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound


DEFAULT_CTX = {'ignore_auth': True}
DEFAULT_ORG_CTX = DEFAULT_CTX.copy()
FILENAME="organizations.json"
DEFAULT_ORG_CTX.update(dict((k, False) for k in ('include_tags',
                                                 'include_users',
                                                 'include_groups',
                                                 'include_extras',
                                                 'include_followers',)))
def _get_organizations_from_file(filename=None):
    return json.loads(_get_file_from_disk(filename))


def _get_user_name(context):
    context['defer_commit'] = True  # See ckan/ckan#1714
    _site_user = p.toolkit.get_action('get_site_user')(context, {})
    return  _site_user['name']




def get_org_context():
    return DEFAULT_ORG_CTX.copy()

def get_organization_by_name(context, name):
    """
    quick'n'dirty way to get organization by rights holder's identifer
    from dcat rdf.
    """
    try:
        ge = Session.query(GroupExtra).filter_by(key='name',
                                                 value=name,
                                                 state='active')\
            .one()
    except MultipleResultsFound:
        raise
    except NoResultFound:
        ge = None
    if ge:
        # safety check
        assert ge.group_id is not None
        ctx = context.copy()
        ctx.update(get_org_context())

        return toolkit.get_action('organization_show')(context=ctx, data_dict={'id': ge.group_id})




def load_organizations(ctx):
    with ctx.meta['flask_app'].test_request_context():
        act = p.toolkit.get_action('organization_create')
        context = {
            'ignore_auth': True
                }
        
        user=_get_user_name(context)
        context["user"]=user
        organizations=_get_organizations_from_file(FILENAME)
        print("len: ",len(organizations))
        for key_org in organizations:
            org_dict=organizations[key_org]
            print("orga_dict: ",org_dict)
            org=get_organization_by_name(ctx,org_dict['name'])
            if org:
                org = act(context=context, data_dict=org_dict)


   
