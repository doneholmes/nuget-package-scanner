import unittest
from nugetconfig import Package as Package

class TestPackage(unittest.TestCase):

    def test_ctor_null_name(self):        
        with self.assertRaises(AssertionError):
            Package(None, "something", "something")    

    def test_eq_all(self):        
        a = Package("stuffs", "versionstuffs", "frizzle")
        b = Package("stuffs", "versionstuffs", "frizzle")
        self.assertTrue(a==b)

    def test_eq_null_framework(self):        
        a = Package("stuffs", "versionstuffs")
        b = Package("stuffs", "versionstuffs")
        self.assertTrue(a==b)

    def test_not_eq_version(self):        
        a = Package("stuffs", "versionstuffs")
        b = Package("stuffs", "version123stuffs")
        self.assertFalse(a==b)

    def test_not_eq_name(self):        
        a = Package("stuffs", "versionstuffs")
        b = Package("stuffs123", "versionstuffs")
        self.assertFalse(a==b)

    def test_not_eq_framework(self):        
        a = Package("stuffs", "versionstuffs")
        b = Package("stuffs", "versionstuffs", "123")
        self.assertFalse(a==b)

    def test_hash(self):        
        a = Package("stuffs", "versionstuffs")
        b = Package("stuffs", "versionstuffs")
        self.assertTrue(a==b)
            
if __name__ == '__main__':
    unittest.main()