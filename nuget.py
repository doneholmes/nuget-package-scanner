import logging
from enum import Enum
import functools
from typing import List, Union

import requests

def get_request(url, ignore_codes: List[int] = [404]) -> dict:
    logging.info(f'GET {url}')
    response = requests.get(url = url)
        
    if response.status_code != 200 and response.status_code not in ignore_codes:
        response.raise_for_status()    

    return response.json() if response.status_code == 200 else None
    
class RegistrationsVersion(Enum):
    RELEASE = 1
    BETA = 2
    RC = 3
    V3_4 = 4
    V3_6 = 5

class RegistrationsVersionConfig:
    # https://docs.microsoft.com/en-us/nuget/api/registration-base-url-resource#versioning
    BASE_URL_TYPE_VALUE = "RegistrationsBaseUrl"
    BASE_URL_BETA_TYPE_VALUE = "RegistrationsBaseUrl/3.0.0-beta"
    BASE_URL_RC_TYPE_VALUE = "RegistrationsBaseUrl/3.0.0-rc"
    BASE_URL_3_4_TYPE_VALUE = "RegistrationsBaseUrl/3.4.0"
    BASE_URL_3_6_TYPE_VALUE = "RegistrationsBaseUrl/3.6.0"    

    def __init__(self, service_index_json: dict):
        """
        Params:
        service_index_json: Teh json response from the nuget service index endpoint
        https://docs.microsoft.com/en-us/nuget/api/service-index
        """        
        assert isinstance(service_index_json, dict), ":param service_index_json cannot be None"
        assert service_index_json.get("resources"), "You must provide a valid :param service_index_json object."        
        
        resources = service_index_json["resources"]
        self.base_urls = {
            RegistrationsVersion.RELEASE: "",
            RegistrationsVersion.BETA: "",
            RegistrationsVersion.RC: "",
            RegistrationsVersion.V3_4: "",
            RegistrationsVersion.V3_6: ""
        }

        for resource in resources:
            resource_type = resource["@type"]
            resource_id = resource["@id"]
            if resource_type == self.BASE_URL_TYPE_VALUE:
                self.base_urls[RegistrationsVersion.RELEASE] = resource_id
                continue
            if resource_type == self.BASE_URL_BETA_TYPE_VALUE:
                self.base_urls[RegistrationsVersion.BETA] = resource_id
                continue
            if resource_type == self.BASE_URL_RC_TYPE_VALUE:
                self.base_urls[RegistrationsVersion.RC] = resource_id
                continue
            if resource_type == self.BASE_URL_3_4_TYPE_VALUE:
                self.base_urls[RegistrationsVersion.V3_4] = resource_id
                continue
            if resource_type == self.BASE_URL_3_6_TYPE_VALUE:
                self.base_urls[RegistrationsVersion.V3_6] = resource_id
                continue
    @property
    def default_base_url(self):
        return self.get_base_url()

    def get_base_url(self, version: RegistrationsVersion = RegistrationsVersion.RELEASE) -> str:
        """ Returns the base url from the configuration that matches the version specified. """
        return self.base_urls[version]

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
            self.__set_items(get_request(self.url))  
        
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
        assert isinstance(json, dict), "json cannot be None."
        assert isinstance(url, str), "url cannot be None"
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
        url = f'{self._version_config.get_base_url(service_version)}{package_id.lower()}/index.json'
        index_data = get_request(url)
        return RegistrationsIndex(index_data, url) if index_data else None

class Nuget:
    """
    Class used to access the Nuget Server API.
    https://docs.microsoft.com/en-us/nuget/api/overview
    """
    DEFAULT_SERVICE_INDEX_URL = "https://api.nuget.org/v3/index.json"        

    def __init__(self, service_index_url = DEFAULT_SERVICE_INDEX_URL):
        """
        The constructor for the Nuget class. This creates and initialize the root 
        object for accessing the API. This method will make a call out to the Nuget 
        Service index to fetch the list of resources and that are available on the 
        API and the urls used to access them.
        """        
        self.__fetch_base_urls(service_index_url)   
    
    def __fetch_base_urls(self, service_index_url):  
        self.index_url = service_index_url
        response = get_request(service_index_url)                        
        self.registrations = Registrations(response)

if __name__ == "__main__":
    pass
