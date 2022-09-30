"""Utilitaires pour l'exploitation des schémas de ckanext-scheming. 

Les classes et fonctions définies par ce module permettent
de construire des coquilles de dictionnaires structurées selon
un schéma et prêtes à être remplies de métadonnées moissonnées.

Initialisation du ``dataset_dict`` d'un jeu de données :

    >>> dataset_dict = EcospheresDatasetDict(dataset_schema)

Il est possible de préciser une "langue principale", dans laquelle
seront présumées rédigées toutes les métadonnées traduisibles sauf
mention contraire :

    >>> dataset_dict = EcospheresDatasetDict(dataset_schema,
    ...     main_language='fr')

Si ``main_language`` n'est pas spécifié, les métadonnées seront
présumées rédigées en français.

Pour ajouter une ressource :

    >>> resource_dict = dataset_dict.new_resource()

``resource_dict`` est un dictionnaire à compléter avec les métadonnées
décrivant la ressource, avec les mêmes méthodes que ``dataset_dict``.

Pour définir la valeur ou l'une des valeurs d'une métadonnée (cas
d'une métadonnée admettant des valeurs littérales) :

    >>> dataset_dict.set_value(field_name, value)

Il est possible de spécifier individuellement la langue
des valeurs admettant des traductions, sinon c'est la langue
principale définie à l'initialisation du dictionnaire qui sera
appliquée :

    >>> dataset_dict.set_value(field_name, value, langue='en')

Préciser la langue pour des métadonnées non traduisibles ne pose pas
de problème, l'information sera simplement ignorée.

:py:meth:``EcospheresObjectDict.set_value`` n'a généralement aucun
effet lorsque le champ n'est pas référencé par le schéma, sauf si
le dictionnaire contient un champ ``extras``. Dans ce cas, les
métadonnées inconnues sont ajoutées à ``extras`` sous la forme d'un
dictionnaire ``{'key': field_name, 'value': value}``.

Appliquer plusieurs fois :py:meth:``EcospheresObjectDict.set_value``
à la même métadonnée n'écrase les valeurs précédemment saisies que
si la métadonnée n'admettait qu'une valeur ou qu'une traduction par
langue. Autrement dit, elle se charge d'assurer le respect de la
cardinalité définie par le schéma, et il n'y a pas lieu de prendre
d'autres précautions en la matière par ailleurs.

Pour définir la valeur ou l'une des valeurs d'une métadonnée
lorsque la valeur est elle-même décrite par un ensemble de
propriétés :

    >>> subdict = dataset_dict.new_item(field_name)

``subdict`` pointe sur une coquille de dictionnaire structurée selon le
schéma, au même titre que ``dataset_dict``, et qui peut elle aussi
être remplie avec les méthodes :py:meth:``EcospheresObjectDict.set_value``
et :py:meth:``EcospheresObjectDict.new_item``.

"""

MAIN_LANGUAGE = 'fr'

