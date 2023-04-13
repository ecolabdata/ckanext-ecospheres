
import  ckan.plugins.toolkit as toolkit

class EcospheresAccessor(type):
    def __getattr__(self, name):
        schema = toolkit.get_action('scheming_dataset_schema_show')(
            None, {'type': 'dataset'}
        )
        setattr(self, name, schema)
        return schema

class EcospheresSchemas(metaclass=EcospheresAccessor):
    '''Access to cached metadata schemas.
    
    The schema for a given type can be accessed by 
    calling the class attribute named after this 
    type.

    For datasets:
        >>> EcospheresSchemas.dataset
    
    '''
