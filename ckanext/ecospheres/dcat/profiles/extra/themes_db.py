import psycopg2
import os 
postgreSQL_select_Query = "SELECT\
                                theme.theme_label,\
                                theme.theme_uri,\
                                sous_theme.s_theme_label,\
                                sous_theme.s_theme_uri \
                            FROM\
                                theme\
                            FULL JOIN sous_theme \
                            ON sous_theme.theme_id=theme.theme_label;\
                            "
themes={}


# connection_cred={
#     'user':"postgres",
#     'password':"tabac",
#     'host':"127.0.0.1",
#     'port':"5432",
#     'database':"mtes"
# }


from urllib.parse import urlparse
uri_postgres=os.getenv('CKAN_SQLALCHEMY_URL',None)
result = urlparse(uri_postgres)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

connection_cred={
    'user':username,
    'password':password,
    'host':hostname,
    'port':port,
    'database':database
}
# print("username: ",username)
# print("password: ",password)
# print("database: ",database)
# print("hostname: ",hostname)
# connection = psycopg2.connect(
#     database = database,
#     user = username,
#     password = password,
#     host = hostname,
#     port = port
# )

def add_if_key_not_exist(dict_obj, key,theme_uri):
    if key not in dict_obj:
        dict_obj.update({key: {}})
        dict_obj[key]["theme_uri"]=theme_uri
        dict_obj[key].update({"s_themes": []})


def add_sub_theme(dict_obj,theme_label:str,sub_theme_label:str,sub_theme_uri:str):

    if theme_label not in dict_obj or (not sub_theme_label and not sub_theme_uri):
        return
    dict_obj[theme_label]['s_themes'].append({
                                            "s_theme_label":sub_theme_label,
                                            "sub_theme_uri":sub_theme_uri
                                            })

def get_records_from_db(connection_cred):
    themes_records=None
    try:
        connection = psycopg2.connect(**connection_cred)
        cursor = connection.cursor()
        cursor.execute(postgreSQL_select_Query)
        themes_records = cursor.fetchall()
        
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)

    finally:
        if connection:
            cursor.close()
            connection.close()
    return themes_records


def get_records_as_dict():
    themes=dict()
    records=get_records_from_db(connection_cred)
    if not records:
        return
    for row in records:
            theme_label=row[0]
            theme_uri=row[1]
            s_theme_label=row[2]
            s_theme_uri=row[3]
            add_if_key_not_exist(themes,theme_label,theme_uri)
            add_sub_theme(themes,theme_label,s_theme_label,s_theme_uri)
    return themes

print("test: ", get_records_as_dict())


def test_db():
    uri_postgres=os.getenv('CKAN_SQLALCHEMY_URL',None)
    print("uri_postgres: ",uri_postgres)
