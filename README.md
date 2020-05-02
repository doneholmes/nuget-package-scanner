# nuget-package-scanner

## How do I use this?
nuget -> nu

You will need to ensure that a `GITHUB_TOKEN` envorinment variable exists and contains a valid personal access token in order for the Github queries to work.
https://github.com/settings/tokens

### TODOs
- Implement async web requests in nuget module. Not strictly necessary, but would likely speed this up a good bit. Most of the time is currently spent waiting on web requests to complete and there is little reason for that to happen serially.
    - https://docs.aiohttp.org/en/stable/
- Rate limiting checks on calls to the github api. When searching within a very large github org, there is the possiblity that the search api rate limit budget could be exhausted (currently 30 calls/minute if authenticated)
    - Github Rate Limiting: https://developer.github.com/v3/#rate-limiting
    - Github Search API Rate Limiting: https://developer.github.com/v3/search/#rate-limit
- Optimizing json object scanning algorhithms. It's currently a very simple brute force approach. This may be a lot of work for little gain.
- Possibly break out the nuget module into a Python package. I'm not sure if there's any use beyond basic GET functionality.

### Why did you write your own github client?

I originally tried to make use of PyGithub. I couldn't get it working correctly with my personal acccess token, so I wrote a simple client of my own. If I need to support any more complicated use cases, I would look at switching back to PyGithub. This also gave me a chance to familiarize a bit more with the Github API.

### Why did you write this in Python? Nuget only supports .Net.

Mostly, I'm trying to learn Python. This project seemed like a good use case for the high-level scripting support available in Python. I could have written this in C#, but I wouldn't have leared as much in the process.