class EcospheresObjectDict(dict):
    """Dictionnaire contenant les métadonnées qui décrivent un objet CKAN.

    Un objet :py:class:`EcospheresObjectDict` peut constituer un
    fragment d'un autre :py:class:`EcospheresObjectDict`.

    :py:class:`EcospheresObjectDict` produit des dictionnaires vides.
    Pour préparer le stockage des métadonnées d'un objet donné, on
    utilisera toujours la sous-classe correspondant à son type
    (par exemple :py:class:`EcospheresDatasetDict` pour les jeux de
    données / datasets). Celle-ci initialise le dictionnaire à partir
    du schéma défini pour le type et met à disposition des méthodes
    spécifiques.

    """

    def get_values(self, field_name, language=None):
        """Liste toutes les valeurs d'un champ du dictionnaire.
        
        Pour les champs avec ``repeating_subfields``, cette
        méthode récupère les valeurs du premier des champs qui décrivent
        l'objet (de manière récursive si ce champ a lui-même
        des ``repeating_subfields``).

        Parameters
        ----------
        field_name : str
            Nom d'un champ (une clé) du dictionnaire présumé
            être référencé et admettre une valeur de type
            autre que :py:class:`EcospheresSubfieldsList`. Si
            l'une de ces conditions n'est pas respectée, la
            méthode renvoie silencieusement une liste vide.
        language : str, optional
            Le cas échéant, la langue attendue pour les valeurs.
            Si non spécifié, toutes les valeurs sont renvoyées.
            On utilisera autant que possible les codes ISO 639
            sur deux caractères (ex : ``'fr'``), et plus
            généralement le code approprié pour désigner la
            langue en RDF.
        
        Returns
        -------
        list

        """
        if not field_name in self:
            return []
        
        values = self[field_name]

        if isinstance(values, EcospheresSimpleTranslationDict):
            if language:
                if language in values:
                    return [values[language]]
                else:
                    return []
            else:
                res = []
                for value in values.values():
                    if not value in res:
                        res.append(value)
                return res
        
        if isinstance(values, EcospheresMultiTranslationsDict):
            if language:
                if language in values:
                    return values[language]
                else:
                    return []
            else:
                res = []
                for lang_values in values.values():
                    for value in lang_values:
                        if not value in res:
                            res.append(value)
                return res
        
        if isinstance(values, EcospheresMultiValuesList):
            return values
        
        if isinstance(values, EcospheresSubfieldsList):
            return values.list_values(language=language)

        return [values] if values else []

    def set_value(self, field_name, value, language=None):
        """Définit la valeur ou l'une des valeurs d'un champ du dictionnaire.
        
        Pour les champs avec ``repeating_subfields``, cette
        méthode alimente le premier des champs qui décrivent
        l'objet (de manière récursive si ce champ a lui-même
        des ``repeating_subfields``). Il est tout à fait justifié
        de l'utiliser quand il n'y a qu'un seul sous-champ prenant
        des valeurs littérales ou des URI, sinon il est recommandé
        d'utiliser :py:meth:`EcospheresObjectDict.new_item`.

        Si le champ admet plusieurs valeurs, traduisibles ou non,
        la nouvelle valeur est ajoutée aux précédentes, sauf si
        elle était déjà présente. Si le champ n'admet qu'une
        valeur (ou qu'une seule valeur pour la langue considérée),
        la nouvelle valeur remplacera celle qui aurait pu être
        antérieurement saisie.

        La méthode élimine les espaces et retours à la ligne en début et
        fin des chaînes de caractères, le cas échéant. Elle s'assure de
        ne jamais saisir deux fois la même valeur (post nettoyage) pour
        une métadonnée qui admet plusieurs valeurs. ``None`` et les valeurs
        vides (post nettoyage) sont toujours ignorées, sauf pour une
        métadonnée admettant une seule valeur non traduisible (et les
        chaînes de caractères vides sont alors considérées comme ``None``).

        Pour supprimer toutes les valeurs d'une métadonnée, on utilisera
        plutôt :py:meth`EcospheresObjectDict.delete_values`.

        Parameters
        ----------
        field_name : str
            Nom d'un champ (une clé) du dictionnaire présumé
            être référencé, sans quoi la méthode n'aura
            silencieusement aucun effet.
        value : str or int or float or list(str or int or float)
            La valeur du champ. Le type n'est pas contrôlé, mais il
            devrait tout au moins s'agir d'une valeur litérale ou
            d'une liste de valeurs litérales. Dans ce dernier cas,
            la méthode est appliquée récursivement à tous les éléments
            de la liste (avec la même langue, le cas échéant). Si la
            métadonnée se trouvait n'admettre qu'une seule valeur,
            c'est la dernière de la liste qui subsistera.
        language : str, optional
            Le cas échéant, la langue dans laquelle est rédigée la
            valeur. On utilisera autant que possible les codes
            ISO 639 sur deux caractères (ex : ``'fr'``), et plus
            généralement le code approprié pour désigner la langue
            en RDF.

        Examples
        --------
        >>> dataset_dict = EcospheresDatasetDict(dataset_schema)
        >>> dataset_dict['title']
        {}
        >>> dataset_dict.set_value('title', 'Mon titre', 'fr')
        >>> dataset_dict['title']
        {'fr': 'Mon titre'}

        >>> dataset_dict.set_value('free_tag', ['Mot-clé A', 'Mot-clé A', 'Mot-clé B'], 'fr')
        >>> dataset_dict['free_tag']
        {'fr': ['Mot-clé A', 'Mot-clé B']}

        """  
        if not field_name in self:
            return
        
        if isinstance(value, list):
            for v in value:
                self.set_value(field_name, value=v, language=language)
            return
        
        if isinstance(value, str):
            # nettoyage des chaînes de caractères
            value = value.strip(' \r\n') or None

        if isinstance(self[field_name], (EcospheresSimpleTranslationDict,
            EcospheresMultiTranslationsDict, EcospheresMultiValuesList,
            EcospheresSubfieldsList)):
            self[field_name].add_item(value=value, language=language)
        else:
            # reste le cas où le champ admet des valeurs simples
            # non traduisibles
            self[field_name] = value
    
    def delete_values(self, field_name, language=None):
        """Supprime toutes les valeurs d'un champ.

        Parameters
        ----------
        field_name : str
            Nom d'un champ (une clé) du dictionnaire présumé
            être référencé.
        language : str, optional
            Si la métadonnée considérée est traduisible et que 
            `language` est spécifié, seules les éventuelles valeurs
            dans la langue considérée seront supprimées.
        
        """
        if not field_name in self:
            return
        if isinstance(self[field_name], (EcospheresSimpleTranslationDict,
            EcospheresMultiTranslationsDict, EcospheresMultiValuesList,
            EcospheresSubfieldsList)):
            self[field_name].remove_items(language=language)
        else:
            self[field_name] = None

    def new_item(self, field_name):
        """Crée un nouvel objet pour un champ avec sous-propriétés et renvoie son dictionnaire de métadonnées.

        Cette méthode n'a aucun effet sur les autres champs,
        ie. ceux qui n'ont pas de propriété ``repeating_subfields``.
        Pour ceux-là, l'ajout de valeurs est à faire via
        :py:meth:`EcospheresObjectDict.set_value`.

        Parameters
        ----------
        field_name : str
            Nom d'un champ (une clé) du dictionnaire présumé
            être référencé et admettre une valeur de type
            :py:class:`EcospheresSubfieldsList`. Si ces deux
            conditions ne sont pas remplies, la méthode n'aura
            aucun effet et renverra ``None``.

        Returns
        -------
        EcospheresObjectDict
            La dictionnaire de métadonnées du nouvel objet, prêt à
            être complété.

        Example
        -------
        >>> dataset_dict = EcospheresDatasetDict(dataset_schema)
        >>> dataset_dict.new_item('temporal')
        {'start_date': None, 'end_date': None}

        """
        if isinstance(self.get(field_name), EcospheresSubfieldsList):
            return self[field_name].new_item()

    def copy(self):
        return EcospheresObjectDict.__call__(
            {
                k: v.copy() if isinstance(v, (
                    EcospheresSimpleTranslationDict, EcospheresMultiTranslationsDict,
                    EcospheresMultiValuesList, EcospheresSubfieldsList
                )) else None for k, v in self.items()
            }
        )

