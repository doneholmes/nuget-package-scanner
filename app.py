import logging
import os
import sys
import time
from typing import List

import githubSearch
import nuget
from nuget import Nuget
from nuget import NetCoreProject
from nuget import PackageConfig


def enable_console_logging(level: int = logging.INFO):   
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(logging.StreamHandler())
    logger.addHandler(logging.FileHandler('last_run.log','w'))

def run(github_org:str, github_token: str = None):
    start = time.perf_counter()
    logging.info("Startng test run...")
    assert isinstance(github_org,str) and github_org, ':param github_org must be a non-empty string.'
    org = github_org
    
    # Get token and initialize github search client
    token = github_token if isinstance(github_token,str) and github_token else os.getenv('GITHUB_TOKEN')
    assert isinstance(token,str) and token, 'You must either pass this method a non-empty param: github_token or set the GITHUB_TOKEN environment varaible to a non-empty string.'
    g = githubSearch.GithubClient(token)

    # Find any additional nuget servers that exist 
    configs = g.get_unique_nuget_configs(org)
    logging.info(f'Found {len(configs)} Nuget Server(s) to query.')
    for c in configs:
        logging.info(f'{configs[c]} Index: {c}')
    
    # Create Nuget client from discovered configs
    nq = Nuget(configs)

    package_containers = [] # type: List[nugetconfig.PackageContainer]
   
    # Find all .Net Core projects with nuget packages
    core_projects = g.search_netcore_csproj(org)
    logging.info(f'Found {len(core_projects)} .Net Core projects to process.')
    for core_project in core_projects:
        core_project_source = g.makeRequest(core_project.url).text
        core_project = NetCoreProject(core_project_source, core_project.name, core_project.repo, core_project.path)
        for package in core_project.packages:            
            nq.get_fetch_package_details(package)     
        logging.info(f'Cache Hit info: {nuget.request_wrapper.get_request.cache_info()}')
        package_containers.append(core_project)

    # Find all .Net Framework projects with nuget packages
    package_configs = g.search_package_configs(org)
    logging.info(f'Found {len(package_configs)} legacy .Net Framework projects to process.')
    for package_config in package_configs:        
        package_config_source = g.makeRequest(package_config.url).text
        package_config = PackageConfig(package_config_source, package_config.name, package_config.repo, package_config.path)
        for package in package_config.packages:
            nq.get_fetch_package_details(package) 
        logging.info(f'Cache Hit info: {nuget.request_wrapper.get_request.cache_info()}')
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
    logging.info(f'Cache Hit info: {nuget.request_wrapper.get_request.cache_info()}')