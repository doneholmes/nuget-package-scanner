import asyncio
import logging
from typing import Dict, Optional
from urllib.parse import urlparse
import urllib.parse

import aiohttp
from async_lru import alru_cache
from tenacity import before_log, retry, retry_if_exception_type, stop_after_attempt, wait_random, TryAgain


class SmartClient:
    '''
    Wrapper built around the aiohttp.ClientSession. This class is designed to provide robust and performant
    IO in the case where you need to make many calls to several servers potentially simultaneously. 
    
    The get method includes some basic retry logic that should cover the case in which a resource is temporarily
    unavailable and is not memoized. The get_as_json and get_as_text methods are memoized and will only result
    in 1 external call to fetch the matching resource per application session. See async_lru documentation for a
    a description of how to flush cache if necessary.

    >>> async with SmartClient() as sc
    >>>     # initial call to server is wrapped in retry logic (will retry 3 times)
    >>>     response_json = await sc.get_as_json('http://site.com/resource')
    >>>     # subsequent call is retrieved from cache
    >>>     response_json2 = await sc.get_as_json('http://site.com/resource')
    '''
    clients: Dict[str, aiohttp.ClientSession] = {} # Dictionary to cache clients per base url to better support connection pooling    
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        # The following 2 close() methods are present as a result of the methods being wrapped by alru_cache
        # pylint: disable=no-member        
        await self.get_as_text.close()
        await self.get_as_json.close()
        # pylint: enable=no-member
        await self.close()                     
        
    def get_aiohttp_client(self, url: str) -> aiohttp.ClientSession:        
        u = urlparse(url)
        key = f'{u.scheme}{u.netloc}'        
        if self.clients.get(key) is None:
            conn = aiohttp.TCPConnector(limit=100) #TODO: Dial in pool size
            timeout = aiohttp.ClientTimeout(total=20) #TODO: Dial in timeout
            self.clients[key] = aiohttp.ClientSession(connector=conn,timeout=timeout)
        return self.clients[key]
    
    async def close(self):
        print(f'Closing {len(self.clients)} client sessions...')        
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        for key in self.clients.keys():
            print(f'Closing {key} client session...')
            await self.clients[key].close()
        self.clients = {}
    
    @alru_cache(maxsize=None)
    async def get_as_text(self, url: str, ignore_404 = True,  headers: Optional[dict] = None) -> str:
        response = await self.get(url, ignore_404, headers)
        if response:
            async with response:      
                return await response.text()        
    
    @alru_cache(maxsize=None)    
    async def get_as_json(self, url: str, ignore_404 = True, headers: Optional[dict] = None) -> dict:
        response = await self.get(url, ignore_404, headers)
        if response:
            async with response:      
                return await response.json()            

    # Retry a few times in the event that it's some kind of connection error or 5xx error
    # This method should not retry in the event of any 4xx errors
    @retry(stop=stop_after_attempt(3), retry=retry_if_exception_type(TryAgain), \
        wait=wait_random(min=1, max=3), before=before_log(logging.getLogger(), logging.DEBUG))
    async def get(self, url: str, ignore_404 = True, headers: Optional[dict] = None) -> aiohttp.ClientResponse:             
        assert isinstance(url, str) and url, "url must be a non-empty string"
        client = self.get_aiohttp_client(url)
        try:
            response = await client.get(url,headers=headers)
            if ignore_404 and response.status == 404:
                logging.debug(f'404 GET {url}')
                return            
            if response.status != 200:             
                raise response.raise_for_status()            
            logging.debug(f'200 GET {url}')     
            return response        
        except aiohttp.ClientResponseError as e:            
            logging.exception(e)
            raise e if e.status < 500 else TryAgain # Explicit call to retry for 5xx errors

