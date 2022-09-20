from builtins import str
from builtins import object
import json
import unittest
import nose

import pytest
from dateutil.parser import parse as parse_date
from dateutil.parser import parse as parse_date
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDFS, RDF, SKOS,XSD
from pathlib import Path
from geomet import wkt
from ckantoolkit.tests import helpers, factories
from ckanext.dcat import utils
from ckanext.dcat.processors import RDFSerializer
from ckanext.dcat.profiles import (DCAT, DCT, ADMS, XSD, VCARD, FOAF, SCHEMA,
                                   SKOS, LOCN, GSP, OWL, SPDX, GEOJSON_IMT)
from ckanext.dcat.utils import DCAT_EXPOSE_SUBCATALOGS
import os
ORG=Namespace("http://www.w3.org/ns/org#")
PROV = Namespace( "http://www.w3.org/ns/prov#")
eq_ = nose.tools.eq_

class BaseSerializeTest(unittest.TestCase):

    def _extras(self, dataset):
        extras = {}
        for extra in dataset.get('extras'):
            extras[extra['key']] = extra['value']
        return extras

    def _triples(self, graph, subject, predicate, _object, data_type=None):

        if not (isinstance(_object, URIRef) or isinstance(_object, BNode) or _object is None):
            if data_type:
                _object = Literal(_object, datatype=data_type)
            else:
                _object = Literal(_object)
        triples = [t for t in graph.triples((subject, predicate, _object))]
        return triples

    def _triple(self, graph, subject, predicate, _object, data_type=None):
        triples = self._triples(graph, subject, predicate, _object, data_type)
        return triples[0] if triples else None






