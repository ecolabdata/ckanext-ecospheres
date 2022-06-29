from .dataset.parse_dataset import parse_dataset as _parse_dataset
from .graph.graph_from_dataset import graph_from_dataset as _graph_from_dataset
from .graph.graph_from_catalog import graph_from_catalog as _graph_from_catalog

from ckanext.dcat.profiles import (
    RDFProfile,
    )
class FranchDCATAPProfile(RDFProfile):
    def parse_dataset(self, dataset_dict, dataset_ref):
        return _parse_dataset(self, dataset_dict, dataset_ref)
 
    def graph_from_dataset(self, dataset_dict, dataset_ref):
        return _graph_from_dataset(self, dataset_dict, dataset_ref)

    def graph_from_catalog(self, catalog_dict, catalog_ref):
        return  _graph_from_catalog(self, catalog_dict, catalog_ref)