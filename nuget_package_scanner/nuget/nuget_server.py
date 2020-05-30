from .registrations import Registrations
from ..smart_client import SmartClient

class NugetServer:
    """
    Class used to access the Nuget Server API.
    https://docs.microsoft.com/en-us/nuget/api/overview
    """
    DEFAULT_SERVICE_INDEX_URL = "https://api.nuget.org/v3/index.json"      

    def __init__(self):
        """
        To get an instance of this class call :class NugetServer.create() instead.
        """
        pass      
    
    @classmethod
    async def create(cls, client: SmartClient, service_index_url = DEFAULT_SERVICE_INDEX_URL):
        """
        The constructor for the Nuget class. This creates and initialize the root 
        object for accessing the API. This method will make a call out to the Nuget 
        Service index to fetch the list of resources and that are available on the 
        API and the urls used to access them.
        """    
        self = NugetServer()
        self.__client: SmartClient = client 
        await self.__fetch_base_urls(service_index_url)          
        return self    

    async def __fetch_base_urls(self, service_index_url):  
        self.index_url = service_index_url
        json = await self.__client.get_as_json(service_index_url)                   
        self.registrations = Registrations(json, self.__client)
        self.package_uri_template = self.__get_package_uri_template(json)
        

    def __get_package_uri_template(self, service_index_json: dict) -> str:
        assert isinstance(service_index_json, dict), ":param service_index_json cannot be None"
        assert service_index_json.get("resources"), "You must provide a valid :param service_index_json object."                
        resources = service_index_json["resources"]
        for resource in resources:
            resource_type = resource["@type"]
            if resource_type == "PackageDetailsUriTemplate/5.1.0":
                return resource["@id"]