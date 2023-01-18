import logging

from ckan.model import GroupExtra, Group,Session as Session_CKAN
from ckanext.ecospheres.maps import TYPE_ADMINISTRATION

logger = logging.getLogger(__name__)

def organizations_by_admin_type():
    """Return organization metadata, grouping organizations by administration type

    Returns
    -------
    dict
        {
            "administration_type_label": {
                "count": -1, 
                "orgs":
                    [
                        {
                            "Courriel": "ddtm@gard.gouv.fr", 
                            "Site internet": "homepage"
                            "Territoire": "Territory", 
                            "Type": "admin_type", 
                            "Téléphone": "04 66 62 62 00", 
                            "count": -1, 
                            "created": "Thu, 22 Sep 2022 13:34:17 GMT", 
                            "description": "description",
                            "image_url": "image_url", 
                            "name": "organisation_name", 
                            "title": "organisation_title"
                        },
                        ...
                        ...                                           
                    ]
            },
            ......
            ......
        }

    """
    try:
        list_of_organizations_as_dict=dict()
        organizations_as_dict=dict()
    
        groups = Session_CKAN.query(Group).filter_by(state='active').all()

        if not groups:
            return {"message":"Liste des organisations vide"} 
        for group in groups:
            organizations_as_dict.setdefault(group.id,{})
            organizations_as_dict[group.id]["name"] = group.name
            organizations_as_dict[group.id]["title"] = group.title
            organizations_as_dict[group.id]["description"] = group.description
            organizations_as_dict[group.id]["created"] = group.created
            organizations_as_dict[group.id]["image_url"] = group.image_url
            organizations_as_dict[group.id]["count"] = -1

        groups_details = Session_CKAN.query(GroupExtra).all()

        for group_details in groups_details:
            if group_details.group_id not in organizations_as_dict:
                continue
            organizations_as_dict[group_details.group_id][group_details.key] = group_details.value

        for org in organizations_as_dict:
            list_of_organizations_as_dict.setdefault(TYPE_ADMINISTRATION[organizations_as_dict[org]['Type']],{})
            list_of_organizations_as_dict[TYPE_ADMINISTRATION[organizations_as_dict[org]['Type']]].setdefault("orgs",[])
            list_of_organizations_as_dict[TYPE_ADMINISTRATION[organizations_as_dict[org]['Type']]]["orgs"].append(organizations_as_dict[org])
            list_of_organizations_as_dict[TYPE_ADMINISTRATION[organizations_as_dict[org]['Type']]]["count"] = -1

        return list_of_organizations_as_dict
    
    except Exception as e:
        logger.error('Failed to create organizations view'.format(str(e)))
        return {}
