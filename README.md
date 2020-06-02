# nuget-package-scanner
![PyPI](https://img.shields.io/pypi/v/nuget-package-scanner?color=green)
![PyPI - License](https://img.shields.io/pypi/l/nuget-package-scanner)
![Python package](https://github.com/doneholmes/nuget-package-scanner/workflows/Python%20package/badge.svg?branch=master)

nuget-package-scanner is a Python module that will query your Github organization for Nuget dependencies in your .Net projects and produce a report on how up-to-date they are. This can be useful for identifying which projects' dependencies are out of date (and how badly). It can also be useful for identifying how many disperate versions of the same common package is in use across your codebase (*cough... Newtonsoft.Json...cough*).

Currently, results are saved to a csv file that can be imported into a spreadsheet or another db that can be used for displaying, sorting, and further analysis.

## Installation
`pip install nuget-package-scanner`

## Usage (as a script)

1. Ensure that you have a [Github personal token](https://github.com/settings/tokens)
1. (Optionally) Set a `GITHUB_TOKEN` envorinment variable with the value. If you don't set this variable, you'll have to provide it at the prompt at runtime.
1. `cd` to your local clone of this repo
1. `python -m nuget_package_scanner`
1. Follow the prompt(s)
1. Import the exported .csv into google sheets (or another spreadsheet app)

## Report Data

- From Github
   - **Repo Name** - The name of the github repository that the package configuration was discovered
   - **Container Path** - The file path to the package configuration within the repository
   - **Name** - The name of the package config container that the package was listed in. This will be either a .Net Framework *packages.config* or a .Net core *.csproj* file.
   - **Referenced Version** - The version referenced in the package container (if there was a version specified, some core MSFT libraries don't specify)
- From Nuget Server
   - **Date** - The date the **Referenced Version** was published to the Nuget Server
   - **Latest Release** - The latest full-release version of the package that has been published to the Nuget Server
   - **Latest Release Date** - The date the **Latest Release** was published to the Nuget Server
   - **Latest Package** - The latest published version of the package (inclusive of pre-release) that has been published to the Nuget Server
   - **Latest Package Date** - The date the **Latest Package** was published to the Nuget Server
   - **Link** - If it is a public package on the Nuget Server (e.g nuget.org), this will be a url to the detail page for the package. This link is not likely to be provided by a private package repo   
   - **Source** - Url of the registration index for the package that was used to GET details
- Calculated (included for convenience)
   - **Major Release Behind** - The number of *major* releases behind the referenced package is from the **Latest Release**
   - **Minor Release Behind** - The number of *minor* releases behind the referenced package is from the **Latest Release**. This will only be calculated if the packages have the same *major* version
   - **Patch Release Behind** - The number of *patch* releases behind the referenced package is from the **Latest Release**. This will only be calculated if the packages have the same *major* version and *minor* version
   - **Available Version Count** - The total number of versions of the package that are published to the Nuget Server.

## Basic Application Flow

1. Search the specified Github org for all Nuget server configurations (*nuget.config*) to detect and additional Nuget Server sources.(Nuget.org will be included by default) 
1. Search the specified Github org for all .Net Core and .Net Framework project configurations that contain refrences to Nuget package dependencies.
1. Cycle through each Nuget Package discovered
    1. Cycle through each Nuget Server (preferring nuget.org) to find where the package lives
    1. Use the appropriate Nuget Server to fetch registration information for the package
1. Generate and save CSV

**Runtime Note**: My org (168 repositories w/ 100+ Nuget-referencing projects and ~2k individual package references) can take around 2 minutes to fully process.

## Why did you write your own github client?

I originally tried to make use of [PyGithub](https://github.com/PyGithub/PyGithub). I couldn't get it working correctly with my personal acccess token, so I wrote a simple client of my own. This also gave me a chance to familiarize a bit more with the Github API. I wanted to use the [Github GraphQL API](https://developer.github.com/v4/) for this, but it doesn't support code search as of yet. If I need to support any more-complicated use cases, I will look at switching back to PyGithub.

## Why did you write this in Python? Nuget only supports .Net.

I wanted to learn something new and Python is new to me. This project seemed like a good use case for the high-level scripting support available in Python. I could have written this in C#, but I wouldn't have leared as much in the process.

## TODOs
- [X] Shared session(s) in web requests to support connection pooling and boost performance
- [X] More resilliancy in web call timeout errors. Currently, any timeout crashes things.
- [X] Implement async web requests in nuget module. This would speed this up a good bit. Most of the time is currently spent waiting on web requests to complete and there is little reason for that to happen serially.
- [ ] Build a visual front end consumer
- [ ] [Rate limiting checks](https://developer.github.com/v3/#rate-limiting) on calls to the github api. When searching within a very large github org, there is the possiblity that the [search api rate limit](https://developer.github.com/v3/search/#rate-limit) budget could be exhausted (currently 30 calls/minute if authenticated)
- [ ] Possibly break out the nuget module into a stand-alone Python package. I'm not sure if there's any use beyond basic GET functionality.
- [ ] Optimizing json object scanning algorhithms. It's currently a very simple brute force approach. This may be a lot of work for little gain.
