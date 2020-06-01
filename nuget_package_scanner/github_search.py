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
        response = await self.__client.get(f'https://api.github.com/rate_limit')
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
            return await response.text() 

    async def get_request_as_json(self, url: str) -> dict:
        async with await self.makeRequest(url) as response:

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
        details = await self.get_request_as_json(details_url)
        if details:
            sourceUrl = details["download_url"]                                  
            results.append(GithubSearchResult(name, repo_name, path, sourceUrl))            
    
    async def search_github_code(self, query, limit: Optional[int] = None) -> List[GithubSearchResult]:
        """ 
        Executes a github code search and returns the results in a list.
        Search results are paged - This call will likely result in multple requests to the api in
        order to aggregate all results.
        Note: There is currently no logic to account for search api rate limiting
        """
        search_results = []  
        response: aiohttp.ClientResponse = None      
        url = f'https://api.github.com/search/code?q={query}'
        result_count = 0
        while url:
            logging.info(f'Github Search Query: {url}')
            #TODO: Rate limiting checking while running
            response = await self.makeRequest(url)         
            results = await response.json()
            tasks = []

            for item in results["items"]:
                result_count += 1                
                tasks.append(asyncio.create_task(self.__process_search_page(item,search_results),name=f'__process_search_page[{url}]'))
                if isinstance(limit, int) and result_count >= limit:
                    await wait_or_raise(tasks)                      
                    return search_results  
            await wait_or_raise(tasks) 
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
        source = await self.get_request_as_text(result.url)        
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
        tasks = []
        results = await self.search_nuget_configs(org, limit)  
        configsByValue = {}    
        for r in results:        
            tasks.append(asyncio.create_task(self.__build_nuget_config(r, configsByValue),name=f'__build_nuget_config[{r.url}]'))
        await wait_or_raise(tasks)
        return configsByValue
