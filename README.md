# nuget-package-scanner

nuget-package-scanner is a tool that will query your Github organization for Nuget dependencies in your .Net projects and report on how up-to-date they are.

## How do I use this?

1. Make sure you have python installed (v3.8+) and added to your `PATH` variable
1. Clone this repo to a local directory
1. You will need to ensure that you have a Github personal toke available for the github search to work properly.
    * https://github.com/settings/tokens
    * Once you have acquired a token, setting a `GITHUB_TOKEN` envorinment variable with the value, or have it available to provide in the command prompt.
1. `cd` to the parent directory of this repo
1. `python nuget-package-scanner`
1. Follow the prompt(s)

## Basic Application Flow

1. Search Github org for all Nuget server configurations to detect all sources used outside of nuget.org
1. Search Github org for all .Net Core and .Net Framework project configurations that contain refrences to Nuget package dependencies.
1. Cycle through each Nuget Package discovered
    1. Cycle through each Nuget Server (preferring nuget.org) to find where the package lives
    1. Use the appropriate Nuget Server to fetch registration information for the package
1. Display Report organized by github repo -> .Net project -> package

## TODOs
- Output to a csv or some other storage format that can be used for reporting
- Build a visual front end consumer
- Implement async web requests in nuget module. Not strictly necessary, but would likely speed this up a good bit. Most of the time is currently spent waiting on web requests to complete and there is little reason for that to happen serially.
    - https://docs.aiohttp.org/en/stable/
- Rate limiting checks on calls to the github api. When searching within a very large github org, there is the possiblity that the search api rate limit budget could be exhausted (currently 30 calls/minute if authenticated)
    - Github Rate Limiting: https://developer.github.com/v3/#rate-limiting
    - Github Search API Rate Limiting: https://developer.github.com/v3/search/#rate-limit
- Optimizing json object scanning algorhithms. It's currently a very simple brute force approach. This may be a lot of work for little gain.
- Possibly break out the nuget module into a stand-alone Python package. I'm not sure if there's any use beyond basic GET functionality.

## Why did you write your own github client?

I originally tried to make use of PyGithub. I couldn't get it working correctly with my personal acccess token, so I wrote a simple client of my own. If I need to support any more complicated use cases, I would look at switching back to PyGithub. This also gave me a chance to familiarize a bit more with the Github API.

## Why did you write this in Python? Nuget only supports .Net.

Mostly, I'm trying to learn Python. This project seemed like a good use case for the high-level scripting support available in Python. I could have written this in C#, but I wouldn't have leared as much in the process.