class EcospheresDatasetDict(EcospheresObjectDict):
    """Dictionnaire contenant les métadonnées qui décrivent un jeu de données.

    Parameters
    ----------
    dataset_schema : dict
        Dé-sérialisation du schéma YAML décrivant la structure des
        objets CKAN de type ``dataset`` (jeux de données).
    main_language : str, optional
        S'il y a lieu, une langue dans laquelle seront supposées
        être rédigées toutes les valeurs traduisibles dont la
        langue n'est pas explicitement spécifiée. On utilisera
        autant que possible un code ISO 639 sur deux caractères,
        et plus généralement le code approprié pour désigner la
        langue en RDF.

    """

    def __init__(self, dataset_schema, main_language=None):
        dataset_dict = schema_reader(dataset_schema['dataset_fields'],
            main_language=main_language)
        resource_model = schema_reader(dataset_schema['resource_fields'],
            main_language=main_language)
        dataset_dict['resources'] = EcospheresSubfieldsList(model=resource_model)
        dataset_dict['extras'] = []
        dataset_dict['owner_org'] = None
        self.update(dataset_dict)
    
    def new_resource(self):
        """Référence une nouvelle ressource dans le dictionnaire du jeu de données.

        Returns
        -------
        EcospheresObjectDict
            La dictionnaire de métadonnées de la ressource, prêt à
            être complété.

        """
        return self['resources'].new_item()

    def set_value(self, field_name, value=None, language=None):
        """Définit la valeur ou l'une des valeurs d'un champ du dictionnaire.
        
        Cette méthode complète :py:meth:`EcospheresObjectDict.set_value`
        en autorisant l'ajout d'un champ non référencé dans la section
        ``'extras'`` du dictionnaire.

        Si une nouvelle valeur est définie pour une clé déjà référencée
        dans ``'extras'``, elle remplace la précédente.

        `value` peut être ``None``, néanmoins cela ne se justifierait que
        si une clé doit impérativement être présente pour des traitements
        ultérieurs, même si la valeur de la métadonnée n'est pas connue.
        Dans les autres cas, on appliquera plutôt la méthode
        :py:meth:`EcospheresDatasetDict.delete_values`, ce qui aura pour
        effet d'enlever le champ référencé dans ``'extras'``.

        """
        if not field_name in self:
            if isinstance(value, str):
                # nettoyage des chaînes de caractères
                value = value.strip(' \r\n') or None
            if not field_name in [e.get('key') for e in self['extras']]:
                self['extras'].append({'key': field_name, 'value': value})
            else:
                for e in self['extras']:
                    if e['key'] == field_name:
                        e['value'] = value
                        break
            return
        super().set_value(field_name, value=value, language=language)

    def delete_values(self, field_name, language=None):
        """Supprime toutes les valeurs d'un champ.

        Cette méthode complète :py:meth:`EcospheresObjectDict.delete_values`
        en gérant la suppression des champs référencés dans la section
        ``'extras'`` du dictionnaire.
        
        """
        for e in self['extras'].copy():
            if e.get('key') == field_name:
                self['extras'].remove(e)
        super().delete_values(field_name, language=language)

    def delete_resources(self):
        """Supprime toutes les ressources renseignées dans le dictionnaire de jeu de données."""
        self.delete_values('resources')

