import asyncio
import csv
import logging
import os
import sys
import time
from operator import attrgetter
from typing import List

from smart_client import SmartClient

import nuget
from githubSearch import GithubClient, GithubSearchResult
from nuget import NetCoreProject, Nuget, PackageConfig, PackageContainer


def enable_console_logging(level: int = logging.INFO):   
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(logging.StreamHandler())    
    logger.addHandler(logging.FileHandler('last_run.log','w'))

async def show_github_search_rate_limit_info(github_token):
    # Get token and initialize github search client
    token = github_token if isinstance(github_token,str) and github_token else os.getenv('GITHUB_TOKEN')
    assert isinstance(token,str) and token, 'You must either pass this method a non-empty param: github_token or set the GITHUB_TOKEN environment varaible to a non-empty string.'

    async with SmartClient() as client:        
        g = GithubClient(token, client)
        await g.get_search_rate_limit_info()

def write_to_csv(package_containers: List[PackageContainer], csv_location: str):
    # just assume that we want this to be easy and create any missing directories in the path    
    os.makedirs(os.path.dirname(csv_location), exist_ok=True) 
    with open(csv_location, 'w', newline='') as csvfile:
        # write over any existing file
        w = csv.writer(csvfile)
        columns = [
            "Repo Name", "Container Path",  "Name", "Referenced Version", "Date", 
            "Latest Release", "Latest Release Date", "Latest Package", 
            "Latest Package Date", "Major Release Behind", "Minor Release Behind",
            "Patch Release Behind", "Available Version Count", "Link", "Source"
        ]
        w.writerow(columns)
        for container in package_containers:
            for package in container.packages:
                package_columns = [
                    container.repo, container.path,  package.name, package.version, package.version_date,
                    package.latest_release, package.latest_release_date, package.latest_version,
                    package.latest_version_date, package.major_releases_behind,
                    package.minor_releases_behind, package.patch_releases_behind,
                    package.available_version_count, package.details_url, package.source
                ]
                w.writerow(package_columns)  

async def __find_net_core_project_details(search_result: GithubSearchResult,  package_containers: List[PackageContainer], g: GithubClient, n: Nuget) -> None:
    core_project_source = await g.get_request_as_text(search_result.url)
    core_project = NetCoreProject(core_project_source, search_result.name, search_result.repo, search_result.path)
    package_containers.append(core_project)
    tasks = []
    for package in core_project.packages:            
        tasks.append(n.get_fetch_package_details(package))
    await asyncio.wait(tasks)

async def __find_net_framework_project_details(search_result: GithubSearchResult,  package_containers: List[PackageContainer], g: GithubClient, n: Nuget) -> None:
    package_config_source = await g.get_request_as_text(search_result.url)
    package_config = PackageConfig(package_config_source, search_result.name, search_result.repo, search_result.path)
    package_containers.append(package_config)
    tasks = []
    for package in package_config.packages:            
        tasks.append(n.get_fetch_package_details(package))
    await asyncio.wait(tasks)

async def build_org_report(org:str, token: str) -> List[PackageContainer]:
    start = time.perf_counter()
    async with SmartClient() as client:
        # Find any additional nuget servers that exist for this org
        g = GithubClient(token, client)        
        configs = await g.get_unique_nuget_configs(org)    
        logging.info(f'Found {len(configs)} Nuget Server(s) to query.')
        for c in configs:
            logging.info(f'{configs[c]} Index: {c}')                

        # Create Nuget client from discovered configs
        async with Nuget(client, configs) as n:              
            package_containers: List[PackageContainer] = []
            tasks = []
            # Find all .Net Core projects with nuget packages
            net_core_task = asyncio.create_task(g.search_netcore_csproj(org))
            # Find all .Net Framework projects with nuget packages
            net_framework_task = asyncio.create_task(g.search_package_configs(org))

            await asyncio.wait([net_core_task, net_framework_task])

            core_projects: List[GithubSearchResult] = net_core_task.result()
            logging.info(f'Found {len(core_projects)} .Net Core projects to process.')
            package_configs: List[GithubSearchResult] = net_framework_task.result()
            logging.info(f'Found {len(package_configs)} legacy .Net Framework projects to process.')                                 

            for core_project in core_projects:
                tasks.append(__find_net_core_project_details(core_project, package_containers, g, n))
            for package_config in package_configs:
                tasks.append(__find_net_framework_project_details(package_config, package_containers, g, n))

            await asyncio.wait(tasks)            

            stop = time.perf_counter()
            logging.info(f'Processed {org} for Nuget packages in  {stop - start:0.4f} seconds')
            logging.info(f'Cache Hit Info for client.get_as_json  {client.get_as_json.cache_info()}')
            logging.info(f'Cache Hit Info for client.get_as_text  {client.get_as_text.cache_info()}')

            return package_containers            

async def run(github_org:str, github_token: str = None, output_file: str = None):    
    logging.info(f'Building Nuget dependency report for the {github_org} Github org.')
    assert isinstance(github_org,str) and github_org, ':param github_org must be a non-empty string.'
    org = github_org
    
    # Get token and initialize github search client
    token = github_token if isinstance(github_token,str) and github_token else os.getenv('GITHUB_TOKEN')
    assert isinstance(token,str) and token, 'You must either pass this method a non-empty param: github_token or set the GITHUB_TOKEN environment varaible to a non-empty string.'

    package_containers = await build_org_report(org, token)
    
    if output_file:
        logging.info(f'Writing Report to {output_file}.')
        try:
            write_to_csv(sorted(package_containers, key=attrgetter('repo', 'path')), output_file)
        except Exception as e:
            logging.exception(e)    

    # Iterate over all pacakges and log/display    
    # for package_container in package_containers:                                                  
    #     logging.info(f'Repo:{package_container.repo} Path:{package_container.path}')
    #     for package in package_container.packages:
    #         logging.info(f'********** Name:{package.name} Source: {package.source}')
    #         logging.info(f'********** Referenced Version:{package.version} Date: {package.version_date}')
    #         logging.info(f'********** Latest Release: {package.latest_release} Date: {package.latest_release_date}')
    #         logging.info(f'********** Latest Version: {package.latest_version} Date: {package.latest_version_date}')    
