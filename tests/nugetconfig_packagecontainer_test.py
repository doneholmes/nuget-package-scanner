import os
import unittest
from nuget_package_scanner.nuget import PackageContainer as PackageContainer
from nuget_package_scanner.nuget import PackageConfig as PackageConfig
from nuget_package_scanner.nuget import NetCoreProject as NetCoreProject

class TestPackageContainer(unittest.TestCase):

    def test_base_ctor_null_name(self):        
        with self.assertRaises(AssertionError):
            PackageContainer(None, "something", "something")

    def test_base_ctor_property_values(self):        
        name = "alkj"
        repo = "lwer"
        path = ";lakja"        
        container = PackageContainer("contents", name, repo, path)
        self.assertEqual(name, container.name)
        self.assertEqual(repo, container.repo)
        self.assertEqual(path, container.path)        
    
    def test_base_ctor_packages_always_empty(self):               
        container = PackageContainer("contents are not empty but this is not handled in the base") 
        self.assertIsInstance(container, PackageContainer)       
        self.assertTrue(len(container.packages) == 0)

    def test_package_config_ctor(self):
        name = "alkj"
        repo = "lwer"
        path = ";lakja"        
        config = open(os.path.join(os.path.dirname(__file__), 'sampledata/sample_packages.config')).read()
        package_config = PackageConfig(config, name, repo, path)
        self.assertIsInstance(package_config, PackageContainer)
        self.assertIsInstance(package_config, PackageConfig)
        self.assertTrue(len(package_config.packages) > 0)
        self.assertEqual(name, package_config.name)
        self.assertEqual(repo, package_config.repo)
        self.assertEqual(path, package_config.path)        

    def test_net_core_project_ctor(self):
        name = "alkj"
        repo = "lwer"
        path = ";lakja"        
        csproj = open(os.path.join(os.path.dirname(__file__), 'sampledata/sample.csproj')).read()
        package_config = NetCoreProject(csproj, name, repo, path)
        self.assertIsInstance(package_config, PackageContainer)
        self.assertIsInstance(package_config, NetCoreProject)
        self.assertTrue(len(package_config.packages) > 0)      
        self.assertEqual(name, package_config.name)
        self.assertEqual(repo, package_config.repo)
        self.assertEqual(path, package_config.path)             
                    
if __name__ == '__main__':
    unittest.main()