class TestEuroDCATAPProfileSerializeDataset(BaseSerializeTest):
    def _build_graph_and_check_format_mediatype(self, dataset_dict, expected_format, expected_mediatype):
        """
        Creates a graph based on the given dict and checks for dct:format and dct:mediaType in the
        first resource element.

        :param dataset_dict:
            dataset dict, expected to contain one resource
        :param expected_format:
            expected list of dct:format items in the resource
        :param expected_mediatype:
            expected list of dcat:mediaType items in the resource
        """
        s = RDFSerializer(profiles=['euro_dcat_ap', 'fr_dcat_ap'])
        g = s.g

        dataset_ref = s.graph_from_dataset(dataset_dict)

        # graph should contain the expected nodes
        resource_ref = list(g.objects(dataset_ref, DCAT.distribution))[0]
        dct_format = list(g.objects(resource_ref, DCT['format']))
        dcat_mediatype = list(g.objects(resource_ref, DCAT.mediaType))
        assert expected_format == dct_format
        assert expected_mediatype == dcat_mediatype


    def _get_file_contents(self, file_name):
        path = Path(__file__).parent / f"files/{file_name}"
        with open(path, 'r') as f:
            return json.loads(f.read())


    def test_graph_from_dataset(self):
        dataset=self._get_file_contents("json_parsed_result.json")
        s = RDFSerializer()
        g = s.g

        dataset_ref = s.graph_from_dataset(dataset)
        
        assert str(dataset_ref) == utils.dataset_uri(dataset)
        assert self._triple(g, dataset_ref, RDF.type, DCAT.Dataset)

        
        ############################################   Littéraux  ############################################

        
        """ identifier """
        assert self._triple(g, dataset_ref, DCT.identifier, dataset['identifier'])

        """ title """
        notes_list = list(self._triples(g,dataset_ref, DCT.title, None))
        for x in notes_list:
            eq_(dataset['title'][x[-1].language],str(x[-1]))
        
        """ notes """
        notes_list = list(self._triples(g,dataset_ref, DCT.description, None))
        for x in notes_list:
            eq_(dataset['notes'][x[-1].language],str(x[-1]))
        
        """ created """
        assert self._triple(g, dataset_ref, DCT.created, dataset['created'], XSD.dateTime)


        """ modified """
        assert self._triple(g, dataset_ref, DCT.modified, dataset['modified'], XSD.dateTime)


        """ issued """
        assert self._triple(g, dataset_ref, DCT.issued, dataset['issued'], XSD.dateTime)
        
        
        """ landing_page: Cf. Références """
        assert self._triple(g, dataset_ref, DCAT.landingPage, dataset['landing_page'])
        
        
        """   accrual_periodicity"""
        assert self._triple(g, dataset_ref, DCT.accrualPeriodicity, dataset['accrual_periodicity'])
        
        
        """ version """
        assert self._triple(g, dataset_ref,  OWL.versionInfo, dataset['version'])
        
        
        """ temporal_resolution """
        assert self._triple(g, dataset_ref,  DCAT.temporalResolution, dataset['temporal_resolution'])
        
        """ spatial_resolution """
        assert self._triple(g, dataset_ref,  DCAT.spatialResolutionInMeters, dataset['spatial_resolution'])
        
        
        ############################################   Dates  ############################################

        """------------------------------------------<Temporal>------------------------------------------"""

        temporal_dict=dataset["temporal"][0]
        temp_exts = self._triple(g,dataset_ref, DCT.temporal, None)[-1]
        assert self._triple(g, temp_exts, RDF.type, DCT.PeriodOfTime)
        assert self._triple(g, temp_exts, DCAT.startDate,  parse_date(temporal_dict["start_date"]).isoformat(), XSD.dateTime)
        assert self._triple(g, temp_exts, DCAT.endDate,  parse_date(temporal_dict["end_date"]).isoformat(), XSD.dateTime)
        
        ############################################   Organisations  ############################################
        
        """------------------------------------------<Contact_point>------------------------------------------"""
        contact_point_node = self._triple(g, dataset_ref, DCAT.contactPoint, None)[-1]
        assert self._triple(g, contact_point_node, RDF.type, VCARD.Kind)
        contact_point_dict=dataset['contact_point'][0]
        
        # NAME {*}
        # > vcard:fn
        for x in  self._triples(g, contact_point_node, VCARD.fn, None):
            eq_( contact_point_dict["name"][x[-1].language],str(x[-1]))
        
        # EMAIL []
        # > vcard:hasEmail
        assert self._triple(g, contact_point_node, VCARD.hasEmail, contact_point_dict["email"])
        
        # PHONE []
        # > vcard:hasTelephone
        assert self._triple(g, contact_point_node, VCARD.hasTelephone, contact_point_dict["phone"])
        
        # URL 
        # > vcard:hasURL
        assert self._triple(g, contact_point_node, VCARD.hasURL, contact_point_dict["url"])
        
        # AFFILIATION {*}
        # > vcard:organization-name
        for x in  self._triples(g, contact_point_node, VCARD.organization, None):
            eq_( contact_point_dict["affiliation"][x[-1].language],str(x[-1]))

        
    
        """------------------------------------------<Publisher>------------------------------------------"""

        publisher_node = self._triple(g, dataset_ref, DCAT.publisher, None)[-1]
        assert self._triple(g, publisher_node, RDF.type, FOAF.Organization)
        publisher_dict=dataset['publisher'][0]

        # NAME {*}
        # > foaf:name
        for x in  self._triples(g, publisher_node, FOAF.name, None):
            eq_( publisher_dict["name"][x[-1].language],str(x[-1]))

        # TYPE
        # > dct:type
        assert self._triple(g, publisher_node, DCT.type, publisher_dict["type"])
        
        # > foaf:mbox
        assert self._triple(g, publisher_node, FOAF.mbox, publisher_dict["email"])

        # > foaf:phone
        assert self._triple(g, publisher_node, FOAF.phone, publisher_dict["phone"])

        # > foaf:workplaceHomepage
        assert self._triple(g, publisher_node, FOAF.workplaceHomepage, publisher_dict["url"])
        
        
        # > org:memberOf [-> org:Organization] / foaf:name
        affiliation_node = self._triple(g, publisher_node, ORG.memberOf, None)[-1]
        assert affiliation_node
        assert self._triple(g, affiliation_node, RDF.type, ORG.Organization)
        for x in  self._triples(g, affiliation_node, FOAF.name, None):
            eq_( publisher_dict["affiliation"][x[-1].language],str(x[-1]))
        
        """------------------------------------------<Creator>------------------------------------------"""

        creator_node = self._triple(g, dataset_ref, DCAT.creator, None)[-1]
        assert self._triple(g, creator_node, RDF.type, FOAF.Organization)
        creator_dict=dataset['creator'][0]


        # NAME {*}
        # > foaf:name
        for x in  self._triples(g, creator_node, FOAF.name, None):
            eq_( creator_dict["name"][x[-1].language],str(x[-1]))
        
        # TYPE
        # > dct:type
        assert self._triple(g, creator_node, DCT.type, creator_dict["type"])

        # > foaf:mbox
        assert self._triple(g, creator_node, FOAF.mbox, creator_dict["email"])
        
        # > foaf:phone
        assert self._triple(g, creator_node, FOAF.phone, publisher_dict["phone"])
        
        # > foaf:workplaceHomepage
        assert self._triple(g, creator_node, FOAF.workplaceHomepage, creator_dict["url"])
        
        # > org:memberOf [-> org:Organization] / foaf:name
        affiliation_node = self._triple(g, creator_node, ORG.memberOf, None)[-1]
        assert affiliation_node
        assert self._triple(g, affiliation_node, RDF.type, ORG.Organization)
        
        for x in  self._triples(g, affiliation_node, FOAF.name, None):
            eq_( creator_dict["affiliation"][x[-1].language],str(x[-1]))
        
        """------------------------------------------<rightsHolder>------------------------------------------"""

        rightsHolder_node = self._triple(g, dataset_ref, DCAT.rightsHolder, None)[-1]
        assert self._triple(g, rightsHolder_node, RDF.type, FOAF.Organization)
        rightsHolder_dict=dataset['rights_holder'][0]
        
        
        # NAME {*}
        # > foaf:name
        for x in  self._triples(g, rightsHolder_node, FOAF.name, None):
            eq_( rightsHolder_dict["name"][x[-1].language],str(x[-1]))
        
        # TYPE
        # > dct:type
        assert self._triple(g, rightsHolder_node, DCT.type, rightsHolder_dict["type"])
        
        # > foaf:mbox
        assert self._triple(g, rightsHolder_node, FOAF.mbox, rightsHolder_dict["email"])
        
        # > foaf:phone
        assert self._triple(g, rightsHolder_node, FOAF.phone, publisher_dict["phone"])
        
        # > foaf:workplaceHomepage
        assert self._triple(g, rightsHolder_node, FOAF.workplaceHomepage, rightsHolder_dict["url"])
        
        
        # > org:memberOf [-> org:Organization] / foaf:name
        affiliation_node = self._triple(g, rightsHolder_node, ORG.memberOf, None)[-1]
        assert affiliation_node
        assert self._triple(g, affiliation_node, RDF.type, ORG.Organization)
        
        for x in  self._triples(g, affiliation_node, FOAF.name, None):
            eq_( rightsHolder_dict["affiliation"][x[-1].language],str(x[-1]))
        
        
        
        """------------------------------------------<qualifiedAttribution>------------------------------------------"""
        
        # > prov:qualifiedAttribution -> prov:Attribution

        qualified_attribution_node = self._triples(g, dataset_ref, PROV.qualifiedAttribution, None)
        agent_qualified_attribution_dict=dataset["qualified_attribution"]
        for qualified_attribution in qualified_attribution_node:
            qualified_attribution=qualified_attribution[-1]
            assert self._triple(g, qualified_attribution, RDF.type, PROV.Attribution)
            
            # HAD_ROLE [{}]
            # > dcat:hadRole
            for x in  self._triples(g, qualified_attribution, DCAT.hadRole, None):
                assert str(x[-1]) in agent_qualified_attribution_dict[0]['had_role']
        
            
            # AGENT [{}]
            # > prov:agent -> prov:Agent
            agent_qualified_attribution_node = self._triples(g, qualified_attribution, PROV.agent, None)
            for agent in agent_qualified_attribution_node:
                
                agent=agent[-1]
                assert self._triple(g, agent, RDF.type, PROV.Agent)
                
                #foaf:givenName
                for x in  self._triples(g, agent, FOAF.givenName, None):
                    eq_( agent_qualified_attribution_dict[0]['agent'][0]["name"][x[-1].language],str(x[-1]))
        
                #foaf:mbox 
                assert self._triple(g, agent, FOAF.mbox, agent_qualified_attribution_dict[0]['agent'][0]["mail"])
                
                #foaf:homePage
                assert self._triple(g, agent, FOAF.homePage, agent_qualified_attribution_dict[0]['agent'][0]["url"])
                


        ############################################   Relations  ############################################
        """------------------------------------------<in_series>------------------------------------------"""
        # IN_SERIES []
        # > dcat:inSeries

        in_series_identifier=[s["identifier"]  for s in dataset['in_series']]
        in_series = self._triples(g,dataset_ref, DCAT.inSeries, None)
        assert len(in_series) == len(in_series_identifier)
        for in_ser in in_series:
            assert str(in_ser[-1]) in in_series_identifier
        
        """------------------------------------------<series_dataset>------------------------------------------"""
        # SERIES_MEMBER []
        # > dcat:seriesMember

        series_member_identifier=[s["identifier"]  for s in dataset['dataset_series']]
        in_series = self._triples(g,dataset_ref, DCAT.seriesMember, None)
        assert len(in_series) == len(series_member_identifier)
        for _in_ser in in_series:
            assert str(_in_ser[-1]) in series_member_identifier
        
        
        
        ############################################   Références  ############################################

        """ ------------------<page>: Documentation ------------------ """
        page_documentation = self._triples(g,dataset_ref, FOAF.page, None)
        for p in page_documentation:
            p=p[-1]
            if str(p) == dataset["page"][0]['uri']:
                assert self._triple(g, p, RDF.type, FOAF.Document)
                assert self._triple(g, p,  DCT.url, dataset["page"][0]['url'])
                
                for x in  self._triples(g, p, DCT.title, None):
                    eq_(dataset["page"][0]['title'][x[-1].language],str(x[-1]))

                for x in  self._triples(g, p, DCT.description, None):
                    eq_(dataset["page"][0]['description'][x[-1].language],str(x[-1]))

                assert self._triple(g, p,  DCT.modified,Literal( dataset["page"][0]['modified'],
                                                  datatype=XSD.dateTime))
                assert self._triple(g, p,  DCT.created,Literal(dataset["page"][0]['created'],
                                                  datatype=XSD.dateTime))
                assert self._triple(g, p,  DCT.issued,Literal(dataset["page"][0]['issued'],
                                                  datatype=XSD.dateTime))
            else:
                assert str(p) == dataset["attributes_page"]
                
        ############################################   Thèmes et mots clés   ############################################
        
        list_categories=[cat["uri"] for cat in dataset["category"]]+[theme['uri'] for theme in dataset["theme"]]
        """------------------------------------------ [ category, theme ] ------------------------------------------"""
        # CATEGORY []
        # > dcat:theme
        # THEME []
        # > dcat:theme
        themes = self._triples(g,dataset_ref, DCAT.theme, None)
        for theme in themes:
            assert str(theme[-1]) in list_categories


        """------------------------------------------ free_tags ------------------------------------------"""
        # FREE_TAG [{*}]
        # > dcat:keyword

        ############################################   Métadonnées sur les métadonnées   ############################################

        """------------------------------------------ is_primary_topic_of ------------------------------------------"""
        # > foaf:isPrimaryTopicOf -> dcat:CatalogRecord
        # [- DCAT-AP v2]
        is_primary_topic_of_dict=dataset["is_primary_topic_of"]
        is_primary_topic_of_node = self._triples(g,dataset_ref, FOAF.isPrimaryTopicOf, None)
        assert is_primary_topic_of_dict
        for primary in is_primary_topic_of_node:
            primary=primary[-1]
            assert self._triple(g, primary, RDF.type, DCAT.CatalogRecord)

            # MODIFIED
            # > dct:modified
            assert self._triple(g, primary, DCT.modified,Literal(is_primary_topic_of_dict[0]["modified"],
                                                  datatype=XSD.dateTime))

            # LANGUAGE []
            # > dct:language
            langages=[str(lang[-1]) for lang in self._triples(g, primary, DCT.language,None)]
            for lang in  langages:
                assert lang in is_primary_topic_of_dict[0]["language"]                


            # IDENTIFIER 
            # > dct:identifier
            assert self._triple(g, primary, DCT.identifier,is_primary_topic_of_dict[0]["identifier"])
            
            
            contact_point_node = self._triple(g,primary, DCAT.contactPoint, None)[-1]
            assert contact_point_node is not None
            assert self._triple(g, contact_point_node, RDF.type, VCARD.Kind)

            for x in  self._triples(g, contact_point_node, VCARD.fn, None):
                eq_(is_primary_topic_of_dict[0]["contact_point"][0]['name'][x[-1].language],str(x[-1]))
            
            assert self._triple(g, contact_point_node, VCARD.hasEmail, is_primary_topic_of_dict[0]["contact_point"][0]["email"])
            
            assert self._triple(g, contact_point_node, VCARD.hasTelephone, is_primary_topic_of_dict[0]["contact_point"][0]["phone"])
            
            assert self._triple(g, contact_point_node, VCARD.hasURL, is_primary_topic_of_dict[0]["contact_point"][0]["url"])
            
            
            # AFFILIATION {*}
            # > vcard:organization-name
            for x in  self._triples(g, contact_point_node, VCARD.organization, None):
                eq_( is_primary_topic_of_dict[0]["contact_point"][0]["affiliation"][x[-1].language],str(x[-1]))

            # IN_CATALOG [{}]
            # > dcat:inCatalog -> dcat:Catalog
            inCatalog_node = self._triple(g,primary, DCAT.inCatalog, None)
            assert  self._triple(g, inCatalog_node[-1], RDF.type, DCAT.Catalog)
            for x in  self._triples(g, inCatalog_node[-1], DCT.title, None):
                eq_( is_primary_topic_of_dict[0]["in_catalog"]["title"][x[-1].language],str(x[-1]))
            assert self._triple(g, inCatalog_node[-1], FOAF.homepage, is_primary_topic_of_dict[0]["in_catalog"]["homepage"])



        # ############################################   Couverture spatiale   ############################################

        bbox_node = self._triples(g,dataset_ref, DCT.spatial, None)
        for node in bbox_node:
             
            node=node[-1]
            assert  self._triple(g, node, RDF.type, DCT.Location)

            """------------------------------------------ spatial_coverage ------------------------------------------"""
            if str(node) == dataset["spatial_coverage"][0]['uri']:
                assert self._triple(g, node, DCT.identifier, dataset["spatial_coverage"][0]["identifier"])
                for x in  self._triples(g, contact_point_node, SKOS.prefLabel, None):
                    eq_( dataset["spatial_coverage"][0]["label"][x[-1].language],str(x[-1]))
                assert self._triple(g, node, SKOS.inScheme, dataset["spatial_coverage"][0]["in_scheme"])
    
            """------------------------------------------ bbox ------------------------------------------"""
            if node_bbox:=self._triple(g, node,  DCT.bbox, dataset["bbox"]):
                assert str(node_bbox[-1]) == dataset["bbox"]

                
                
        # ############################################   Etc   ############################################
        
        """------------------------------------------ access_rights ------------------------------------------"""
    
        access_rights = self._triples(g,dataset_ref, FOAF.accessRights, None)
        for a_r in access_rights:
            a_r=a_r[-1]
            assert  self._triple(g, a_r, RDF.type, DCT.RightsStatement)
            # URI
            eq_( dataset["access_rights"][0]["uri"],str(a_r))
            # LABEL {*}
            # > rdfs:label
            for x in  self._triples(g, a_r, SKOS.prefLabel, None):
                eq_( dataset["access_rights"][0]["label"][x[-1].language],str(x[-1]))


        _crs_list=[c for c in dataset["crs"]]
        crs_nodes = self._triples(g,dataset_ref, DCT.conformsTo, None)
        for a in crs_nodes:
            a=a[-1]
            """------------------------------------------conforms_to ------------------------------------------"""
            if str(a) == dataset["conforms_to"][0]["uri"]:
                assert  self._triple(g, a, RDF.type,  DCT.Standard)
                for x in  self._triples(g, a, DCT.title, None):
                    eq_( dataset["conforms_to"][0]["title"][x[-1].language],str(x[-1]))
            else:
                """------------------------------------------ crs ------------------------------------------"""
                assert  str(a) in _crs_list
        
        

        """------------------------------------------language ------------------------------------------"""
   
        langages=[l for l in dataset["language"]] 
        langage = self._triples(g,dataset_ref, DCT.language, None)
        for l in langage:
            assert str(l[-1]) in langages
            
        """------------------------------------------ provenance ------------------------------------------"""

        provenance_nodes = self._triples(g,dataset_ref, DCT.provenance, None)
        assert provenance_nodes
        for prov_node in provenance_nodes:
            prov_node=prov_node[-1]
            assert  self._triple(g, prov_node, RDF.type, DCT.ProvenanceStatement)

            for v_note in self._triples(g,prov_node, RDFS.label,  None):
                assert dataset["provenance"][v_note[-1].language] == str(v_note[-1])
    
        
        
        """------------------------------------------ version ------------------------------------------"""
        #voir littéraux 
        
        """------------------------------------------ version notes ------------------------------------------"""

        #version_notes
        version_notes = list(self._triples(g,dataset_ref, ADMS.versionNotes, None))
        for v_note in version_notes:
            assert dataset["version_notes"][v_note[-1].language] == str(v_note[-1])
            
            
        """------------------------------------------  temporal_resolution ------------------------------------------"""
        #voir littéraux 

        """------------------------------------------ spatial_resolution   ------------------------------------------"""
        #voir littéraux 
    
    
        ############################################   RESSOURCES ############################################
        
        distribution_nodes = self._triples(g,dataset_ref, DCAT.distribution, None)
        for dist in distribution_nodes:
            dist=dist[-1]

            assert str(dist) == dataset["resources"][0]["uri"]


            """------------------------------------------ url   ------------------------------------------"""

            assert self._triple(g,dist, DCAT.accessURL, dataset["resources"][0]["url"])
            
            """------------------------------------------ download_url   ------------------------------------------"""
            assert  self._triple(g,dist, DCAT.downloadURL, dataset["resources"][0]["download_url"])


            """------------------------------------------ title   ------------------------------------------"""

            titles = self._triples(g,dist, DCT.title, None)
            for title in titles:
                if title[-1].language:
                    assert dataset["resources"][0]["name"][title[-1].language] == str(title[-1])


            """------------------------------------------ description   ------------------------------------------"""

            descriptions = self._triples(g,dist, DCT.description, None)
            for description in descriptions:
                if description[-1].language:
                    assert dataset["resources"][0]["description"][description[-1].language] == str(description[-1])

            """------------------------------------------ media_type_ressource   ------------------------------------------"""
            
            media_type_ressource_nodes = self._triple(g,dist, DCT.mediaType, None)[-1]
            assert  self._triple(g, media_type_ressource_nodes, RDF.type, DCT.MediaType)

            assert str(media_type_ressource_nodes) ==  dataset["resources"][0]["media_type_ressource"][0]["uri"]
            for node in  self._triples(g,media_type_ressource_nodes, RDFS.label, None):
                assert   dataset["resources"][0]["media_type_ressource"][0]["label"][node[-1].language] == str(node[-1])
            

            """------------------------------------------ other_format   ------------------------------------------"""
            
            format_nodes = self._triple(g,dist, DCT["format"], None)[-1]
            assert  self._triple(g, format_nodes, RDF.type, DCT.MediaTypeOrExtent)
            assert str(format_nodes) ==  dataset["resources"][0]["other_format"][0]["uri"]
            for node in  self._triples(g,format_nodes, RDFS.label, None):
                assert   dataset["resources"][0]["other_format"][0]["label"][node[-1].language] == str(node[-1])


            """------------------------------------------ service_conforms_to   ------------------------------------------"""
            
            _conforms_to_node = self._triples(g,dist, DCT.accessService, None)
            assert _conforms_to_node
            for _conforms_to_node_item in _conforms_to_node:
                assert  self._triple(g, _conforms_to_node_item[-1], RDF.type, DCAT.DataService)
                assert str(_conforms_to_node_item[-1]) ==  dataset["resources"][0]["service_conforms_to"][0]["uri"]
                for node in  self._triples(g,_conforms_to_node_item[-1],  DCT.conformsTo, None):
                    assert   dataset["resources"][0]["service_conforms_to"][0]["title"][node[-1].language] == str(node[-1])


            """------------------------------------------ rights   ------------------------------------------"""
            access_right_node = self._triple(g,dist, DCT.rights, None)
            assert access_right_node
            for node in  self._triples(g,access_right_node, RDFS.label, None):
                assert self._triple(g, node[-1], RDF.type, DCT.RightsStatement)
                assert dataset["rights"][node[-1].language] == str(node[-1])
        

            """------------------------------------------ licenses   ------------------------------------------"""
            _license_node = self._triple(g,dist, DCT.license, None)[-1]
            assert self._triple(g, _license_node, RDF.type, DCT.LicenseDocument)

            #uri
            assert str(_license_node) == dataset["resources"][0]["licenses"][0]["uri"]
            
            #label
            labels = self._triples(g,_license_node, RDFS.label, None)
            for label in labels:
                if label[-1].language:
                    assert dataset["resources"][0]["licenses"][0]["label"][label[-1].language] == str(label[-1])

            #type
            types = self._triples(g,_license_node, DCT.type, None)
            for _type in types:
                assert str(_type[-1]) in  dataset["resources"][0]["licenses"][0]["type"]


            """------------------------------------------ resource_issued   ------------------------------------------"""
            assert self._triple(g, dist, DCT.issued,  parse_date(dataset["resources"][0]["resource_issued"]).isoformat(), XSD.dateTime)
