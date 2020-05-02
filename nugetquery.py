import logging
from typing import List

from lxml import etree

import nuget
import nugetconfig
import nugetversion

class NugetQuery:

    def __init__(self, configs: dict = {}):        
        self._configs = configs
        self._clients_cache = [] # type: List[nuget.Nuget]
        self._package_cache = {}
    
    @property
    def __clients(self):
        return self.__get_clients()

    def __get_clients(self):
        if self._clients_cache:
            return self._clients_cache        
        self._clients_cache.append(nuget.Nuget()) # ensuring that nuget.org is added first
        for c in self._configs:
            self._clients_cache.append(nuget.Nuget(c))

        return self._clients_cache

    
    def get_fetch_package_details(self, package: nugetconfig.Package) -> nugetconfig.Package:
        """
        Attempts to ge the package from cache, then falls back to a nuget server query if not found.
        If a server query is attempted, this fetches nuget package details from the first :class nuget.RegistrationsIndex found
        for :param package. The strategy is to first search for package registrations at nuget.org and then 
        to cycle through any :param configs that have been provided.
        """
        assert isinstance(package, nugetconfig.Package)
        package_hash = hash(package)                           
        if not self._package_cache.get(package_hash): # we don't have cache, query for details
            registrations_index = self.__fetch_index_from_nuget_configs(package.name)
            if registrations_index: # we found it. TODO: Possibly cash unfound packages as well or just let them re-query?
                package.source = registrations_index.url
                self.__fetch_and_populate_version(registrations_index, package)
                self.__fetch_and_populate_latest_release(registrations_index, package)
                self.__fetch_and_populate_latest_version(registrations_index, package)           
                self._package_cache[package_hash] = package
            else:
                logging.info(f'Could not find {package.name}({package_hash}) in any of the configured nuget servers.')
        else: # copy values from cache
            # TODO: This smells a bit
            package.version_date = self._package_cache[package_hash].version_date
            package.latest_version = self._package_cache[package_hash].latest_version
            package.latest_version_date = self._package_cache[package_hash].latest_version_date
            package.latest_release = self._package_cache[package_hash].latest_release 
            package.latest_release_date = self._package_cache[package_hash].latest_release_date
            package.source = "cache"

    def __fetch_index_from_nuget_configs(self, id: str) -> nuget.RegistrationsIndex:
        """
        Returns the first :type nuget.RegistrationsIndex found for the provided :param id.
        The strategy is to first search for package registrations at nuget.org and then 
        to cycle through any :param configs that have been provided.    
        :param configs: A :class:dict  that contains non-nuget.org server implementations to query
        :param id: A :class:dict  that contains non-nuget.org server implementations to query
        """
        ## TODO: Maybe optimize for preferred ordering in some cases?
        for c in self.__clients:
            index = c.registrations.index(id)                
            if index:
                return index        

    # TODO: Optimize?
    def __fetch_and_populate_version(self, registrationsIndex: nuget.RegistrationsIndex, package: nugetconfig.Package):
        if registrationsIndex and package.version:
            for page in registrationsIndex.items:                            
                if not nugetversion.is_newer_release(page.upper, package.version):
                    for leaf in page.items():
                        if leaf.catalogEntry.version == package.version:
                            package.version_date = leaf.commitTimeStamp                                                        
                            return

    def __fetch_and_populate_latest_version(self, registrationsIndex: nuget.RegistrationsIndex, package: nugetconfig.Package):
        # current version metadata
        if registrationsIndex:
            # assumption newest at the end
            for page in reversed(registrationsIndex.items):                                
                for leaf in reversed(page.items()):                    
                    package.latest_version = leaf.catalogEntry.version 
                    package.latest_version_date = leaf.commitTimeStamp
                    return                         

    def __fetch_and_populate_latest_release(self, registrationsIndex: nuget.RegistrationsIndex, package: nugetconfig.Package):
        # current version metadata
        if registrationsIndex:
            # assumption newest at the end
            for page in reversed(registrationsIndex.items):                                
                for leaf in reversed(page.items()):
                    if nugetversion.is_full_release(leaf.catalogEntry.version):
                        package.latest_release = leaf.catalogEntry.version 
                        package.latest_release_date = leaf.commitTimeStamp
                        return
