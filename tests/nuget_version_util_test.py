import unittest
from nuget_package_scanner.nuget import version_util as nugetversion
from nuget_package_scanner.nuget import VersionPart as VersionPart

class TestNugetVersion(unittest.TestCase):

    def test_get_version_part(self):
        m = nugetversion.pattern.match("1.2.3.4")
        self.assertEqual(nugetversion.get_version_part(m,VersionPart.MAJOR),1)
        self.assertEqual(nugetversion.get_version_part(m,VersionPart.MINOR),2)
        self.assertEqual(nugetversion.get_version_part(m,VersionPart.PATCH),3)
        self.assertEqual(nugetversion.get_version_part(m,VersionPart.BUILD),4)      

    def test_get_version_part_default(self):
        m = nugetversion.pattern.match("1.2")
        self.assertEqual(nugetversion.get_version_part(m,VersionPart.MAJOR),1)
        self.assertEqual(nugetversion.get_version_part(m,VersionPart.MINOR),2)
        self.assertEqual(nugetversion.get_version_part(m,VersionPart.PATCH),0)        

    def test_is_full_release_invalid_version(self):
        with self.assertRaises(AssertionError):
            nugetversion.is_full_release("not.a.version.nope")

    def test_is_full_release_false(self):
        self.assertFalse(nugetversion.is_full_release("1.2.3-beta"))
        self.assertFalse(nugetversion.is_full_release("1.2.3+build.1-rc"))
        self.assertFalse(nugetversion.is_full_release("1.2.3-beta+build.1-rc"))
        
    def test_is_full_release_true(self):
        self.assertTrue(nugetversion.is_full_release("1.2.3"))
        self.assertTrue(nugetversion.is_full_release("999.999.999"))
        self.assertTrue(nugetversion.is_full_release("1.2.3.4"))
        self.assertTrue(nugetversion.is_full_release("999.999.999.1"))

    def test_is_newer_release_invalid_version(self):
        with self.assertRaises(AssertionError):
            nugetversion.is_newer_release("not.a.version.nope", "1.2.3")

    def test_is_newer_release_invalid_compare_version(self):
        with self.assertRaises(AssertionError):
            nugetversion.is_newer_release("1.2.3", "not.a.version.nope")        
        
    def test_is_newer_release_false(self):
        self.assertFalse(nugetversion.is_newer_release("1.2.40604.0921","1.2.40604.00920"))           
        self.assertFalse(nugetversion.is_newer_release("1.2.3.4","1.2.3.4"))
        self.assertFalse(nugetversion.is_newer_release("1.2.3","0.7.9"))
        self.assertFalse(nugetversion.is_newer_release("1.2","1.2.0"))
        self.assertFalse(nugetversion.is_newer_release("1.2.0","1.2"))
        self.assertFalse(nugetversion.is_newer_release("3.3.105.24","3.3.4.16"))
        self.assertFalse(nugetversion.is_newer_release("3.3.105.24","3.3.105.16"))   
        self.assertFalse(nugetversion.is_newer_release("3.3.105.24","3.3.105.24-beta"))

    def test_is_newer_release_true(self):
        self.assertTrue(nugetversion.is_newer_release("1.2.40604.0921","01.2.040604.00922"))
        self.assertTrue(nugetversion.is_newer_release("1.2","1.2.1"))
        self.assertTrue(nugetversion.is_newer_release("1.2","1.2.0.1"))
        self.assertTrue(nugetversion.is_newer_release("1.2.3","1.3.1"))
        self.assertTrue(nugetversion.is_newer_release("1.2.3","1.2.9"))
        self.assertTrue(nugetversion.is_newer_release("3.3.105.24","3.3.105.999-beta"))
        self.assertTrue(nugetversion.is_newer_release("3.3.105.24","3.3.105.999"))
        self.assertTrue(nugetversion.is_newer_release("1.2.3","3.0.0"))
    
    def test_get_version_count_behind_basic(self):
        result = nugetversion.get_version_count_behind("1.2.3","2.0.0")        
        self.assertEqual(list(result.values()), [1,0,0])

        result = nugetversion.get_version_count_behind("2.1.1","2.1.1")
        self.assertEqual(list(result.values()), [0,0,0])

        result = nugetversion.get_version_count_behind("1.99.1","1.299.0")
        self.assertEqual(list(result.values()), [0,200,0])

        result = nugetversion.get_version_count_behind("1.1.1","1.1.009")
        self.assertEqual(list(result.values()), [0,0,8])     
            
if __name__ == '__main__':
    unittest.main()