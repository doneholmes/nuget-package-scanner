import unittest
import json
from nuget.registrations import Registrations
import smart_client

class TestRegistrations(unittest.TestCase):

    def test_const(self):
        response = json.load(open("./tests/sampledata/sample_nuget_service_index.json", "r"))   
        registration = Registrations(response, smart_client.SmartClient())
        self.assertIsNotNone(registration)
        
if __name__ == '__main__':
    unittest.main()