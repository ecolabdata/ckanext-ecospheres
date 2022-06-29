# -*- coding: utf-8 -*-

import os
from datetime import datetime
from pathlib import Path

import nose
import json
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import RDF

try:
    from ckan.tests import helpers
except ImportError:
    from ckan.new_tests import helpers

from ckanext.dcat.processors import RDFParser
from ckanext.dcat.profiles import (DCAT, DCT)

eq_ = nose.tools.eq_
assert_true = nose.tools.assert_true

class BaseParseTest(object):

    def _extras(self, dataset):
        extras = {}
        for extra in dataset.get('extras'):
            extras[extra['key']] = extra['value']
        return extras


        
    def _get_file_contents(self, file_name):
        path = os.path.join(os.path.dirname(__file__),
                            'files',
                            file_name)
        with open(path, 'r') as f:
            return f.read()

class TestFranchDCATAPProfileParsing(BaseParseTest):

    def test_dataset_all_fields(self):

        contents = self._get_file_contents('rdf_dummy.xml')

        p = RDFParser(profiles=['euro_dcat_ap', 'fr_dcat_ap'])

        p.parse(contents)

        datasets = [d for d in p.datasets()]

        eq_(len(datasets), 1)

        dataset = datasets[0]

        # dct:identifier
        eq_(dataset['identifier'], "https://data.statistiques.developpement-durable.gouv.fr/dido/api/harvesting/dcat-ap/id/datasets/610244c9e436671e84ec5da8")
        eq_(dataset['uri'], "https://data.statistiques.developpement-durable.gouv.fr/dido/api/harvesting/dcat-ap/id/datasets/610244c9e436671e84ec5da8")
        
        # dct:title
        eq_(dataset["title"]['fr'],"fr_Données locales de consommation d'électricité, de gaz naturel et de chaleur et de froid - IRIS (à partir de 2018)")
        eq_(dataset["title"]['en'],"en_Données locales de consommation d'électricité, de gaz naturel et de chaleur et de froid - IRIS (à partir de 2018)")



        
        #ct:description
        eq_(dataset['notes']['fr'], "FR Données locales de consommation d'électricité, de gaz naturel et de chaleur et de froid - consommations annuelles et points de livraison d'électricité, de gaz naturel, et de chaleur et de froid, répartis en cinq secteurs (agriculture, industrie, tertiaire, résidentiel et non affecté) ou selon le code NAF à 2 niveaux selon les cas, à la maille IRIS")
        eq_(dataset['notes']['en'], "EN Données locales de consommation d'électricité, de gaz naturel et de chaleur et de froid - consommations annuelles et points de livraison d'électricité, de gaz naturel, et de chaleur et de froid, répartis en cinq secteurs (agriculture, industrie, tertiaire, résidentiel et non affecté) ou selon le code NAF à 2 niveaux selon les cas, à la maille IRIS")
        
        #supprimer fr et en (juste pour demo)
        eq_(dataset['description']['fr'], "FR Données locales de consommation d'électricité, de gaz naturel et de chaleur et de froid - consommations annuelles et points de livraison d'électricité, de gaz naturel, et de chaleur et de froid, répartis en cinq secteurs (agriculture, industrie, tertiaire, résidentiel et non affecté) ou selon le code NAF à 2 niveaux selon les cas, à la maille IRIS")
        eq_(dataset['description']['en'], "EN Données locales de consommation d'électricité, de gaz naturel et de chaleur et de froid - consommations annuelles et points de livraison d'électricité, de gaz naturel, et de chaleur et de froid, répartis en cinq secteurs (agriculture, industrie, tertiaire, résidentiel et non affecté) ou selon le code NAF à 2 niveaux selon les cas, à la maille IRIS")


        """-------------------------------------------<Temporal>-------------------------------------------""" 
        eq_(dataset['temporal'][0]['start_date'], '2020-12-31')
        eq_(dataset['temporal'][0]['end_date'], '2005-01-01')


        """-------------------------------------------< created, modified, issued >-------------------------------------------"""        
        # > dct:modified
        eq_(dataset['modified'],'2022-03-09T09:12:56.785000+00:00')
        
        # > dct:issued
        eq_(dataset['issued'],'2021-07-29T06:03:53.921000+00:00')

        # > dct:created
        eq_(dataset['created'],'2021-07-29T06:02:34.134000+00:00')

        ############################################   Organisations  ############################################

        """-------------------------------------------<contact_point>-------------------------------------------"""        
        # NAME {*} > vcard:fn
        eq_(dataset['contact_point'][0]['name']['fr'],'Point de contact DiDo')
        eq_(dataset['contact_point'][0]['name']['en'],'Point de contact DiDo')
        # EMAIL []
        # > vcard:hasEmail
        eq_(dataset['contact_point'][0]['email'],'ckan@mtes.fr')
        # PHONE []
        # > vcard:hasTelephone
        eq_(dataset['contact_point'][0]['phone'],'0158585858')
        # URL 
        # > vcard:hasURL
        eq_(dataset['contact_point'][0]['url'],'https://statistiques.developpement-durable.gouv.fr/contact')
        
        # AFFILIATION {*}
        # > vcard:organization-name
        eq_(dataset['contact_point'][0]['affiliation']['fr'],'fr_Organisation-Name')
        eq_(dataset['contact_point'][0]['affiliation']['en'],'en_Organisation-Name')


        """-------------------------------------------<creator>-------------------------------------------"""        

        # CREATOR [{}]
        # > dct:creator -> foaf:Organization
        
        # NAME {*}
        # > foaf:name
        eq_(dataset['creator'][0]['name']['fr'],'CGDD/SDES/SDIE/BEM')
        eq_(dataset['creator'][0]['name']['en'],'CGDD/SDES/SDIE/BEM')
        
        # > foaf:mbox
        eq_(dataset['creator'][0]['email'],'ckan@mtes.fr')
        
        # > foaf:workplaceHomepage
        eq_(dataset['creator'][0]['url'],'https://statistiques.developpement-durable.gouv.fr/contact')
        
        eq_(dataset['creator'][0]['title'],"Bureau de l'état des milieux")
        
        # > foaf:phone
        eq_(dataset['creator'][0]['phone'],'0158585858')
        
        # COMMENT {*}
        eq_(dataset['creator'][0]['comment']['fr'],"Bureau de l'état des milieux")
        eq_(dataset['creator'][0]['comment']['en'],"Bureau de l'état des milieux")

        # > org:memberOf [-> org:Organization] / foaf:nam
        eq_(dataset['creator'][0]['affiliation'],'Organisation-Name')




        """-------------------------------------------<rights_holder>-------------------------------------------"""        
        # RIGHTS_HOLDER [{}]
        # dct:rightsHolder -> foaf:Organization


        # NAME {*}
        # > foaf:name
        eq_(dataset['rights_holder'][0]['name']['fr'],'CGDD/SDES/SDIE/BEM')
        eq_(dataset['rights_holder'][0]['name']['en'],'CGDD/SDES/SDIE/BEM')

        # > foaf:mbox
        eq_(dataset['rights_holder'][0]['email'],'ckan@mtes.fr')

        eq_(dataset['rights_holder'][0]['title'],"Bureau de l'état des milieux")

        # > foaf:phone
        eq_(dataset['rights_holder'][0]['phone'],'0158585858')

        # COMMENT {*}
        eq_(dataset['rights_holder'][0]['comment']['fr'],"Bureau de l'état des milieux")
        eq_(dataset['rights_holder'][0]['comment']['en'],"Bureau de l'état des milieux")

        # > foaf:workplaceHomepage
        eq_(dataset['rights_holder'][0]['url'],'https://statistiques.developpement-durable.gouv.fr/contact')
        
        # > org:memberOf [-> org:Organization] / foaf:nam
        eq_(dataset['rights_holder'][0]['affiliation'],'Organisation-Name')



        """-------------------------------------------<publisher>-------------------------------------------"""        
        # PUBLISHER [{}]
        # > dct:publisher -> foaf:Organization
        
        # NAME {*}
        # > foaf:name
        eq_(dataset['publisher'][0]['name']['fr'],'CGDD/SDES/SDIE/BEM')
        eq_(dataset['publisher'][0]['name']['en'],'CGDD/SDES/SDIE/BEM')

        # > foaf:mbox
        eq_(dataset['publisher'][0]['email'],'ckan@mtes.fr')

        eq_(dataset['publisher'][0]['title'],"Bureau de l'état des milieux")

        # > foaf:phone
        eq_(dataset['publisher'][0]['phone'],'0158585858')

        # COMMENT {*}
        eq_(dataset['publisher'][0]['comment']['fr'],"Bureau de l'état des milieux")
        eq_(dataset['publisher'][0]['comment']['en'],"Bureau de l'état des milieux")

        # > foaf:workplaceHomepage
        eq_(dataset['publisher'][0]['url'],'https://statistiques.developpement-durable.gouv.fr/contact')
        
        # > org:memberOf [-> org:Organization] / foaf:nam
        eq_(dataset['publisher'][0]['affiliation'],'Organisation-Name')

        
        """-------------------------------------------<qualified_attribution>-------------------------------------------"""        
        # QUALIFIED_ATTRIBUTION [{}]
        # > prov:qualifiedAttribution -> prov:Attribution
        
        # > dcat:hadRole
        eq_(dataset['qualified_attribution'][0]['had_role'],'owner')
        
        #foaf:givenName
        eq_(dataset['qualified_attribution'][0]['agent'][0]['name'],'mtes')
        #foaf:mbox
        eq_(dataset['qualified_attribution'][0]['agent'][0]['mail'],'ckan@mtes.fr')
        #foaf:homePage
        eq_(dataset['qualified_attribution'][0]['agent'][0]['url'],'mtes.website.com')

        ############################################   Relations  ############################################
        #  in_series et serie_datasets généré par harverster.py.




        ############################################   Références  ############################################
        # > dcat:landingPage
        eq_(dataset['landing_page'],'http://publications.europa.eu/resource/authority/frequency/ANNUAL')

        # ATTRIBUTE_PAGE
        # > foaf:page
        
        #TODO

        """-------------------------------------------<page>-------------------------------------------"""        
        # PAGE [{}]
        # > foaf:page -> foaf:Document
        
        # TITLE {*}
        # > dct:title
        eq_(dataset['page'][0]['title']['fr'], 'Non répondants - collecte électricité 2018 à 2020')
        eq_(dataset['page'][0]['title']['en'], 'Non répondants - collecte électricité 2018 à 2020')
        
        # MODIFIED
        # > dct:modified
        eq_(dataset['page'][0]['modified'],'2021-10-17T17:19:00.965000+00:00')
        
        # DESCRIPTION {*}
        # > dct:description
        eq_(dataset['page'][0]['description']['fr'],'description_fr')
        eq_(dataset['page'][0]['description']['en'],'description_en')
        
        # ISSUED
        # > dct:issued
        eq_(dataset['page'][0]['issued'],'2021-10-19T22:00:00+00:00')
        
        # CREATED
        # > dct:created
        eq_(dataset['page'][0]['created'],'2021-10-17T17:19:00.178000+00:00')

        # > dct:url
        eq_(dataset['page'][0]['url'],'https://data.statistiques.developpement-durable.gouv.fr/dido/api/files/442e60a9-d626-44d2-99ee-57e2f41f90be')
        
        # URI
        eq_(dataset['page'][0]['uri'],'https://data.statistiques.developpement-durable.gouv.fr/dido/api/harvesting/dcat-ap/id/attachments/442e60a9-d626-44d2-99ee-57e2f41f90be')

    
        ############################################   Thèmes et mots clés    ############################################
        """-------------------------------------------<category>-------------------------------------------"""        
        #TODO
        """-------------------------------------------<subcategory>-------------------------------------------"""        
        #TODO

        """-------------------------------------------<theme>-------------------------------------------"""        
        #TODO

        """-------------------------------------------<subject>-------------------------------------------"""        
        #TODO

        """-------------------------------------------<free_tags>-------------------------------------------"""        
        #TODO


        ############################################   Métadonnées sur les métadonnées   ############################################
        
        """-------------------------------------------<is_primary_topic_of>-------------------------------------------"""        
        # IS_PRIMARY_TOPIC_OF [{}]
        # > foaf:isPrimaryTopicOf -> dcat:CatalogRecord
        
        # MODIFIED
        # > dct:modified
        eq_(dataset['is_primary_topic_of'][0]['modified'],'2021-10-17T17:19:00.965000+00:00')
        
        # IDENTIFIER 
        # > dct:identifier
        eq_(dataset['is_primary_topic_of'][0]['identifier'],'https://data.ststiques.developpement-durable.gouv.fr/dido/api/harvesting/dcat-ap/id/datasets/610244c9e436671e84ec5da8')
        
        # LANGUAGE []
        # > dct:language
        eq_(len(dataset['is_primary_topic_of'][0]['language']),3)
        
        # NAME {*}
        # > vcard:fn
        eq_(dataset['is_primary_topic_of'][0]['contact_point'][0]['name']['en'],'Point de contact DiDo')
        eq_(dataset['is_primary_topic_of'][0]['contact_point'][0]['name']['fr'],'Point de contact DiDo')
        
        # EMAIL []
        # > vcard:hasEmail
        eq_(dataset['is_primary_topic_of'][0]['contact_point'][0]['email'],'ckan@mtes.fr')
        
        # PHONE []
        # > vcard:hasTelephone
        eq_(dataset['is_primary_topic_of'][0]['contact_point'][0]['phone'],'0158585858')
    
        # URL 
        # > vcard:hasURL
        eq_(dataset['is_primary_topic_of'][0]['contact_point'][0]['url'],'https://statistiques.developpement-durable.gouv.fr/contact')
        
        # AFFILIATION {*}
        # > vcard:organization-name
        eq_(dataset['is_primary_topic_of'][0]['contact_point'][0]['affiliation']["fr"],'fr_Organisation-Name_pt')
        eq_(dataset['is_primary_topic_of'][0]['contact_point'][0]['affiliation']["en"],'en_Organisation-Name_pt')


        ############################################   Couverture spatiale  ############################################

        """-------------------------------------------<bbox>-------------------------------------------"""        
        
        # BBOX
        # > dct:spatial [-> dct:Location] / dcat:bbox
        eq_(dataset['bbox'],'Ile-de-France')
        
        """-------------------------------------------<spatial_coverage>-------------------------------------------"""        
        # SPATIAL_COVERAGE [{}]
        # > dct:spatial -> dct:Location
    
        # LABEL {*}
        # > skos:prefLabel
        eq_(dataset['spatial_coverage'][0]['label']['fr'], 'fr-label')
        eq_(dataset['spatial_coverage'][0]['label']['en'], 'en-label')
        print(dataset['spatial_coverage'][0])
        eq_(dataset['spatial_coverage'][0]['uri'], 'https://location_ressorce')
        
        # IN_SCHEME
        # > skos:inScheme
        #TODO

        # IDENTIFIER
        # > dct:identifier
        eq_(dataset['spatial_coverage'][0]['identifier'], 'identifier-location')
    
    
        ############################################   Etc. ############################################

        """-------------------------------------------<access_rights>-------------------------------------------"""        
        # ACCESS_RIGHTS [{}]
        # > dct:accessRights -> dct:RightsStatement
        
        # LABEL {*}
        # > rdfs:label
        eq_(dataset['access_rights'][0]['label']['en'],'access_rights_label_en')
        eq_(dataset['access_rights'][0]['label']['fr'],'access_rights_label_fr')
        
        # URI
        eq_(dataset['access_rights'][0]['uri'],"accessRights-uri")   
        
        
        """-------------------------------------------<crs>-------------------------------------------"""        
    
    
        """-------------------------------------------<conforms_to>-------------------------------------------"""        
        # > dct:conformsTo -> dct:Standard
        #   dct:Standard 

        # TITLE {*}
        # > dct:title
        eq_(dataset["conforms_to"][0]['title']["fr"],"title_fr")
        eq_(dataset["conforms_to"][0]['title']["en"],"title_en")

        # URI
        eq_(dataset["conforms_to"][0]['uri'],'conformsTo_Standard-uri')    
        


        """-------------------------------------------<accrual_periodicity>-------------------------------------------"""        
        # ACCRUAL_PERIODICITY
        # > dct:accrualPeriodicity
        assert dataset["accrual_periodicity"]


        """-------------------------------------------<language>-------------------------------------------"""        
        # LANGUAGE []
        # > dct:language
        eq_(len(dataset['language']),2)

        """-------------------------------------------<provenance>-------------------------------------------"""        
        # PROVENANCE [{*}]
        # > dct:provenance [-> dct:ProvenanceStatement] / rdfs:label
        
        eq_(dataset["provenance"]["fr"],"fr_label")
        eq_(dataset["provenance"]["en"],"en_label")


        """-------------------------------------------<version>-------------------------------------------"""        
        # VERSION
        # > owl:versionInfo
        eq_(dataset["version"],"1.0.1")

        """-------------------------------------------<version_notes>-------------------------------------------"""        
        # VERSION_NOTES {*}
        # > adms:versionNotes
        eq_(dataset["version_notes"]["fr"],"version_notes_fr")
        eq_(dataset["version_notes"]["en"],"version_notes_en")



        """-------------------------------------------<temporal_resolution>-------------------------------------------"""        
        # TEMPORAL_RESOLUTION
        # > dcat:temporalResolution
        eq_(dataset["temporal_resolution"],"temporal_resolution")

        """-------------------------------------------<spatial_resolution>-------------------------------------------"""        
        # SPATIAL_RESOLUTION
        # > dcat:spatialResolutionInMeters
        eq_(dataset["spatial_resolution"],"spatial_resolution")
        
        
        
        ############################################   RESOURCES ############################################
        
        """-------------------------------------------<URI>-------------------------------------------"""        
        eq_(dataset["resources"][0]["uri"],"https://data.statistiques.developpement-durable.gouv.fr/dido/api/harvesting/dcat-ap/id/distributions/f88a1c55-0f24-4dac-9ac5-e151caf745e8/spatial/geojson?millesime=2021-10&geoField=IRIS")

        """-------------------------------------------<URL>-------------------------------------------"""        
        eq_(dataset["resources"][0]["url"],'https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/f88a1c55-0f24-4dac-9ac5-e151caf745e8/spatial/geojson?millesime=2021-10&geoField=IRIS')

        """-------------------------------------------<url_download>-------------------------------------------"""        
        eq_(dataset["resources"][0]["url_download"],'https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/f88a1c55-0f24-4dac-9ac5-e151caf745e8/spatial/geojson?millesime=2021-10&geoField=IRIS')

        """-------------------------------------------<description: multilangue>-------------------------------------------"""        
        eq_(dataset["resources"][0]["name"]['fr'],"fr_Données de consommation et de points de livraison d'énergie à la maille IRIS - électricité - année 2020 - millésime 2021-10 - format geojson - Champ IRIS")
        eq_(dataset["resources"][0]["name"]['en'],"en_Données de consommation et de points de livraison d'énergie à la maille IRIS - électricité - année 2020 - millésime 2021-10 - format geojson - Champ IRIS")
        

        """-------------------------------------------< description: multilangue>-------------------------------------------"""        
        eq_(dataset["resources"][0]["description"]['fr'],"fr_description")
        eq_(dataset["resources"][0]["description"]['en'],"en_description")


        """-------------------------------------------<media_type_ressource>-------------------------------------------"""        

        eq_(dataset["resources"][0]["media_type_ressource"][0]['uri'],"https://www.iana.org/assignments/media-types/application/geo+json")
        eq_(dataset["resources"][0]["media_type_ressource"][0]['label']['fr'],"label_fr")
        eq_(dataset["resources"][0]["media_type_ressource"][0]['label']['en'],"label_en")
        
        
        
        """-------------------------------------------<other_format>-------------------------------------------"""        
        eq_(dataset["resources"][0]["other_format"]['label']['fr'],'label_fr')
        eq_(dataset["resources"][0]["other_format"]['label']['en'],'label_en')
        
        """-------------------------------------------<service_conforms_to>-------------------------------------------"""        
        eq_(dataset["resources"][0]["service_conforms_to"]['fr'],'fr_title')
        eq_(dataset["resources"][0]["service_conforms_to"]['en'],'en_title')
        
        
        """-------------------------------------------<rights>-------------------------------------------"""        
        eq_(dataset["resources"][0]["rights"]['label']['fr'],'label_fr')
        eq_(dataset["resources"][0]["rights"]['label']['en'],'label_en')
        
        
        """-------------------------------------------<licenses>-------------------------------------------"""        
        eq_(dataset["resources"][0]["licenses"][0]["label"]['fr'],"label_fr")
        eq_(dataset["resources"][0]["licenses"][0]["label"]['en'],"label_en")
        eq_(dataset["resources"][0]["licenses"][0]["uri"],"https://www.etalab.gouv.fr/licence-ouverte-open-licence")
        eq_(dataset["resources"][0]["licenses"][0]["type"],"type_licence")
        
        
        """-------------------------------------------<resource_issued>-------------------------------------------"""        
        eq_(dataset["resources"][0]["resource_issued"],'2022-03-09T09:12:55.902000+00:00')