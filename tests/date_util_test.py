
import datetime
import unittest
import nuget_package_scanner.nuget.date_util as date_util

class TestDateUtil(unittest.TestCase):

    def test_get_date_from_iso_string_expected(self):
        d = date_util.get_date_from_iso_string('2020-02-08T04:03:07.1786999+00:00')
        self.assertEqual(d.year, 2020)   
        self.assertEqual(d.month, 2)
        self.assertEqual(d.day, 8)

        d = date_util.get_date_from_iso_string('2019-06-24T13:13:58.739069')
        self.assertEqual(d.year, 2019)   
        self.assertEqual(d.month, 6)
        self.assertEqual(d.day, 24)

    def test_get_date_from_iso_string_nothing(self):
        with self.assertRaises(AssertionError):            
           date_util.get_date_from_iso_string('')
        with self.assertRaises(AssertionError):
            d = None
            date_util.get_date_from_iso_string(d)     
            
if __name__ == '__main__':
    unittest.main()