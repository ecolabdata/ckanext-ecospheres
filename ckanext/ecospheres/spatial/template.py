# encoding: utf-8

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.model as model
import os
try:
    import json
except ImportError:
    import simplejson as json


def toobj(term): 
    termj=None
    try:
        termj = json.loads(term)
    except:
        log.debug('Unrecognized JSON %s', term)
    return termj

def package_name_to_title(name):
# converts package's name (aka unique URL identifier) to its title. Returns None if package doesn't exist.
    package = model.Package.by_name(name)
    if package is not None:
        if package.title is not None:
            return package.title
        return name
    return None

def translate_dict(lang):
    print(lang)
    tdir = os.path.dirname(__file__)
    dictname = os.path.join(tdir, "dict/dict."+lang[:2]+".json")
    if not os.path.exists(dictname):
        dictname = os.path.join(tdir, "dict/dict.en.json")
    f = open(dictname, 'r')
    s = f.read()
    f.close()
    j = json.loads(s)
    return j

class FrSpatialTemplate(plugins.SingletonPlugin):
    '''Customization of ckanext-scheming templates.

    '''
    # Declare that this class implements IConfigurer.
    # plugins.implements(plugins.IConfigurer)

    # Declare that this plugin will implement ITemplateHelpers.
    plugins.implements(plugins.ITemplateHelpers)

    # def update_config(self, config):

    #     # Add this plugin's templates dir to CKAN's extra_template_paths, so
    #     # that CKAN will use this plugin's custom templates.
    #     # 'templates' is the path to the templates dir, relative to this
    #     # plugin.py file.
    #     toolkit.add_template_directory(config, 'templates')

    def get_helpers(self):
        '''Register the functions above as a template
        helper functions.
        '''
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {
                'fr_spatial_package_name_to_title': package_name_to_title, 
                'fr_spatial_toobj': toobj, 
                'fr_spatial_translate_dict': translate_dict
               }
