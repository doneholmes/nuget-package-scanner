
import logging
import os
import datetime
from typing import List,Optional

import requests

import nugetconfig


class GithubSearchResult:

    def __init__(self, name, repo, path, url):        
        self.name = name
        self.repo = repo
        self.path = path
        self.url = url        

class GithubClient:
    def __init__(self, token):        
        self.token = token

    def get_search_rate_limit_info(self):
        response = self.makeRequest(f'https://api.github.com/rate_limit')
        search = response.json()["resources"]["search"]
        github_reset = datetime.datetime.utcfromtimestamp(int(response.headers["X-RateLimit-Reset"]))
        search_reset = datetime.datetime.utcfromtimestamp(int(search["reset"]))
        print(f'Github Limit: { response.headers["X-RateLimit-Limit"] }')
        print(f'Github Remainig: { response.headers["X-RateLimit-Remaining"] }')
        print(f'Github Reset: { github_reset }')
        print(f'Search API Limit: { search["limit"] }')
        print(f'Search API Remainig: { search["remaining"] }')
        print(f'Search API Reset: { search_reset }')


    def makeRequest(self, url) -> requests.Response:    
        headers = {"Authorization" : f"token {self.token}"}         
        response = requests.get(url = url, headers = headers)
        limit = response.headers.get("X-RateLimit-Limit")
        remaining = response.headers.get("X-RateLimit-Remaining")
        logging.info(f'GET { url } | Limit: { limit } | Remaining: { remaining }')  
        response.raise_for_status()
        return response

    def getNextPageLink(self, response: requests.Response):
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

    def search_github_code(self, query, limit: Optional[int] = None) -> List[GithubSearchResult]:
        """ Executes a github code search and returns the results in a list. """
        search_results = []        
        url = f'https://api.github.com/search/code?q={query}'  
        while url:
            logging.info(f'Search Query: {url}')
            response = self.makeRequest(url)            
            results = response.json()["items"]

            for result in results:                        
                name = result["name"]
                repo_name = result["repository"]["name"]
                path = result["path"]        
                resultDetailsUrl = result["url"]
                resultDetails = self.makeRequest(resultDetailsUrl).json()
                sourceUrl = resultDetails["download_url"]                                  
                search_results.append(GithubSearchResult(name, repo_name, path, sourceUrl))
                if isinstance(limit, int) and len(search_results) >= limit:
                    return search_results
                          
            url = self.getNextPageLink(response)
        return search_results    

    def search_nuget_configs(self, org, limit: Optional[int] = None):      
        return self.search_github_code(f'packageSources+org:{org}+filename:nuget.config', limit)    

    def search_netcore_csproj(self, org, limit: Optional[int] = None):
        return self.search_github_code(f'PackageReference+org:{org}+extension:csproj', limit)

    def search_package_configs(self, org, limit: Optional[int] = None):
        return self.search_github_code(f'package+org:{org}+filename:packages.config', limit)

    def get_unique_nuget_configs(self, org, limit: Optional[int] = None):
        results = self.search_nuget_configs(org, limit)    
        configsByValue = {}    
        for result in results:
            source = self.makeRequest(result.url).text        
            nc = nugetconfig.NugetConfig(source)
            for i in nc.indexes:
                v = nc.indexes[i]
                if not configsByValue.get(v):
                    configsByValue[v] = i
        return configsByValue  
