[![Tests](https://github.com/ecolab/ckanext-ecospheres/workflows/Tests/badge.svg?branch=main)](https://github.com/ecolab/ckanext-ecospheres/actions)






# Installation 

### Création des tables thèmes, sous-thèmes et territoires
```sh 

docker-compose -f docker-compose.dev.yml exec  ckan-dev ckan -c ckan.ini ecospherefr initdb
```

### Chargement des fichiers <i>vocabularies/territoires.json</i> et <i>vocabularies/themes_jsonld.json</i> en base de données.
```sh
docker-compose -f docker-compose.dev.yml exec  ckan-dev ckan -c ckan.ini ecospherefr load-file -t themes
docker-compose -f docker-compose.dev.yml exec  ckan-dev ckan -c ckan.ini ecospherefr load-file -t territory

```

### APIs pour récuperer les themes et territoires:

```
http://ckan-dev:5000/themes
http://ckan-dev:5000/territoires

```











# ckanext-ecospheres

**TODO:** Put a description of your extension here:  What does it do? What features does it have? Consider including some screenshots or embedding a video!


## Requirements

**TODO:** For example, you might want to mention here which versions of CKAN this
extension works with.

If your extension works across different versions you can add the following table:

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.6 and earlier | not tested    |
| 2.7             | not tested    |
| 2.8             | not tested    |
| 2.9             | not tested    |

Suggested values:

* "yes"
* "not tested" - I can't think of a reason why it wouldn't work
* "not yet" - there is an intention to get it working
* "no"


## Installation

**TODO:** Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-ecospheres:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/ecolab/ckanext-ecospheres.git
    cd ckanext-ecospheres
    pip install -e .
	pip install -r requirements.txt

3. Add `ecospheres` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Config settings

None at present

**TODO:** Document any optional config settings here. For example:

	# The minimum number of hours to wait before re-checking a resource
	# (optional, default: 24).
	ckanext.ecospheres.some_setting = some_default_value


## Developer installation

To install ckanext-ecospheres for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/ecolab/ckanext-ecospheres.git
    cd ckanext-ecospheres
    python setup.py develop
    pip install -r dev-requirements.txt


## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## Releasing a new version of ckanext-ecospheres

If ckanext-ecospheres should be available on PyPI you can follow these steps to publish a new version:

1. Update the version number in the `setup.py` file. See [PEP 440](http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers) for how to choose version numbers.

2. Make sure you have the latest version of necessary packages:

    pip install --upgrade setuptools wheel twine

3. Create a source and binary distributions of the new version:

       python setup.py sdist bdist_wheel && twine check dist/*

   Fix any errors you get.

4. Upload the source distribution to PyPI:

       twine upload dist/*

5. Commit any outstanding changes:

       git commit -a
       git push

6. Tag the new release of the project on GitHub with the version number from
   the `setup.py` file. For example if the version number in `setup.py` is
   0.0.1 then do:

       git tag 0.0.1
       git push --tags

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)



## ________________________________________________________________________________________________________________________________

# Ckanext-écospheres



## Requirements

- [CKAN 2.9+](https://github.com/ckan/ckan)
- [ckanext-scheming](https://github.com/ckan/ckanext-scheming)
- [ckanext-spatial](https://github.com/ckan/ckanext-spatial)
- [ckanext-harvest](https://github.com/ckan/ckanext-harvest)
- [ckanext-dcat](https://github.com/ckan/ckanext-dcat)
- [ckanext-hierarchy](https://github.com/ckan/ckanext-hierarchy)
- [ckanext-fluent](https://github.com/ckan/ckanext-fluent)
- [ckanext-scheming](https://github.com/ckan/ckanext-scheming)


## Installation

To install ckanext-ecospheres:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-ecospheres Python package into your virtual environment:

     pip install ckanext-ecospheres

3. Add  ``ecospheres``, ``dcat_ecospheres_harvester``, ``dcat_ecospheres_plugin``, ``spatial_ecospheres_harvester``, ``spatial_ecospheres_template`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/ckan.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload



<br>
<br>




## Config Settings

This extension uses the following config options (<b>ckan.ini</b> file)
    
    #scheming configuration
    scheming.dataset_schemas = ckanext.ecospheres.scheming:ecospheres_dataset_schema.yaml   
    scheming.presets =  ckanext.ecospheres.scheming:presets.yml     
                    ckanext.scheming:presets.json
                    ckanext.fluent:presets.json

    #DCAT configuration
    ckanext.dcat.catalog_endpoint = /dcat/catalog/{_format} 
    #DCAT profil
    ckanext.dcat.rdf.profiles = euro_dcat_ap fr_dcat_ap   

    
    #publisher
    ckanext.dcatfrench_config.publisher_name = MTE
    ckanext.dcatfrench_config.publisher_mail = mte@gouv.fr
    ckanext.dcatfrench_config.publisher_phone = 015858585858
    ckanext.dcatfrench_config.publisher_url =  mte.gouv.fr

    #General config
    ckan.site_title = Guichet d accès à la donnée du ministère de la transition écologique et de la cohésion des territoires
    ckan.site_description = Guichet d accès à la donnée du ministère de la transition écologique et de la cohésion des territoires
    
    #language
    ckan.locale_default = fr  
    ckan.locale_order =  fr en 
    
### Solr config
Add indexed fields to solr <b>schema.xml</b>

    <fields>
        .........
        <field name="page" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="contact_point" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="publisher" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="creator" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="rights_holder" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="qualified_attribution" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="free_tags" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="licenses" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="series_member" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="in_series" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="category" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="territory" type="string" indexed="true" stored="true" multiValued="true"/>
        <field name="modified" type="date" indexed="true" stored="true" multiValued="false"/>
        <field name="created" type="date" indexed="true" stored="true" multiValued="false"/>
        <field name="issued" type="date" indexed="true" stored="true" multiValued="false"/>
        <field name="theme" type="string" indexed="true" stored="true" multiValued="true"/>
        ........
    </fields>



<br>

### Loading vocabularies
    ckan -c ckan.ini ecospherefr load-vocab                                                                                                                                                     