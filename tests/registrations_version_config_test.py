import unittest
import json
import nuget_package_scanner.nuget as nuget

class TestRegistrationsVersionConfig(unittest.TestCase):

    def test_version_config_null_index(self):        
        with self.assertRaises(AssertionError):
            nuget.RegistrationsVersionConfig(None)

    def test_version_config_incorrect_type(self):        
        with self.assertRaises(AssertionError):
            nuget.RegistrationsVersionConfig(123)

    def test_version_config_get_base_url(self):        
        response = json.load(open("./tests/sampledata/sample_nuget_service_index.json", "r"))        
        config = nuget.RegistrationsVersionConfig(response)
        print(config.default_base_url)  
        self.assertTrue(len(config.default_base_url) > 0)

    def test_version_config_get_base_url_default(self):        
        response = json.load(open("./tests/sampledata/sample_nuget_service_index.json", "r"))        
        config = nuget.RegistrationsVersionConfig(response)        
        self.assertTrue(len(config.default_base_url) > 0)
        self.assertEqual(config.default_base_url,config.get_base_url())

    def test_version_config_get_base_url_named_versions_dont_match(self):        
        response = json.load(open("./tests/sampledata/sample_nuget_service_index.json", "r"))        
        config = nuget.RegistrationsVersionConfig(response)                
        v3_6_url = config.get_base_url(nuget.RegistrationsVersion.V3_6)
        v3_4_url = config.get_base_url(nuget.RegistrationsVersion.V3_4)      
        self.assertTrue(len(v3_6_url) > 0)
        self.assertTrue(len(v3_4_url) > 0)  
        self.assertNotEqual(v3_6_url,v3_4_url)

    def test_version_config_get_base_url_every_version_has_value(self):        
        response = json.load(open("./tests/sampledata/sample_nuget_service_index.json", "r"))        
        config = nuget.RegistrationsVersionConfig(response)  
        for v in nuget.RegistrationsVersion:
            base_url = config.get_base_url(v)                        
            self.assertTrue(len(base_url) > 0)
        
if __name__ == '__main__':
    unittest.main()