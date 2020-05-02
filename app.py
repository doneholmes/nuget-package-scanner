import logging
from typing import List

import githubSearch
import nuget
import nugetconfig
from nugetquery import NugetQuery


def enable_console_logging(level: int = logging.INFO):   
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(logging.StreamHandler())
    logger.addHandler(logging.FileHandler('last_run.log','w'))

if __name__ == '__main__':
    import sys
    import os
    import time

    # Uncomment the following line to enable debug-level logging to the console
    enable_console_logging()

    start = time.perf_counter()
    logging.info("Startng test run...")
    org = "DnDBeyond" #todo: move to arg    
    
    # Make sure to set the apropriate env var before calling
    g = githubSearch.GithubClient(os.getenv('GITHUB_TOKEN'))
    g.get_search_rate_limit_info()

    # Find any additional nuget servers that exist 
    configs = g.get_unique_nuget_configs(org)
    logging.info(f'Found {len(configs)} Nuget Server(s) to query.')
    for c in configs:
        logging.info(f'{configs[c]} Index: {c}')
    
    nq = NugetQuery(configs)

    package_containers = [] # type: List[nugetconfig.PackageContainer]
   
    # Find all .Net Core projects with nuget packages
    core_projects = g.search_netcore_csproj(org)
    logging.info(f'Found {len(core_projects)} .Net Core projects to process.')
    for core_project in core_projects:
        core_project_source = g.makeRequest(core_project.url).text
        core_project = nugetconfig.NetCoreProject(core_project_source, core_project.name, core_project.repo, core_project.path)
        for package in core_project.packages:            
            nq.get_fetch_package_details(package)     
        package_containers.append(core_project)

    # Find all .Net Framework projects with nuget packages
    package_configs = g.search_package_configs(org)
    logging.info(f'Found {len(package_configs)} legacy .Net Framework projects to process.')
    for package_config in package_configs:        
        package_config_source = g.makeRequest(package_config.url).text
        package_config = nugetconfig.PackageConfig(package_config_source, package_config.name, package_config.repo, package_config.path)
        for package in package_config.packages:
            nq.get_fetch_package_details(package) 
        package_containers.append(package_config)

    # Iterate over all pacakges and report    
    for package_container in package_containers:                                                  
        logging.info(f'Repo:{package_container.repo} Path:{package_container.path}')
        for package in package_container.packages:
            logging.info(f'********** Name:{package.name} Source: {package.source}')
            logging.info(f'********** Referenced Version:{package.version} Date: {package.version_date}')
            logging.info(f'********** Latest Release: {package.latest_release} Date: {package.latest_release_date}')
            logging.info(f'********** Latest Version: {package.latest_version} Date: {package.latest_version_date}')
    stop = time.perf_counter()
    logging.info(f'Processed {org} for Nuget packages in  {stop - start:0.4f} seconds')