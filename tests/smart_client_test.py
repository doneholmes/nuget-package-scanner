import aiohttp
import asyncio
import tenacity
import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from nuget_package_scanner.smart_client import SmartClient


class TestSmartClient(IsolatedAsyncioTestCase):    

    async def asyncSetUp(self):        
        self.sc = SmartClient()

    async def asyncTearDown(self):
        # Clear alru_cache after each test
        # pylint: disable=no-member        
        self.sc.get_as_json.cache_clear()
        self.sc.get_as_text.cache_clear()
        # pylint: enable=no-member
        await self.sc.close()
                  
    async def test_get_empty(self):   
        c = MagicMock(aiohttp.ClientSession)    
        c.get = AsyncMock()
        self.sc.get_aiohttp_client = MagicMock(return_value=c)
        with self.assertRaises(AssertionError):
            await self.sc.get('')    
    
    async def test_get_200(self):        
        c = MagicMock(aiohttp.ClientSession)
        r = MagicMock(aiohttp.ClientResponse)
        r.status = 200
        c.get = AsyncMock(return_value=r)                
        self.sc.get_aiohttp_client = MagicMock(return_value=c)
        response = await self.sc.get('some url here')
        c.get.assert_awaited_once()
        r.raise_for_status.assert_not_called()
        self.assertEqual(response,r)

    async def test_get_404_default(self):        
        c = MagicMock(aiohttp.ClientSession)
        r = MagicMock(aiohttp.ClientResponse)
        r.status = 404
        c.get = AsyncMock(return_value=r)                
        self.sc.get_aiohttp_client = MagicMock(return_value=c)
        response = await self.sc.get('some url here')
        c.get.assert_awaited_once()
        r.raise_for_status.assert_not_called()
        self.assertIsNone(response)

    async def test_get_as_json_is_cached(self):        
        c = MagicMock(aiohttp.ClientSession)
        r = MagicMock(aiohttp.ClientResponse)
        url = "something hashable for alru_cache"
        value = {"the expected": "return value for the test"}
        r.json = AsyncMock(return_value=value)
        r.status = 200
        c.get = AsyncMock(return_value=r)                
        self.sc.get_aiohttp_client = MagicMock(return_value=c)
        response = await self.sc.get_as_json(url)
        response2 = await self.sc.get_as_json(url)
        c.get.assert_awaited_once() # second should come from cache
        r.raise_for_status.assert_not_called()
        self.assertEqual(response,response2)

    async def test_get_as_text_is_cached(self):        
        c = MagicMock(aiohttp.ClientSession)
        r = MagicMock(aiohttp.ClientResponse)
        url = "something hashable for alru_cache"
        value = "the expected return value for the test"
        r.text = AsyncMock(return_value=value)
        r.status = 200
        c.get = AsyncMock(return_value=r)                
        self.sc.get_aiohttp_client = MagicMock(return_value=c)
        response = await self.sc.get_as_text(url)
        response2 = await self.sc.get_as_text(url)
        c.get.assert_awaited_once() # second should come from cache
        r.raise_for_status.assert_not_called()
        self.assertEqual(response,response2)

    async def test_get_aiohttp_client_cached(self):
        url = "https://a.url.here"     
        client = self.sc.get_aiohttp_client(url)
        client2 = self.sc.get_aiohttp_client(url)
        self.assertEqual(client,client2)
        self.assertEqual(len(self.sc.clients),1)

    async def test_get_aiohttp_client_not_cached(self):
        url = "https://a.url.here"
        url2 = "https://a.url.over.there"
        client = self.sc.get_aiohttp_client(url)
        client2 = self.sc.get_aiohttp_client(url2)
        self.assertNotEqual(client,client2)
        self.assertEqual(len(self.sc.clients),2)
       
    async def test_get_is_retried_for_5xx(self):        
        c = MagicMock(aiohttp.ClientSession)                           
        c.get = AsyncMock(side_effect=aiohttp.ClientResponseError(None,None,status=500))                
        self.sc.get_aiohttp_client = MagicMock(return_value=c)
        with self.assertRaises(tenacity.RetryError):
            await self.sc.get('https://a.url.here')
        self.assertTrue(c.get.await_count > 1)

    async def test_get_is_not_retried_for_4xx(self):
        c = MagicMock(aiohttp.ClientSession)                           
        c.get = AsyncMock(side_effect=aiohttp.ClientResponseError(None,None,status=422))                
        self.sc.get_aiohttp_client = MagicMock(return_value=c)
        with self.assertRaises(aiohttp.ClientResponseError):
            await self.sc.get('https://a.url.here')
        c.get.assert_awaited_once()

        
if __name__ == '__main__':
    unittest.main()
