import logging
from enum import Enum
import functools
from typing import List, Union

from .nugetconfig import Package
from .nuget_server import NugetServer
from .registrations import RegistrationsIndex
import nuget.version_util as version_util

class Nuget:
    """
    Nuget client that can be used to retrieve package registration info from multiple Nuget Servers.    
    """
    def __init__(self, configs: dict = {}):  
        """
        Initializes the client.
        param: configs Additional Nuget servers to search if a package is not found on nuget.org.\n
            key: Nuget server server index url
            value: Name
        """      
        self._configs = configs
        self._clients_cache = [] # type: List[nuget.Nuget]
        self._package_cache = {}
    
    @property
    def __clients(self):
        return self.__get_clients()

    def __get_clients(self):
        if self._clients_cache:
            return self._clients_cache        
        self._clients_cache.append(NugetServer()) # ensuring that nuget.org is added first
        for c in self._configs:
            self._clients_cache.append(NugetServer(c))

        return self._clients_cache

    
    def get_fetch_package_details(self, package: Package):
        """
        Attempts to ge the package from cache, then falls back to a nuget server query if not found.
        If a server query is attempted, this fetches nuget package details from the first :class nuget.RegistrationsIndex found
        for :param package. The strategy is to first search for package registrations at nuget.org and then 
        to cycle through any :param configs that have been provided.
        """
        assert isinstance(package, Package)        
        registrations_index = self.__fetch_index_from_nuget_configs(package.name)
        #Note: I originally had some manual memoization here, but moved that caching to the request_wrapper class using built-in functools support
        if registrations_index:           
            package.source = registrations_index.url
            self.__fetch_and_populate_version(registrations_index, package)
            self.__fetch_and_populate_latest_release(registrations_index, package)
            self.__fetch_and_populate_latest_version(registrations_index, package)                       
        else:
            logging.info(f'Could not find {package.name} in any of the configured nuget servers.')        

    def __fetch_index_from_nuget_configs(self, id: str) -> RegistrationsIndex:
        """
        Returns the first :type nuget.RegistrationsIndex found for the provided :param id.
        The strategy is to first search for package registrations at nuget.org and then 
        to cycle through any :param configs that have been provided.    
        :param configs: A :class:dict  that contains non-nuget.org server implementations to query
        :param id: A :class:dict  that contains non-nuget.org server implementations to query
        """
        ## TODO: Allow for preferred ordering in some cases? You may have a convention or some other means that allows you to know exactly which server to query.
        for c in self.__clients:
            index = c.registrations.index(id)                
            if index:
                return index        

    # TODO: Potentially optimize these
    def __fetch_and_populate_version(self, registrationsIndex: RegistrationsIndex, package: Package):
        if registrationsIndex and package.version:
            for page in registrationsIndex.items:                            
                if not version_util.is_newer_release(page.upper, package.version):
                    for leaf in page.items():
                        if leaf.catalogEntry.version == package.version:
                            package.version_date = leaf.commitTimeStamp                                                        
                            return

    def __fetch_and_populate_latest_version(self, registrationsIndex: RegistrationsIndex, package: Package):
        # current version metadata
        if registrationsIndex:
            # assuming the newest is aways at the end of the list
            for page in reversed(registrationsIndex.items):                                
                for leaf in reversed(page.items()):                    
                    package.latest_version = leaf.catalogEntry.version 
                    package.latest_version_date = leaf.commitTimeStamp
                    return                         

    def __fetch_and_populate_latest_release(self, registrationsIndex: RegistrationsIndex, package: Package):
        # current version metadata
        if registrationsIndex:
            # assuming the newest is aways at the end of the list
            for page in reversed(registrationsIndex.items):                                
                for leaf in reversed(page.items()):
                    if version_util.is_full_release(leaf.catalogEntry.version):
                        package.latest_release = leaf.catalogEntry.version 
                        package.latest_release_date = leaf.commitTimeStamp
                        return


