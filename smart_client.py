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
        await self.close()

    def __init__(self, headers: Optional[dict] = None, timeout: Optional[int] = 15):
        self.headers=headers
        self.timeout = aiohttp.ClientTimeout(total=timeout) if timeout else aiohttp.ClientTimeout()             
        
    def get_aiohttp_client(self, url: str) -> aiohttp.ClientSession:        
        u = urlparse(url)
        key = f'{u.scheme}{u.netloc}'        
        if self.clients.get(key) is None:
            conn = aiohttp.TCPConnector(limit=500)         
            self.clients[key] = aiohttp.ClientSession(headers=self.headers,timeout=self.timeout, connector=conn)
        return self.clients[key]
    
    async def close(self):
        print(f'Closing {len(self.clients)} sessions...')
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        for key in self.clients.keys():
            print(f'Closing {key} session...')
            await self.clients[key].close()
        self.clients = {}
    
    @alru_cache(maxsize=None)
    async def get_as_text(self, url: str, ignore_404 = True) -> str:
        result = await self.get(url, ignore_404)
        if result:
            text = await result.text()
            result.close()
            return text
        return
    
    @alru_cache(maxsize=None)    
    async def get_as_json(self, url: str, ignore_404 = True) -> dict:
        result = await self.get(url, ignore_404)
        if result:
            json = await result.json()
            result.close()
            return json
        return
    
    async def get(self, url: str, ignore_404 = True, log_success = True) -> aiohttp.ClientResponse:             
        assert isinstance(url, str) and url, "url must be a non-empty string"
        client = self.get_aiohttp_client(url)
        try:
            response = await client.get(url)
            if ignore_404 and response.status == 404:
                logging.info(f'404 GET {url}')
                return                    
            if response.status != 200:
                raise response.raise_for_status()
            if log_success:
                logging.info(f'200 GET {url}')     
            return response          
        except asyncio.TimeoutError:
            logging.error(f'Timeout Error {url}')
        except Exception as e:            
            logging.exception(e)
            raise e
        return
