
from builtins import object
from yaml import load, Loader
from pathlib import Path
from ckanext.ecospheres.scheming import __path__ as scheming_path

def _get_schema(schema_name):
    path = Path(scheming_path[0]) / f'{schema_name}.yaml'
    with open(path, 'r') as src:
        return load(src.read(), Loader)

class TestEcospheresDatasetSchema(object):

    def test_load_ecospheres_dataset_schema(self):
        """Vérifie que le schéma des jeux de données est dé-sérialisable."""
        schema = _get_schema('ecospheres_dataset_schema')
        assert 'dataset_fields' in schema

    def test_all_fields_have_names(self):
        """Vérifie que tous les champs ont un nom."""
        schema = _get_schema('ecospheres_dataset_schema')
        for field in schema['dataset_fields']:
            assert field.get('field_name')

    def test_all_fields_have_french_and_english_labels(self):
        """Vérifie que tous les champs ont un libellé français et anglais."""
        schema = _get_schema('ecospheres_dataset_schema')
        fields = schema['dataset_fields'] + schema['resource_fields']
        while fields:
            field = fields.pop()
            labels = field.get('label')
            assert isinstance(labels, dict), field.get('field_name')
            assert 'fr' in labels, field.get('field_name')
            assert 'en' in labels, field.get('field_name')
            if 'repeating_subfields' in field:
                fields += field['repeating_subfields']

    def test_all_fields_have_value_type(self):
        """Vérifie que tous les champs ont un type de valeur et qu'il est valide."""
        schema = _get_schema('ecospheres_dataset_schema')
        fields = schema['dataset_fields'] + schema['resource_fields']
        while fields:
            field = fields.pop()
            value_type = field.get('value_type')
            assert value_type in ('literal', 'uri', 'node', 'node or uri'), field.get('field_name')
            if 'repeating_subfields' in field:
                fields += field['repeating_subfields']

    def test_only_literals_are_translatable(self):
        """Vérifie que seuls des champs admettant des valeurs litérales sont marqués comme traduisibles."""
        schema = _get_schema('ecospheres_dataset_schema')
        fields = schema['dataset_fields'] + schema['resource_fields']
        while fields:
            field = fields.pop()
            value_type = field.get('value_type')
            assert value_type == 'literal' or not field.get('translatable_values'), \
                field.get('field_name')
            if 'repeating_subfields' in field:
                fields += field['repeating_subfields']

    def test_only_uris_are_controlled(self):
        """Vérifie que seuls des champs prenant en valeur des URI utilisent un vocabulaire contrôlé."""
        schema = _get_schema('ecospheres_dataset_schema')
        fields = schema['dataset_fields'] + schema['resource_fields']
        while fields:
            field = fields.pop()
            value_type = field.get('value_type')
            assert value_type in ('uri', 'node or uri') or not field.get('known_values'), \
                field.get('field_name')
            if 'repeating_subfields' in field:
                fields += field['repeating_subfields']

    def test_known_values_is_valid(self):
        """Vérifie que les propriétés known_values prennent des valeurs valides."""
        schema = _get_schema('ecospheres_dataset_schema')
        fields = schema['dataset_fields'] + schema['resource_fields']
        while fields:
            field = fields.pop()
            known_values = field.get('known_values')
            assert known_values in (None, 'require', 'allow'), field.get('field_name')
            if 'repeating_subfields' in field:
                fields += field['repeating_subfields']

    def test_know_values_always_comes_with_a_vocabulary(self):
        """Vérifie que la propriété vocabularies liste au moins un vocabulaire quand know_values est présente."""
        schema = _get_schema('ecospheres_dataset_schema')
        fields = schema['dataset_fields'] + schema['resource_fields']
        while fields:
            field = fields.pop()
            vocabularies = field.get('vocabularies')
            assert field.get('known_values') is None or isinstance(vocabularies, list)
            assert field.get('known_values') is None or len(vocabularies) >= 1
            if 'repeating_subfields' in field:
                fields += field['repeating_subfields']

    def test_no_vocabulary_without_know_values(self):
        """Vérifie que la propriété vocabularies n'est présente que conjointement à know_values."""
        schema = _get_schema('ecospheres_dataset_schema')
        fields = schema['dataset_fields'] + schema['resource_fields']
        while fields:
            field = fields.pop()
            vocabularies = field.get('vocabularies')
            assert field.get('known_values') is not None or vocabularies is None
            if 'repeating_subfields' in field:
                fields += field['repeating_subfields']

    def test_all_nodes_have_repeating_subfields(self):
        """Vérifie que tous les champs de type noeud ont des sous-champs."""
        schema = _get_schema('ecospheres_dataset_schema')
        fields = schema['dataset_fields'] + schema['resource_fields']
        while fields:
            field = fields.pop()
            value_type = field.get('value_type')
            assert not value_type in ('node', 'node or uri') \
                or isinstance(field.get('repeating_subfields'), list), \
                field.get('field_name')
            if 'repeating_subfields' in field:
                fields += field['repeating_subfields']

    def test_only_nodes_have_repeating_subfields(self):
        """Vérifie que seuls les champs de type noeud ont des sous-champs."""
        schema = _get_schema('ecospheres_dataset_schema')
        fields = schema['dataset_fields'] + schema['resource_fields']
        while fields:
            field = fields.pop()
            value_type = field.get('value_type')
            assert value_type in ('node', 'node or uri') \
                or not 'repeating_subfields' in field, \
                field.get('field_name')
            if 'repeating_subfields' in field:
                fields += field['repeating_subfields']

    def test_node_or_uri_fields_have_uri_subfield(self):
        """Vérifie que les champs de type noeud ou URI ont un sous-champ uri."""
        schema = _get_schema('ecospheres_dataset_schema')
        fields = schema['dataset_fields'] + schema['resource_fields']
        while fields:
            field = fields.pop()
            value_type = field.get('value_type')
            sfields = field.get('repeating_subfields')
            assert not value_type == 'node or uri' \
                or isinstance(sfields, list) \
                and any(x.get('field_name') == 'uri' for x in sfields), \
                field.get('field_name')
            if sfields:
                fields += sfields


