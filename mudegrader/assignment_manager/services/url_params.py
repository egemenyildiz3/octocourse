from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def add_query_params(url, params):
    """Add or replace query parameters to the URL.
    Example: add ?saved=true to url when saving a form

    Args:
        url (str): The original URL.
        params (dict): Dictionary of query parameters to add or replace.

    Returns:
        str: The modified URL with the new query parameters.
    """
    # Parse the URL into components
    url_parts = list(urlparse(url))
    # Parse the query part of the URL into a dictionary
    query = parse_qs(url_parts[4])
    # Update the dictionary with the new parameters
    query.update(params)
    # URL-encode the query dictionary and set it as the new query string
    url_parts[4] = urlencode(query, doseq=True)
    # Reconstruct the URL from components
    return urlunparse(url_parts)