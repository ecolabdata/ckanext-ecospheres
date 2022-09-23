## DCAT

1. **dataset/**:contains the business logic to parse the metadata of an RDF dataset into a JSON dictionary.
    - **parse_dataset.py**: parse a dataset in RDF format into a dictionary.
    - **_fuction.py**: contains the parsing fuctions


1. **graph/**: contains the business logic to expose a dataset in DCAT format.
    - **graph_from_dataset.py**: expose a dataset in RDF format.
    - **graph_from_catalog.py** : expose a catalog in RDF format. 
    - **_functions.py**:  contains the exposure fuctions