class EcospheresSubfieldsList(list):
    """Liste de valeurs elles-mêmes décrites par des métadonnées.
    
    Les valeurs associées aux clés des :py:class:`EcospheresObjectDict`
    représentant des métadonnées dont les valeurs sont elles-mêmes décrites
    par des métadonnées sont de type :py:class:`EcospheresSubfieldsList`.

    """

    def __init__(self, model):
        self.model = model
    
    def new_item(self):
        item = self.model.copy()
        self.append(item)
        return item

    def remove_items(self, *args, **kwargs):
        self.clear()

    def add_item(self, value, *args, **kwargs):
        if not value:
            return
        new_item = self.new_item()
        for field_name in new_item:
            new_item.set_value(field_name, value, *args, **kwargs)
            break
    
    def list_values(self, *args, **kwargs):
        values = []
        for item in self:
            for field_name in item:
                values += item.get_values(field_name, *args, **kwargs)
                break
        return values

    def copy(self):
        copy = type(self).__call__(self.model)
        # une copie est une liste vide avec le même modèle
        return copy

class EcospheresSimpleTranslationDict(dict):
    """Dictionnaire de traductions (une seule valeur par langue).
    
    Les valeurs associées aux clés des :py:class:`EcospheresObjectDict`
    représentant des métadonnées admettant une unique valeur traduisible
    dans plusieurs langues sont de type :py:class:`EcospheresSimpleTranslationDict`.

    """

    def __init__(self, main_language=None):
        self.main_language = main_language or MAIN_LANGUAGE
    
    def add_item(self, value, language=None):
        if not value:
            return
        lang = language or self.main_language
        self[lang] = value
    
    def remove_items(self, language=None):
        if not language:
            self.clear()
        elif language in self:
            del self[language]
    
    def copy(self):
        return type(self).__call__(self.main_language)

