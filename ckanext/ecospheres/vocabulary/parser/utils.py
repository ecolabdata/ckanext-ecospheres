"""Utilitary functions for vocabulary parsing."""

import requests

def fetch_data(url, format='json', **kwargs):
        """Uses the requests module to get some data.

        This function will raise any possible HTTP error,
        JSON parsing error, etc. so the vocabulary parser can
        either:

        * Log the error (as a critical failure or not).

        * Be assured that some proper data has been
          returned.

        For instance, if getting the data is required
        for the parsing to succeed:

            >>> result = VocabularyParsingResult()
            >>> try:
            ...     data = fetch_data(some_url)
            ... except Exception as error:
            ...     result.exit(error)
            ...     return result

        If the parser has a work around, the error
        will just be logged:

            >>> result = VocabularyParsingResult()
            >>> try:
            ...     data = fetch_data(some_url)
            ... except Exception as error:
            ...     result.log_error(error)

        Parameters
        ----------
        url : str
            The URL to request to.
        format : {'json', 'text', 'bytes'}, optional
            The expected format for the result.
        **kwargs
            Any nammed parameter to pass to the
            :py:func:`requests.get` function.

        Returns
        -------
        dict or list or str or bytes
            The type of the result depends on the
            `format` parameter.

        """
        response = requests.get(url, **kwargs)
        response.raise_for_status()

        if format == 'text':
            return response.text
        
        if format == 'bytes':
            return response.content
        
        return response.json()

