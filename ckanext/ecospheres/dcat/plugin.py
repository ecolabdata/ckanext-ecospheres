import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.ecospheres.validators as v
import ckanext.ecospheres.helpers as helpers


class DcatFrenchPlugin(plugins.SingletonPlugin):
    # Declare that this class implements IConfigurer.
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)
    # IConfigurer

    
    def get_helpers(self):
        '''Register the functions above as a template
        helper functions.
        '''
        return {
                'fr_dcat_json_string_to_object_aggregated_ressources':helpers.json_string_to_object_aggregated_ressources,
                'fr_dcat_aggregated_package_name_to_title':helpers.aggregated_package_name_to_title,
                'get_localized_value_for_display':helpers.get_localized_value_for_display,
                'get_localized_date':helpers.get_localized_date,
                }

    
    # IValidators
    def get_validators(self):
        return {
            'timestamp_to_datetime': v.timestamp_to_datetime,
            'multilingual_text_output': v.multilingual_text_output,
        }