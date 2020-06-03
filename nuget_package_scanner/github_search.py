import asyncio
import datetime
import logging
import os
from typing import AsyncGenerator, List, Optional, Set

import aiohttp

from .smart_client import SmartClient
from .async_utils import wait_or_raise
from .nuget import NugetConfig


class GithubSearchResult:
    def __init__(self, name, repo, path, url):        
        self.name = name
        self.repo = repo
        self.path = path
        self.url = url        

class GithubClient:
         
    def __init__(self, token, client: SmartClient): 
        assert isinstance(token, str) and token
        self.headers = {"Authorization" : f"token {token}"}
        self.__client: SmartClient = client

    async def get_search_rate_limit_info(self) -> None:
        response = await self.__client.get(f'https://api.github.com/rate_limit', False, self.headers)
        response_json = await response.json()
        search = response_json["resources"]["search"]
        github_reset = datetime.datetime.utcfromtimestamp(int(response.headers["X-RateLimit-Reset"]))
        search_reset = datetime.datetime.utcfromtimestamp(int(search["reset"]))
        print(f'Github Limit: { response.headers["X-RateLimit-Limit"] }')
        print(f'Github Remainig: { response.headers["X-RateLimit-Remaining"] }')
        print(f'Github Reset: { github_reset }')
        print(f'Search API Limit: { search["limit"] }')
        print(f'Search API Remainig: { search["remaining"] }')
        print(f'Search API Reset: { search_reset }')        
    
    async def get_request_as_text(self, url: str) -> str:
        async with await self.makeRequest(url) as response:            
            return await response.text() #TODO There is an occassional issue with reading the response            

    async def get_request_as_json(self, url: str) -> dict:
        async with await self.makeRequest(url) as response:            
            return await response.json()                                            

    async def makeRequest(self, url) -> aiohttp.ClientResponse:        
        response = await self.__client.get(url, False, self.headers)        
        limit = response.headers.get("X-RateLimit-Limit")
        remaining = response.headers.get("X-RateLimit-Remaining")
        logging.debug(f'GET { url } | Limit: { limit } | Remaining: { remaining }')          
        return response

    def __getNextPageLink(self, response: aiohttp.ClientResponse) -> str:
        nextPage = ""
        RELNEXT = "; rel=\"next\""
        linkHeader = response.headers.get("Link")
        if linkHeader is not None:
            links = linkHeader.split(",")
            for l in links:
                if(l.endswith(RELNEXT)):
                    nextPage = l.replace(RELNEXT, "").replace("<","").replace(">","").strip()
                    break
        return nextPage

    async def __process_search_page(self, item_json, results: List[GithubSearchResult]) -> None:                                
        name = item_json["name"]
        repo_name = item_json["repository"]["name"]
        path = item_json["path"]        
        details_url = item_json["url"]
        try:     
            details = await self.get_request_as_json(details_url)
        except aiohttp.ClientPayloadError:
            # https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientPayloadError
            logging.warning(f'Failed to read (and therefore skipped) details_url json for search result response {details_url}')
        if details:
            sourceUrl = details["download_url"]                                  
            results.append(GithubSearchResult(name, repo_name, path, sourceUrl))     
    
    async def search_github_code(self, query, limit: Optional[int] = None) -> List[GithubSearchResult]:
        """ 
        Executes a github code search and returns the results in a list.
        Search results are paged - This call will likely result in multple requests to the api in
        order to aggregate all results. This call runs serially as it's explicity requested in
        the Gihub API documentation (link below).

        Note: There is currently no logic to account for search api rate limiting. The github search
        API will occassionally truncate responses based on how expensive the search call is on their
        backend. This can produce unexpected results.
        https://developer.github.com/v3/search/#timeouts-and-incomplete-results
        https://developer.github.com/changes/2014-04-07-understanding-search-results-and-potential-timeouts/
        Explicit ask to not make calls for a user concurrently
        https://developer.github.com/v3/guides/best-practices-for-integrators/#dealing-with-abuse-rate-limits
        """
        search_results = []  
        response: aiohttp.ClientResponse = None      
        url = f'https://api.github.com/search/code?q={query}'
        result_count = 0
        while url:
            logging.info(f'Github Search Query: {url}')
            #TODO: Bettter limiting checking while running. Currently, this will just bomb when the client
            # throws an exception.
            response = await self.makeRequest(url)         
            results = await response.json()            

            if results["incomplete_results"] is True:
                logging.debug(f'Incomplete results returned for code search query.')

            for item in results["items"]:
                result_count += 1                
                await self.__process_search_page(item,search_results)
                if isinstance(limit, int) and result_count >= limit:                                     
                    return search_results              
            url = self.__getNextPageLink(response)     
        response.release()
        return search_results    

    async def search_nuget_configs(self, org, limit: Optional[int] = None) -> List[GithubSearchResult]:      
        return await self.search_github_code(f'packageSources+org:{org}+filename:nuget.config', limit)    

    async def search_netcore_csproj(self, org, limit: Optional[int] = None) -> List[GithubSearchResult]:
        return await self.search_github_code(f'PackageReference+org:{org}+extension:csproj', limit)

    async def search_package_configs(self, org, limit: Optional[int] = None) -> List[GithubSearchResult]:
        return await self.search_github_code(f'package+org:{org}+filename:packages.config', limit)   
    
    async def __build_nuget_config(self, result: GithubSearchResult, configs: dict) -> None:
        try:      
            source = await self.get_request_as_text(result.url)
        except aiohttp.ClientPayloadError:
            # https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientPayloadError
            logging.warning(f'Failed to read (and therefore skipped) nuget.config source from {result.url}')
        nc = NugetConfig(source)
        for i in nc.indexes:
            v = nc.indexes[i]
            if not configs.get(v):
                configs[v] = i        
        return
        
    async def get_unique_nuget_configs(self, org, limit: Optional[int] = None) -> dict:
        """
        Returns a dict of nuget servers where the key is the server url and the value is the name given in the config
        """        
        results = await self.search_nuget_configs(org, limit)  
        configsByValue = {}
        tasks = []
        for r in results:        
            tasks.append(asyncio.create_task(self.__build_nuget_config(r, configsByValue),name=f'{r.url}'))
        await asyncio.wait(tasks)
        return configsByValue
