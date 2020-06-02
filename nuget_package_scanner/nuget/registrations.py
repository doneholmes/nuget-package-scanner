import logging
from typing import List, Union

from ..smart_client import SmartClient

from .registrations_version import (RegistrationsVersion,
                                    RegistrationsVersionConfig)


class CatalogEntry:
    def __init__(self, json):
        self.url: str = json["@id"]
        self.id: str = json["id"]
        self.version: str = json["version"]
        
        self.authors: Union[str, List[str]] = json.get("authors")       
        self.depracation = json.get("deprecation")
        self.description: str = json.get("description")
        self.licenseUrl: str = json.get("licenseUrl")
        self.licenseExpression: str = json.get("licenseExpression")
        self.listed: bool = json.get("listed")
        self.minClientVersion: str = json.get("minClientVersion")
        self.projectUrl: str = json.get("projectUrl")
        self.published: str = json.get("published")
        self.requireLicenseAcceptance: bool = json.get("requireLicenseAcceptance")
        self.summary: str = json.get("summary")
        self.tags: Union[str, List[str]] = json.get("tags")
        self.title: str = json.get("title")

        self.dependencyGroups = json.get("dependencyGroups")        

class RegistrationLeaf:    
    def __init__(self, json):
        self.url: str = json["@id"]
        self.packageContent: str = json["@id"]
        self.catalogEntry = CatalogEntry(json["catalogEntry"])
        self.commitTimeStamp: str = json.get("commitTimeStamp")

class RegistrationPage:    
    def __init__(self, json, client: SmartClient):        
        self.url: str = json["@id"]
        self.count: int = json["count"]
        self.lower: str = json["lower"]
        self.parent: str = json.get("parent")
        self.upper: str = json["upper"]
        self.commitTimeStamp: str = json.get("commitTimeStamp")
        self.__set_items(json)
        self.__client = client     

    async def items(self) -> List[RegistrationLeaf]:
        """
        Gets or fetches every RegistrationLeaf for this page. This will require a Server API call to self.url if the items were not included originally.
        """
        if not self.__items:
            json = await self.__client.get_as_json(self.url)
            if json:
                self.__set_items(json)            
        
        return self.__items

    def __set_items(self,json):
        self.__items = []
        if json.get("items"):                  
            for i in json["items"]:
                self.__items.append(RegistrationLeaf(i)) 

class RegistrationsIndex:
    """
    Represents the Registration index resource.
    https://docs.microsoft.com/en-us/nuget/api/registration-base-url-resource#registration-index

    """    
    def __init__(self, json: dict, url: str, client: SmartClient):        
        assert isinstance(json, dict), f":param json must be a dict for url:{url} json:{json}"
        assert isinstance(url, str), f":param url must be a str. {url}"
        self.url = url
        self.count: int = json["count"]
        self.items: List[RegistrationPage] = []
        self.commitTimeStamp: str = json.get("commitTimeStamp")
        for i in json["items"]:
            self.items.append(RegistrationPage(i, client))        

class Registrations:
    """
    This class can be used to access nuget package registration data from the Server API.
    https://docs.microsoft.com/en-us/nuget/api/registration-base-url-resource
    """

    def __init__(self, service_index_json: dict, client: SmartClient):
        """        
        :param service_index_json The json response from the nuget service index endpoint.
        https://docs.microsoft.com/en-us/nuget/api/service-index
        """            
        self._version_config = RegistrationsVersionConfig(service_index_json)
        assert isinstance(client, SmartClient)
        self.__client = client
    
    async def index(self, package_id: str, service_version: RegistrationsVersion = RegistrationsVersion.RELEASE) -> RegistrationsIndex:
        assert isinstance(package_id, str), ":param package_id must be a str"
        url = f'{self._version_config.get_base_url(service_version)}{package_id.lower()}/index.json'
        json = await self.__client.get_as_json(url)
        if json:                        
            return RegistrationsIndex(json, url, self.__client)        
        return
