import functools
import logging

import requests

@functools.lru_cache(maxsize=None) # memoization
def get_request(url) -> dict:
    """
    Returns the json object response or nothing in the case of a 404.
    """
    logging.info(f'GET {url}')
    response = requests.get(url = url)
        
    if response.status_code == 404:
        return

    if response.status_code != 200:        
        response.raise_for_status()         
    
    return response.json()
    
