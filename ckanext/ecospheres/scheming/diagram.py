from collections import namedtuple
import yaml
from pathlib import Path
from ckanext.ecospheres.scheming import __path__ as scheming_path

MERMAID_BASE = """

flowchart LR

    classDef tab fill:#fee9e5,stroke:#E4794A
    classDef main fill:#fddede,stroke:#e1000f
    classDef hidden fill:#f3ede5,stroke:#AEA397
    classDef resources fill:#fee7fc,stroke:#A558A0

    classDef node fill:#e9edfe,stroke:#465F9D
    classDef uri fill:#bafaee,stroke:#009081
    classDef nodeOrUri fill:#009099,stroke:#c7f6fc
    classDef literal fill:#feebd0,stroke:#C3992A

"""


class MermaidDiagramElement(tuple):
    """Mermaid diagram element.
    
    This is a tuple of two elements:
    * the parent (mermaid diagram element as well) ;
    * the name of the mermaid diagram element.

    Attributes
    ----------
    kind : str
        The mermaid class of the element, if any.
    label : str
        Label of the element, if any.
    controlled : bool, default False
        ``True`` pour un élément dont les valeurs sont
        contrôlées.
    
    """

    REPEATED_NAMES_INDEX = {}

    TABS = {}

    def __init__(self, definition, label=None, kind=None, controlled=False):
        self.kind = kind
        self.label = label
        self.controlled = controlled

    @property
    def parent(self):
        """MermaidDiagramElement : Parent of the element, if any."""
        return self[0]

    @property
    def name(self):
        """str : Name of the element."""
        return self[1]

    @property
    def level(self):
        """int : Level of the element in the diagram."""
        if self.parent is None:
            return 0
        else:
            return self.parent.level + 1

    def mermaid(self, full=False):
        """Create the mermaid representation of the element.
        
        Parameters
        ----------
        full : bool, default False
            Should be ``True`` when the element is used
            for the first and should be properly definied,
            using its label, kind, etc.

        """
        if full:
            label = self.label or self.name

            if self.level == 0:
                ante, post = '{', '}'
            elif self.level == 1:
                ante, post = '([', '])'
            else:
                ante, post = '[', ']'

            kind = f':::{self.kind}' if self.kind else ''
            pic = f'fa:fa-list ' if self.controlled else ''

            return f'{self.name}{ante}{pic}{label}{post}{kind}'
        else:
            return self.name

    def mermaid_definition(self, full=False, parent_full=False):
        """Create the mermaid representation of the relation between the element and its parent.

        Parameters
        ----------
        full : bool, default False
            Should be ``True`` when the element is used
            for the first and should be properly definied,
            using its label, kind, etc.
        parent_full : bool, default False
            Should be ``True`` when the parent element is used
            for the first and should be properly definied,
            using its label, kind, etc.
        
        """
        indent = self.level * 4 * ' '
        return f'{indent}{self.parent.mermaid(full=parent_full)}-->{self.mermaid(full=full)}'

    @classmethod
    def dataset_element(cls):
        """Create a root mermaid diagram element representing the dataset."""
        return cls.__call__((None, 'dataset'))

    @classmethod
    def tab_element(cls, kind='tab', label=None):
        """Create a mermaid diagram element representing a tab or equivalent.

        Parameters
        ----------
        kind : {'tab', 'main', 'hidden', 'resources'}, optional
            Mermaid class of the tab or similar element.
        label : str, optional
            Tab label. This should be provided if the
            element is a tab. In other cases it will be
            ignored.

        """
        parent = cls.dataset_element()
        if kind == 'tab':
            if label in cls.TABS:
                return cls.TABS[label]
            index = cls.REPEATED_NAMES_INDEX.get('tab', 1) 
            name = f'tab{index}'
            cls.REPEATED_NAMES_INDEX['tab'] = index + 1
            tab = cls.__call__(
                (parent, name), label=label, kind=kind
            )
            cls.TABS[label] = tab
            return tab
        else:
            return cls.__call__((parent, kind), kind=kind)

    @classmethod
    def field_element(cls, parent, name, kind='literal', controlled=False):
        """Create a mermaid diagram element representing a metadata field.

        Parameters
        ----------
        parent : MermaidDiagramElement
            Parent diagram element. This may be a tab or
            another field with subfields.
        name : str
            Field name.
        kind : {'literal', 'node', 'uri', 'nodeOrUri'}, optional
            Mermaid class.
        controlled : bool, default False
            ``True`` if the field's values are controlled.

        """
        index = cls.REPEATED_NAMES_INDEX.get(name, 1) 
        unique_name = f'{name}{index}'
        cls.REPEATED_NAMES_INDEX[name] = index + 1
        return cls.__call__((parent, unique_name), label=name, kind=kind, controlled=controlled)

