import asyncio
import logging
from typing import Dict, Optional
from urllib.parse import urlparse
import urllib.parse

import aiohttp
from async_lru import alru_cache


class SmartClient:    
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
            conn = aiohttp.TCPConnector(limit=50) #TODO: Dial in pool size        
            self.clients[key] = aiohttp.ClientSession(connector=conn)
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
            raise
        return
