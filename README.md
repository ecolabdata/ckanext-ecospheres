
# ckanext-ecospheres
CKAN extension for the french minister of ecology  Open Data Portals.


## Contents

- [Overview](#overview)
- [License](#license)
- [Demo Instance](#demo-instance)
- [Requirements](#requirements)
- [Installation](#installation)
- [Development Installation](#development-installation)
- [Running the Tests](#running-the-tests)
- [APIs](#apis)
- [Contributing](#contributing)
- [Support, Communication and Credits](#support-communication-and-credits)


## License

**ckanext-ecospheres** is Free and Open Source software and is licensed under the [GNU Affero General Public License (AGPL) v3.0](http://www.fsf.org/licensing/licenses/agpl-3.0.html).


## Demo Instance

A demo instance can be found [lien vers le guichet de donnnées](http://lien-vers-le-guichet.data.gouv.fr).

## Overview 

Ajouter une desription



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


1. Install the requirements as described [above](#requirements)


2. Activate your CKAN virtual environment, for example:

        . /usr/lib/ckan/default/bin/activate


<br>

3. Go into your CKAN path for extension (like /usr/lib/ckan/default/src):

        cd ckanext-ecospheres    
    
        git clone https://github.com/ecolab/ckanext-ecospheres.git
    
        pip install -e .
    
        pip install -r requirements.txt
    




    
    

<br>

4. Add the required plugins to the ckan.plugins setting in your CKAN config file 
  (by default the config file is located at /etc/ckan/default/production.ini).

    * ecospheres
    * dcat_ecospheres_harvester
    * dcat_ecospheres_plugin
    * spatial_ecospheres_harvester
    * spatial_ecospheres_template

<br>

5. Set the following configuration properties in the production.ini file:

    - Enable de dcatfrench profile: 

            ckanext.dcat.rdf.profiles = euro_dcat_ap fr_dcat_ap
    - Set de DCAT catalog endpoint: 
        
            ckanext.dcat.catalog_endpoint = /dcat/catalog/{_format}

    - Set information about the publisher:

                ckanext.dcatfrench_config.publisher_name = MTE
                ckanext.dcatfrench_config.publisher_mail = mte@gouv.fr
                ckanext.dcatfrench_config.publisher_phone = 015858585858
                ckanext.dcatfrench_config.publisher_url =  mte.gouv.fr
    
    
    - Set the general config
        
            ckan.site_title = Guichet d accès à la donnée du ministère .......
            ckan.site_description = Guichet d accès à la donnée du ministère
            ckan.locale_default = fr
            ckan.locale_order =  fr en
    
    - Set Scheming configuration:
    
            scheming.dataset_schemas = ckanext.ecospheres.scheming:ecospheres_dataset_schema.yaml
            scheming.presets =  ckanext.ecospheres.scheming:presets.yml
                                ckanext.scheming:presets.json
                                ckanext.fluent:presets.json



    - Set spatial 
            ckanext.spatial.harvest.continue_on_validation_errors = True
            ckanext.spatial.common_map.type = custom
            ckanext.spatial.common_map.custom.url = https://wxs.ign.fr/decouverte/geoportail/wmts?service=WMTS&request=GetTile&version=1.0.0&tilematrixset=PM&tilematrix={z}&tilecol={x}&tilerow={y}&layer=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&format=image/png&style=normal
            ckanext.spatial.common_map.attribution = "IGN-F/Géoportail"                                                                                                                                  
            ckan.datasets_per_page = 5     

<br>

5. Enable the dcatfrench profile adding the following configuration property in the production.ini file:

        ckanext.dcat.rdf.profiles = euro_dcat_ap fr_dcat_ap


<br>

6. Configure the CKAN base URI as reported in the [dcat documentation](https://github.com/ckan/ckanext-dcat/blob/master/README.md#uris):

        ckanext.dcat.base_uri = YOUR_BASE_URI

<br>


7. Initialize the vocabularies needed to run the ckanext-ecosphere extension

        ckan --config=/etc/ckan/default/production.ini ecospherefr load-vocab

<br>

8. Update the Solr schema.xml file used by CKAN introducing the following element:
        
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


9. Restart Solr.

<br>

10. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

    sudo service apache2 reload

<br>
<br>


## Development Installation
To install ckanext-ecospheres for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/ecolab/ckanext-ecospheres.git
    cd ckanext-ecospheres
    python setup.py develop
    pip install -r dev-requirements.txt
 
   
    
### Running the Tests                                                                    


       cd /usr/lib/ckan/default/src/ckanext-ecospheres
        . /usr/lib/ckan/default/bin/activate

        pytest --ckan-ini=test.ini --disable-warnings ckanext/ecospheres/tests

## APIs


1. Thèmes
        
        GET /api/themes

1. Territoires

        GET /api/territoires
        GET /api/territoires_hierarchy

1. Organisations
        
        GET /api/organizations


## Contributing

## Support, Communication and Credits