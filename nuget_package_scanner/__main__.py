import asyncio
import logging

import nuget_package_scanner.app as app

print(f'{app.NAME} v{app.VERSION}')
print(f'Occassionally, you will get errors due to IO issues. Please retry if this happens.')

app.enable_console_logging()
org = input("Enter a github org to search: ")
token = input("Enter a github token (or enter to use GITHUB_TOKEN environment variable: ")
#asyncio.run(app.show_github_search_rate_limit_info(token),debug=True)
output = input("Enter a file location if you want to output to a csv: ")

loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(app.run(org, token, output))  

# Wait for the underlying SSL connections to close
# https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
loop.run_until_complete(asyncio.sleep(3))

# There's a Windows-specific bug that clogs the console w/ errors when closing the loop
# https://github.com/aio-libs/aiohttp/issues/4324
# I haven't been successful at eating those logs, so just adding a pause here :(
input("Press any key to get a wall of 'Event loop is closed' errors. (Known aiohttp bug)")    
loop.close()
