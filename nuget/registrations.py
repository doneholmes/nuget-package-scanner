import logging
from typing import List, Union
from .registrations_version import RegistrationsVersion
from .registrations_version import RegistrationsVersionConfig
import nuget.request_wrapper

class CatalogEntry:
    def __init__(self, json):
        self.url = json["@id"] # type: str
        self.id = json["id"] # type: str
        self.version = json["version"] # type: str
        
        self.authors = json.get("authors") # type: Union[string,List[string]]        
        self.depracation = json.get("deprecation")
        self.description = json.get("description") # type: str
        self.licenseUrl = json.get("licenseUrl") # type: str
        self.licenseExpression = json.get("licenseExpression") # type: str
        self.listed = json.get("listed") # type: bool
        self.minClientVersion = json.get("minClientVersion") # type: str
        self.projectUrl = json.get("projectUrl") # type: str
        self.published = json.get("published") # type: str
        self.requireLicenseAcceptance = json.get("requireLicenseAcceptance") # type: bool
        self.summary = json.get("summary") # type: str
        self.tags = json.get("tags") # type: Union[string,List[string]]
        self.title = json.get("title") # type: str

        self.dependencyGroups = json.get("dependencyGroups")        

class RegistrationLeaf:    
    def __init__(self, json):
        self.url = json["@id"] # type: str
        self.packageContent = json["@id"] # type: str
        self.catalogEntry = CatalogEntry(json["catalogEntry"])
        self.commitTimeStamp = json.get("commitTimeStamp") # type: str

class RegistrationPage:    
    def __init__(self, json):        
        self.url = json["@id"] # type: str
        self.count = json["count"] #type: int            
        self.lower = json["lower"] # type: str
        self.parent = json.get("parent") # type: str
        self.upper = json["upper"] # type: str
        self.commitTimeStamp = json.get("commitTimeStamp") # type: str
        self.__set_items(json)        

    def items(self) -> List[RegistrationLeaf]:
        """
        Gets or fetches every RegistrationLeaf for this page. This will require a Server API call to self.url if the items were not included originally.
        """
        if not self.__items:            
            self.__set_items(nuget.request_wrapper.get_request(self.url))  
        
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
    def __init__(self, json: dict, url: str):
        super().__init__()
        assert isinstance(json, dict), ":param json must be a dict"
        assert isinstance(url, str), ":param url must be a str"
        self.url = url
        self.count = json["count"] #type: int
        self.items = [] #type: List[RegistrationPage]
        self.commitTimeStamp = json.get("commitTimeStamp") # type: str
        for i in json["items"]:
            self.items.append(RegistrationPage(i))

class Registrations:
    """
    This class can be used to access nuget package registration data from the Server API.
    https://docs.microsoft.com/en-us/nuget/api/registration-base-url-resource
    """

    def __init__(self, service_index_json: dict):
        """        
        :param service_index_json The json response from the nuget service index endpoint.
        https://docs.microsoft.com/en-us/nuget/api/service-index
        """            
        self._version_config = RegistrationsVersionConfig(service_index_json)        
    
    def index(self, package_id: str, service_version: RegistrationsVersion = RegistrationsVersion.RELEASE) -> RegistrationsIndex:
        assert isinstance(package_id, str), ":param package_id must be a str"
        url = f'{self._version_config.get_base_url(service_version)}{package_id.lower()}/index.json'
        index_data = nuget.request_wrapper.get_request(url)
        return RegistrationsIndex(index_data, url) if index_data else None