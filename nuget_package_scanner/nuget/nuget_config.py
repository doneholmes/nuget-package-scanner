import logging
from typing import List

from lxml import etree

class Package:
    """
    Class for accessing nuget package metadata.
    """
    def __init__(self, name: str, version: str = "", target_framework: str = ""):
        assert isinstance(name, str)        
        self.name = name
        self.target_framework = target_framework
        self.version = version
        self.version_date = ""
        self.latest_release = "" # includes full release only   
        self.latest_release_date = ""
        self.latest_version = "" # includes prerelease and other builds
        self.latest_version_date = ""             
        self.major_releases_behind = 0
        self.minor_releases_behind = 0
        self.patch_releases_behind = 0
        self.available_version_count = 0
        self.source = ""
        self.details_url = ""
    
    def set_details_url(self, template_uri: str):
        if template_uri:
            self.details_url = template_uri.replace('{id}',str.lower(self.name)).replace('{version}', self.version)

    def __eq__(self, other):
        return self.name == other.name and self.version == other.version and self.target_framework == other.target_framework

    def __hash__(self):
        return hash((self.name, self.version, self.target_framework))    
        
class PackageContainer:
    """
    Base class for  a nuget package configuraion. Implementation of package parsing from the file contents
    is left up to the inheriting class.
    """
    def __init__(self, contents: str, name: str = '', repo = '', path = ''):
        assert contents is not None, ':param contents cannot be empty.'
        logging.debug(f'PackageContainer ctor() Repo: {repo} Path: {path}')
        self.name = name
        self.repo = repo   
        self.path = path        
        self.packages = self._load_packages(contents)

    def _load_packages(self, contents: str) -> List[Package]:
        return []

class PackageConfig(PackageContainer):
    """
    A class to load and access nuget package configurations from a .Net Framework packages.config file.
    """
    def __init__(self, contents, name='', repo='', path=''):
        super().__init__(contents, name, repo, path)
    
    def _load_packages(self, contents) -> List[Package]:
        root = etree.fromstring(_strip_declaration(contents))
        elements = root.findall(".//package")        
        packages = []      
        for element in elements:
            packages.append(Package(element.get("id"), element.get("version"), element.get("targetFramework")))
        return packages       

class NetCoreProject(PackageContainer):
    """
    A class to load and access nuget package configurations from a .Net core .csproj file.
    """
    def __init__(self, contents, name='', repo='', path=''):
        super().__init__(contents, name, repo, path)

    def _load_packages(self, contents) -> List[Package]: 
        root = etree.fromstring(_strip_declaration(contents))
        elements = root.findall(".//PackageReference")
        packages = []      
        for element in elements:            
            packages.append(Package(element.get("Include"),element.get("Version")))
        return packages     

def _strip_declaration(contents: str):
    """ Strips declaration from the file if there - lxml doesn't like it."""
    return str.replace(contents,r'<?xml version="1.0" encoding="utf-8"?>','').strip()

class NugetConfig:
    """
    A class to load and access nuget server source url configurations from a nuget.config file.
    """
    def __init__(self, contents: str): 
        assert contents is not None
        stripped = _strip_declaration(contents)        
        root = etree.fromstring(stripped)
        elements = root.findall(".//packageSources/add")
        self.indexes = {}        
        for element in elements:
            self.indexes[element.get("key")] = element.get("value")
