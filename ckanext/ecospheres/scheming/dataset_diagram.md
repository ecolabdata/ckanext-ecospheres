```mermaid

flowchart LR

    classDef tab fill:#fee9e5,stroke:#E4794A
    classDef main fill:#fddede,stroke:#e1000f
    classDef hidden fill:#f3ede5,stroke:#AEA397

    classDef node fill:#e9edfe,stroke:#465F9D
    classDef uri fill:#bafaee,stroke:#009081
    classDef nodeOrUri fill:#009099,stroke:#c7f6fc
    classDef literal fill:#feebd0,stroke:#C3992A

    dataset{dataset}-->hidden([hidden]):::hidden
    dataset-->main([main]):::main
    dataset-->resources([resources]):::resources
        main-->name1[name]:::literal
        hidden-->uri1[uri]:::uri
        hidden-->identifier1[identifier]:::literal
        main-->title1[title]:::literal
        main-->notes1[notes]:::literal
        main-->temporal1[temporal]:::node
            temporal1-->end_date1[end_date]:::literal
            temporal1-->start_date1[start_date]:::literal
        main-->modified1[modified]:::literal
        tab1([Détails]):::tab-->created1[created]:::literal
        tab1-->issued1[issued]:::literal
        tab2([Contacts et acteurs]):::tab-->contact_point1[contact_point]:::node
            contact_point1-->comment1[comment]:::literal
            contact_point1-->acronym1[acronym]:::literal
            contact_point1-->affiliation1[affiliation]:::literal
            contact_point1-->url1[url]:::uri
            contact_point1-->phone1[phone]:::uri
            contact_point1-->email1[email]:::uri
            contact_point1-->name2[name]:::literal
        tab2-->publisher1[publisher]:::node
            publisher1-->comment2[comment]:::literal
            publisher1-->acronym2[acronym]:::literal
            publisher1-->affiliation2[affiliation]:::literal
            publisher1-->url2[url]:::uri
            publisher1-->phone2[phone]:::uri
            publisher1-->email2[email]:::uri
            publisher1-->type1[fa:fa-list type]:::uri
            publisher1-->name3[name]:::literal
        tab2-->creator1[creator]:::node
            creator1-->comment3[comment]:::literal
            creator1-->acronym3[acronym]:::literal
            creator1-->affiliation3[affiliation]:::literal
            creator1-->url3[url]:::uri
            creator1-->phone3[phone]:::uri
            creator1-->email3[email]:::uri
            creator1-->type2[fa:fa-list type]:::uri
            creator1-->name4[name]:::literal
        tab2-->rights_holder1[rights_holder]:::node
            rights_holder1-->comment4[comment]:::literal
            rights_holder1-->acronym4[acronym]:::literal
            rights_holder1-->affiliation4[affiliation]:::literal
            rights_holder1-->url4[url]:::uri
            rights_holder1-->phone4[phone]:::uri
            rights_holder1-->email4[email]:::uri
            rights_holder1-->type3[fa:fa-list type]:::uri
            rights_holder1-->name5[name]:::literal
        tab2-->qualified_attribution1[qualified_attribution]:::node
            qualified_attribution1-->agent1[agent]:::node
                agent1-->url5[url]:::uri
                agent1-->email5[email]:::uri
                agent1-->name6[name]:::literal
            qualified_attribution1-->had_role1[fa:fa-list had_role]:::uri
        main-->in_series1[in_series]:::nodeOrUri
            in_series1-->title2[title]:::literal
            in_series1-->url6[url]:::uri
            in_series1-->uri2[uri]:::uri
        main-->series_member1[series_member]:::nodeOrUri
            series_member1-->title3[title]:::literal
            series_member1-->url7[url]:::uri
            series_member1-->uri3[uri]:::uri
        main-->landing_page1[landing_page]:::uri
        tab3([Documentation]):::tab-->attributes_page1[attributes_page]:::uri
        tab3-->page1[page]:::nodeOrUri
            page1-->issued2[issued]:::literal
            page1-->created2[created]:::literal
            page1-->modified2[modified]:::literal
            page1-->url8[url]:::uri
            page1-->description1[description]:::literal
            page1-->title4[title]:::literal
            page1-->uri4[uri]:::uri
        tab1-->category1[fa:fa-list category]:::uri
        tab1-->subcategory1[fa:fa-list subcategory]:::uri
        hidden-->theme1[fa:fa-list theme]:::uri
        tab1-->free_tags1[free_tags]:::literal
        tab1-->is_primary_topic_of1[is_primary_topic_of]:::node
            is_primary_topic_of1-->in_catalog1[in_catalog]:::node
                in_catalog1-->homepage1[homepage]:::uri
                in_catalog1-->title5[title]:::literal
            is_primary_topic_of1-->contact_point2[contact_point]:::node
                contact_point2-->comment5[comment]:::literal
                contact_point2-->acronym5[acronym]:::literal
                contact_point2-->affiliation5[affiliation]:::literal
                contact_point2-->url9[url]:::uri
                contact_point2-->phone5[phone]:::uri
                contact_point2-->email6[email]:::uri
                contact_point2-->name7[name]:::literal
            is_primary_topic_of1-->identifier2[identifier]:::literal
            is_primary_topic_of1-->language1[fa:fa-list language]:::uri
            is_primary_topic_of1-->harvested1[harvested]:::literal
            is_primary_topic_of1-->modified3[modified]:::literal
        hidden-->bbox1[bbox]:::literal
        tab1-->spatial_coverage1[spatial_coverage]:::nodeOrUri
            spatial_coverage1-->label1[label]:::literal
            spatial_coverage1-->identifier3[identifier]:::literal
            spatial_coverage1-->in_scheme1[fa:fa-list in_scheme]:::uri
            spatial_coverage1-->uri5[fa:fa-list uri]:::uri
        hidden-->spatial1[spatial]:::literal
        hidden-->territory1[fa:fa-list territory]:::uri
        hidden-->territory_full1[fa:fa-list territory_full]:::uri
        tab1-->access_rights1[access_rights]:::nodeOrUri
            access_rights1-->label2[label]:::literal
            access_rights1-->uri6[fa:fa-list uri]:::uri
        main-->restricted_access1[restricted_access]:::literal
        tab1-->crs1[fa:fa-list crs]:::uri
        tab1-->conforms_to1[conforms_to]:::nodeOrUri
            conforms_to1-->title6[title]:::literal
            conforms_to1-->uri7[fa:fa-list uri]:::uri
        tab1-->accrual_periodicity1[fa:fa-list accrual_periodicity]:::uri
        tab1-->language2[fa:fa-list language]:::uri
        tab1-->provenance1[provenance]:::literal
        tab1-->version1[version]:::literal
        tab1-->version_notes1[version_notes]:::literal
        tab1-->temporal_resolution1[temporal_resolution]:::literal
        tab1-->spatial_resolution1[spatial_resolution]:::literal
        hidden-->equivalent_scale1[equivalent_scale]:::literal
        hidden-->license_id1[license_id]:::literal
        main-->graphic_preview1[graphic_preview]:::uri
        tab4([Export]):::tab-->as_inspire_xml1[as_inspire_xml]:::uri
        tab4-->as_dcat_rdf1[as_dcat_rdf]:::node
            as_dcat_rdf1-->download_url1[download_url]:::uri
            as_dcat_rdf1-->format1[format]:::nodeOrUri
                format1-->label3[label]:::literal
                format1-->uri8[fa:fa-list uri]:::uri
        tab4-->ckan_api_show1[ckan_api_show]:::uri
        resources-->uri9[uri]:::uri
        resources-->url10[url]:::uri
        resources-->download_url2[download_url]:::uri
        resources-->name8[name]:::literal
        resources-->description2[description]:::literal
        resources-->media_type_ressource1[media_type_ressource]:::nodeOrUri
            media_type_ressource1-->label4[label]:::literal
            media_type_ressource1-->uri10[fa:fa-list uri]:::uri
        resources-->other_format1[other_format]:::nodeOrUri
            other_format1-->label5[label]:::literal
            other_format1-->uri11[fa:fa-list uri]:::uri
        resources-->format2[format]:::literal
        resources-->service_conforms_to1[service_conforms_to]:::nodeOrUri
            service_conforms_to1-->title7[title]:::literal
            service_conforms_to1-->uri12[fa:fa-list uri]:::uri
        resources-->rights1[rights]:::literal
        resources-->licenses1[licenses]:::nodeOrUri
            licenses1-->label6[label]:::literal
            licenses1-->type4[fa:fa-list type]:::uri
            licenses1-->uri13[fa:fa-list uri]:::uri
        resources-->resource_issued1[resource_issued]:::literal

```
