import unittest
import json
from nuget_package_scanner.nuget.registrations import Registrations
import nuget_package_scanner.smart_client as smart_client

class TestRegistrations(unittest.TestCase):

    def test_const(self):
        response = json.load(open("./tests/sampledata/sample_nuget_service_index.json", "r"))   
        registration = Registrations(response, smart_client.SmartClient())
        self.assertIsNotNone(registration)
        
if __name__ == '__main__':
    unittest.main()