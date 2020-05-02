import unittest
import json
import nuget

class TestRegistrations(unittest.TestCase):

    def test_const(self):
        response = json.load(open("./tests/sampledata/sample_nuget_service_index.json", "r"))   
        registration = nuget.Registrations(response)
        self.assertIsNotNone(registration)
        
if __name__ == '__main__':
    unittest.main()