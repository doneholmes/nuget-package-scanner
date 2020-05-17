import app
import asyncio
import logging

app.enable_console_logging()
org = input("Enter a github org to search: ")
token = input("Enter a github token (or enter to use GITHUB_TOKEN environment variable: ")
# asyncio.run(app.show_github_search_rate_limit_info(token),debug=True)
output = input("Enter a file location if you want to output to a csv: ")

org = 'DnDBeyond'
output = r'E:\temp\ddb-package-scan8.csv'

asyncio.run(app.run(org, token, output),debug=True)
loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(app.run(org, token, output))  

# There's a Windows-specific bug that clogs the console w/ errors when closing the loop
# https://github.com/aio-libs/aiohttp/issues/4324
logger = logging.getLogger()
logger.disabled = True

# Wait for the underlying SSL connections to close
# https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
loop.run_until_complete(asyncio.sleep(3))
loop.close()