class EcospheresMultiTranslationsDict(dict):
    """Dictionnaire de traductions (plusieurs valeurs par langue).
    
    Les valeurs associées aux clés des :py:class:`EcospheresObjectDict`
    représentant des métadonnées admettant plusieurs valeurs traduisibles
    sont de type :py:class:`EcospheresMultiTranslationsDict`.

    """

    def __init__(self, main_language=None):
        self.main_language = main_language or MAIN_LANGUAGE
    
    def add_item(self, value, language=None):
        if not value:
            return
        lang = language or self.main_language
        if lang in self:
            if not value in self[lang]:
                self[lang].append(value)
        else:
            self[lang] = [value]
    
    def remove_items(self, language=None):
        if not language:
            self.clear()
        elif language in self:
            del self[language]
    
    def copy(self):
        return type(self).__call__(self.main_language)

class EcospheresMultiValuesList(list):
    """Liste de valeurs littérales non traduisibles.
    
    Les valeurs associées aux clés des :py:class:`EcospheresObjectDict`
    représentant des métadonnées admettant plusieurs valeurs non
    traduisibles sont de type :py:class:`EcospheresMultiValuesList`.

    """
    
    def add_item(self, value, *args, **kwargs):
        if not value:
            return
        if not value in self:
            self.append(value)
    
    def remove_items(self, *args, **kwargs):
        self.clear()

    def copy(self):
        return type(self).__call__()

def schema_reader(schema_sublist, main_language=None):
    """Génère un dictionnaire vierge à partir d'une liste de champs.

    Si elle rencontre un champ présentant une propriété
    ``'repeating_subfields'``, la fonction est appliquée récursivement.

    Parameters
    ----------
    schema_sublist : list
        Fragment de schéma correspondant à une liste de champs.
        Chaque champ est défini par un dictionnaire présentant au
        moins une propriété ``'field_name'``, dont la valeur deviendra
        une clé du dictionnaire renvoyé. La valeur associé peut être
        ``None``, un dictionnaire ou une liste selon la présence et
        la valeur des propriétés ``'repeating_subfields'``,
        ``'multiple_values'`` et ``'translatable_values'``.
    main_language : str, optional
        Langue dans laquelle seront supposées être rédigées toutes les
        valeurs traduisibles dont la langue n'est pas explicitement
        spécifiée.

    Returns
    -------
    EcospheresObjectDict

    Examples
    --------
    >>> schema_reader([{'field_name': 'title'},
    ...     {'field_name': 'free_tag', 'multiple_values': True}])
    {'title': None, 'free_tags': []}

    """
    subdict = EcospheresObjectDict()
    for e in schema_sublist:
        if 'repeating_subfields' in e:
            model = schema_reader(e['repeating_subfields'])
            subdict[e['field_name']] = EcospheresSubfieldsList(model=model)
        elif e.get('translatable_values') and e.get('multiple_values'):
            subdict[e['field_name']] = EcospheresMultiTranslationsDict(main_language=main_language)
        elif e.get('translatable_values'):
            subdict[e['field_name']] = EcospheresSimpleTranslationDict(main_language=main_language)
        elif e.get('multiple_values'):
            subdict[e['field_name']] = EcospheresMultiValuesList()
        else:
            subdict[e['field_name']] = None
    return subdict

