from enum import Enum

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
        service_index_json: The json response from the nuget service index endpoint
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