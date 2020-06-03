import asyncio
import csv
import logging
import os
import sys
import time
from operator import attrgetter
from typing import List

from nuget_package_scanner.smart_client import SmartClient
from nuget_package_scanner.async_utils import wait_or_raise
from nuget_package_scanner.github_search import GithubClient, GithubSearchResult
from nuget_package_scanner.nuget import NetCoreProject, Nuget, Package, PackageConfig, PackageContainer

NAME = 'nuget-package-scanner'
VERSION = '0.0.6'

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

async def __fetch_net_core_project(search_result: GithubSearchResult,  package_containers: List[PackageContainer], g: GithubClient, failures: List[GithubSearchResult]) -> None:
    try:
        core_project_source = await g.get_request_as_text(search_result.url)
        core_project = NetCoreProject(core_project_source, search_result.name, search_result.repo, search_result.path)
        package_containers.append(core_project)
    except:
        failures.append(search_result)

async def __fetch_net_framework_project(search_result: GithubSearchResult,  package_containers: List[PackageContainer], g: GithubClient, failures: List[GithubSearchResult]) -> None:
    try:
        package_config_source = await g.get_request_as_text(search_result.url)
        package_config = PackageConfig(package_config_source, search_result.name, search_result.repo, search_result.path)
        package_containers.append(package_config)
    except:
        failures.append(search_result)

async def __fetch_package_details(package: Package, n: Nuget, failures: List[Package]) -> None:
    try:
        await n.get_fetch_package_details(package)
    except:
        failures.append(package)


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
            # Find all projects with nuget packages.
            # Note: These were originally concurrent calls, but the Github API forbids this
            core_projects: List[GithubSearchResult] = await g.search_netcore_csproj(org)
            logging.info(f'Found {len(core_projects)} .Net Core projects to process.')
            package_configs: List[GithubSearchResult] = await g.search_package_configs(org)                                 
            logging.info(f'Found {len(package_configs)} legacy .Net Framework projects to process.')

            # Fetch all project contents            
            package_containers: List[PackageContainer] = []
            failed_projects: List[GithubSearchResult] = []
            fetch_project_tasks = []
            for core_project in core_projects:
                fetch_project_tasks.append(asyncio.create_task(__fetch_net_core_project(core_project, package_containers, g, failed_projects),name=core_project.url))
            for package_config in package_configs:
                fetch_project_tasks.append(asyncio.create_task(__fetch_net_framework_project(package_config, package_containers, g, failed_projects),name=package_config.url))

            await asyncio.wait(fetch_project_tasks)
            
            # For now, just report if there were any projects that we failed to fetch
            for f in failed_projects:
                logging.warn(f'Failed to get package containter {f.name} from {f.url}')

            # Fetch all package details
            failed_packages: List[Package] = []  
            fetch_package_tasks = []
            for pc in package_containers:
                for p in pc.packages:
                    name = p.name + p.version if p.version else '' + p.target_framework if p.target_framework else ''
                    fetch_package_tasks.append(asyncio.create_task(__fetch_package_details(p, n, failed_packages), name=name))

            await asyncio.wait(fetch_package_tasks)

            # For now, just report if there were any packages that we failed to fetch
            for fp in failed_packages:
                logging.warn(f'Failed to get package {fp.name} from discovered nuget server(s).')

            stop = time.perf_counter()
            logging.info(f'Processed {org} for Nuget packages in  {stop - start:0.4f} seconds')
            logging.info(f'Cache Hit Info for client.get_as_json  {client.get_as_json.cache_info()}')
            logging.info(f'Cache Hit Info for client.get_as_text  {client.get_as_text.cache_info()}')

            # TODO: Add retry logic for failed tasks (Flush alru_cache and retry)
            # client.get_as_json.invalidate('key')

            return package_containers    

async def run(github_org:str, github_token: str = None, output_file: str = None) -> List[PackageContainer]:    
    logging.info(f'Building Nuget dependency report for the {github_org} Github org.')
    assert isinstance(github_org,str) and github_org, ':param github_org must be a non-empty string.'
    org = github_org
    
    # Get token and initialize github search client
    token = github_token if isinstance(github_token,str) and github_token else os.getenv('GITHUB_TOKEN')
    assert isinstance(token,str) and token, 'You must either pass this method a non-empty param: github_token or set the GITHUB_TOKEN environment varaible to a non-empty string.'

    package_containers: List[PackageContainer] = await build_org_report(org, token)
    
    if output_file:
        logging.info(f'Writing Report to {output_file}.')
        try:
            write_to_csv(sorted(package_containers, key=attrgetter('repo', 'path')), output_file)
        except Exception as e:
            logging.exception(e)        
    
    return package_containers
