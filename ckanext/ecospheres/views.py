import logging

import ckan.plugins.toolkit as toolkit
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
        orgs_dict = {}
        offset = 0
        orgs = []
        while True:
            tp_orgs = toolkit.get_action('organization_list')(
                data_dict={
                    'all_fields': True,
                    'include_extras': True,
                    'include_dataset_count': True,
                    'offset': offset,
                    'limit': 25
                }
            )
            if tp_orgs:
                orgs += tp_orgs
                offset += 25
            else:
                break
        
        if not orgs:
            return {"message": "No active organization"}
            
        for org in orgs:
            org_dict = {}
            org_type = ''
            for prop in (
                'name', 'title', 'description', 'created',
                'image_url', 'package_count'
            ):
                org_dict[prop] = org[prop]
            for extra in org.get('extras', []):
                if extra['key'] == 'Type':
                    org_type = extra['value']
                org_dict[extra['key']] = extra['value']
            org_dict['count'] = -1
            org_type_label = TYPE_ADMINISTRATION.get(org_type, 'Autre')
            orgs_dict.setdefault(org_type_label, {})
            orgs_dict[org_type_label].setdefault('orgs', [])
            orgs_dict[org_type_label]['orgs'].append(org_dict)
            orgs_dict[org_type_label]['count'] = -1

        return orgs_dict
    
    except Exception as e:
        logger.error('Failed to create the view of organizations by administration type. {}'.format(str(e)))
        return {}
