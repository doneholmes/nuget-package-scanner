import datetime
import functools
import logging
from enum import Enum
from typing import AsyncGenerator, List, Union

from ..smart_client import SmartClient

import nuget_package_scanner.nuget
import nuget_package_scanner.nuget.date_util as date_util
import nuget_package_scanner.nuget.version_util as version_util

from .nuget_server import NugetServer
from .nuget_config import Package
from .registrations import RegistrationsIndex
from .version_util import VersionPart


class Nuget:
    """
    Nuget client that can be used to retrieve package registration info from multiple Nuget Servers.    
    """
    async def __aenter__(self):
        await self.initialize_clients()
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        return

    def __init__(self, client: SmartClient, configs: dict = {}): 
        """
        Initializes the client.
        param: configs Additional Nuget servers to search if a package is not found on nuget.org.\n
            key: Nuget server server index url
            value: Name
        """      
        self._configs = configs
        self._clients_cache: List[NugetServer] = []
        self._package_cache = {}
        self._client = client  
    
    async def initialize_clients(self):          
        clients = await self.__get_clients()        
        for c in clients:
            logging.info(f'Initialized Nuget Server API @ {c.index_url}')    

    async def __get_clients(self):
        if self._clients_cache:
            return self._clients_cache        
        self._clients_cache.append(await NugetServer.create(self._client)) # ensuring that nuget.org is added first
        for c in self._configs:
            self._clients_cache.append(await NugetServer.create(self._client,c))

        return self._clients_cache   
    
    async def get_fetch_package_details(self, package: Package):
        """
        Attempts to ge the package from cache, then falls back to a nuget server query if not found.
        If a server query is attempted, this fetches nuget package details from the first :class nuget.RegistrationsIndex found
        for :param package. The strategy is to first search for package registrations at nuget.org and then 
        to cycle through any :param configs that have been provided.
        """
        assert isinstance(package, Package)        
        nuget_server: NugetServer = await self.__fetch_server_for_id(package.name)
        # Note: If you're wondering where caching is at, it's on in the client
        if nuget_server:
            registrations_index = await nuget_server.registrations.index(package.name) # will already be cached
            package.source =  registrations_index.url            
            await self.__fetch_and_populate_version(registrations_index, package)
            await self.__fetch_and_populate_latest_release(registrations_index, package)
            await self.__fetch_and_populate_latest_version(registrations_index, package)
            package.available_version_count = self.__get_available_package_count(registrations_index)
            if package.version and package.latest_release:                
                version_diff = version_util.get_version_count_behind(package.version, package.latest_release)
                package.major_releases_behind = version_diff[VersionPart.MAJOR]
                package.minor_releases_behind = version_diff[VersionPart.MINOR]
                package.patch_releases_behind = version_diff[VersionPart.PATCH]
                package.set_details_url(nuget_server.package_uri_template)
        else:
            logging.warn(f'Could not find {package.name} in any of the configured nuget servers.')

    async def __fetch_server_for_id(self, id: str) -> NugetServer:
        """
        Returns the first :type nuget.NugetServer that houses the provided :param id.
        The strategy is to first search for package registrations at nuget.org and then 
        to cycle through any :param configs that have been provided.    
        :param configs: A :class:dict  that contains non-nuget.org server implementations to query
        :param id: A :class:dict  that contains non-nuget.org server implementations to query
        """
        ## TODO: Allow for preferred ordering in some cases? You may have a convention or some other means that allows you to know exactly which server to query.
        for c in await self.__get_clients():
            index = await c.registrations.index(id)                
            if index:
                return c        

    # TODO: Potentially optimize these
    async def __fetch_and_populate_version(self, registrationsIndex: RegistrationsIndex, package: Package):
        if registrationsIndex and package.version:
            for page in registrationsIndex.items:                            
                if not version_util.is_newer_release(page.upper, package.version):
                    for leaf in await page.items():
                        if leaf.catalogEntry.version == package.version and leaf.commitTimeStamp:
                            package.version_date = date_util.get_date_from_iso_string(leaf.commitTimeStamp).strftime('%Y-%m-%d')
                            return

    async def __fetch_and_populate_latest_version(self, registrationsIndex: RegistrationsIndex, package: Package):
        # current version metadata
        if registrationsIndex:
            # assuming the newest is aways at the end of the list
            for page in reversed(registrationsIndex.items):                                
                for leaf in reversed(await page.items()):                    
                    package.latest_version = leaf.catalogEntry.version
                    if leaf.commitTimeStamp:
                        package.latest_version_date = date_util.get_date_from_iso_string(leaf.commitTimeStamp).strftime('%Y-%m-%d')
                    return                         

    async def __fetch_and_populate_latest_release(self, registrationsIndex: RegistrationsIndex, package: Package):
        # current version metadata
        if registrationsIndex:
            # assuming the newest is aways at the end of the list
            for page in reversed(registrationsIndex.items):                                
                for leaf in reversed(await page.items()):
                    if version_util.is_full_release(leaf.catalogEntry.version):
                        package.latest_release = leaf.catalogEntry.version 
                        if leaf.commitTimeStamp:
                            package.latest_release_date = date_util.get_date_from_iso_string(leaf.commitTimeStamp).strftime('%Y-%m-%d')
                        return

    def __get_available_package_count(self, registrationsIndex: RegistrationsIndex) -> int:
        count = 0
        if registrationsIndex:         
            for page in registrationsIndex.items:
                count += page.count 
        return count