class DatasetSchemaMermaidDiagram:
    """Access to schema definition and mermaid parsing.

    Parameters
    ----------
    file : str
        Name of a YAML file that should exist
        in the ``ecospheres/scheming`` directory.
    language : str, default 'fr'
        Expected language for labels.

    Attributes
    ----------
    schema : dict
        The YAML schema parsed as python object.
    mermaid : str
        The mermaid representation of the schema.

    """

    RECORDED = []

    def __init__(self, file, language='fr'):

        if not '.' in file:
            file = f'{file}.yaml'
        yaml_path = Path(scheming_path[0]) / file
        if not yaml_path.exists() or not yaml_path.is_file():
            raise FileNotFoundError(f'missing {file} file')
        with open(yaml_path, encoding='utf-8') as src:
            data = yaml.load(src, yaml.Loader)
        self.schema = data
        self.mermaid = MERMAID_BASE

        # pseudo tabs
        main = MermaidDiagramElement.tab_element(kind='main')
        hidden = MermaidDiagramElement.tab_element(kind='hidden')
        resources = MermaidDiagramElement.tab_element(kind='resources')

        # dataset fields and resource fields
        fields = [(field, None) for field in self.schema['dataset_fields']]
        fields.sort(
            key=lambda x: (
                x[0]['tab'].get(language) or x[0]['tab'].get('fr') if 'tab' in x[0] else '',
                x[0].get('display_snippet', 'aucun') is None,
                self.schema['dataset_fields'].index(x[0])
            )
        )
        fields += [(field, resources) for field in self.schema['resource_fields']]
        fields.reverse()
        while fields:
            field, parent = fields.pop()
            if not parent:
                if 'tab' in field:
                    parent = MermaidDiagramElement.tab_element(
                        label=field['tab'].get(language) or field['tab'].get('fr')
                    )
                elif field.get('display_snippet', 'aucun') is None:
                    parent = hidden
                else:
                    parent = main

            kind = 'nodeOrUri' if field['value_type'] == 'node or uri' else field['value_type']
            controlled = field.get('known_values') in ('require', 'allow')
            element = MermaidDiagramElement.field_element(
                parent=parent, name=field['field_name'], kind=kind, controlled=controlled
            )
            self.add(element)
            if 'repeating_subfields' in field:
                fields += [(subfield, element) for subfield in field['repeating_subfields']]

    @classmethod
    def declare(cls, element):
        if not element in cls.RECORDED:
            cls.RECORDED.append(element)
            return True
        return False

    def add(self, element):
        """Add any mermaid element to the diagram.

        Parameters
        ----------
        element : MermaidDiagramElement
            Some mermaid element.
        
        """
        if element.level > 1:
            if not element.parent in DatasetSchemaMermaidDiagram.RECORDED:
                self.add(element.parent)
                DatasetSchemaMermaidDiagram.declare(element.parent)
        full = DatasetSchemaMermaidDiagram.declare(element)
        self.mermaid += element.mermaid_definition(full=full) + '\n'

    def save(self):
        path = Path(scheming_path[0]) / f"{self.schema['dataset_type']}_diagram.md"
        with open(path, 'w', encoding='utf-8') as target:
            target.write(f'```mermaid{self.mermaid}\n```\n')
