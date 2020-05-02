from .registrations import Registrations
import nuget.request_wrapper

class NugetServer:
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
        response = nuget.request_wrapper.get_request(service_index_url)                        
        self.registrations = Registrations(response)