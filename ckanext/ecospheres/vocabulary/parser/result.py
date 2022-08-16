
from ckanext.ecospheres.vocabulary.parser.model import VocabularyDataCluster
from ckanext.ecospheres.vocabulary.parser import exceptions

class VocabularyParsingStatusCode(int):
    """Abstract class for parsing status codes."""

class VocabularyParsingSuccess(VocabularyParsingStatusCode):
    """The parsing has been successfully completed."""
    def __new__(cls):
        return super().__new__(cls, 0)
    def __str__(self):
        return 'success (0)'
    def __bool__(self):
        return True

class VocabularyParsingCriticalFailure(VocabularyParsingStatusCode):
    """The parsing was interrupted after a critical error was met."""
    def __new__(cls):
        return super().__new__(cls, 1)
    def __str__(self):
        return 'critical failure (1)'
    def __bool__(self):
        return False

class VocabularyParsingCompletedWithErrors(VocabularyParsingStatusCode):
    """The parsing has been completed but some errors were met.

    Items that could not be parsed would have been skipped,
    so the parsing result might be incomplete.

    """
    def __new__(cls):
        return super().__new__(cls, 2)
    def __str__(self):
        return 'completed with errors (2)'
    def __bool__(self):
        return True

class VocabularyParsingResult:
    """Result of parsing of vocabulary raw data.

    Parameters
    ----------
    vocabulary : str
        Name of the vocabulary, ie its ``name``
        property in ``vocabularies.yaml``.

    Attributes
    ----------
    vocabulary : str
        Name of the vocabulary.

    """
    def __init__(self, vocabulary):
        self._exit = False
        self._log = []
        self._data = VocabularyDataCluster(vocabulary)
        self.vocabulary = vocabulary

    def exit(self, error=None):
        """Declare a critical parsing failure.
        
        Once this function as been used:

        * the :py:attr:`VocabularyParsingResult.data`
          property will always return ``None``, even
          if a vocabulary data cluster was registered
          before.
        
        * the :py:attr:`VocabularyParsingResult.status_code`
          property will return the code ``1``
          (:py:class:`VocabularyParsingCriticalFailure`).
        
        * it is not longer possible to log errors, so the
          last exception on the list will always be the critical
          failure.

        Parameters
        ----------
        error : Exception, optionnal
            :py:class:`Exception` object providing information
            about the critical failure. If this is not provided,
            it will be assumed that the error has been logged
            already.

        """
        if isinstance(error, Exception):
            self.log_error(error)
        self._exit = True

    @property
    def log(self):
        """list(Exception): List of errors met during parsing."""
        return self._log

    def log_error(self, error):
        """Log some non critical error met during parsing.

        Parameters
        ----------
        error : Exception
            :py:class:`Exception` object providing information
            about the error.
        
        """
        if not self._exit:
            if isinstance(error, Exception):
                self._log.append(error)

    @property
    def data(self):
        """VocabularyDataCluster or None: Structured parsed vocabulary data."""
        if not self._exit:
            return self._data
    
    @property
    def status_code(self):
        """VocabularyParsingStatusCode: Parsing status code.
        
        The status code is a customized integer.
        
        The string representation of the code is a literal
        description of the status.

        The boolean value of the code indicates if the
        parsing has provided some presumably usable data
        (even if it might be incomplete or need some
        validation).

        """
        if self._exit:
            return VocabularyParsingCriticalFailure()
        if self.log:
            return VocabularyParsingCompletedWithErrors()
        return VocabularyParsingSuccess()

    def add_label(self, *data, **kwdata):
        """Declare a label.
        
        Shortcut for :py:meth`VocabularyDataCluster.add_label`
        called on the cluster data, ie on the
        :py:attr:`VocabularyParsingResult.data` attribute.

        Validation anomalies met during execution - ie.
        when a "label" was not registred because there was
        no URI or no label in the provided data - are
        logged in the :py:attr:`VocabularyParsingResult.log`
        attribute, so the parser doesn't need to do it
        (even though they are returned as a result of this
        method).

        Returns
        -------
        DataValidationResponse
            If the boolean value of this is ``False``, the
            label has not been added to the cluster.

        """
        response = self.data.add_label(*data, **kwdata)
        if not response:
            for anomaly in response:
                self.log_error(exceptions.InvalidDataError(anomaly))
        return response

