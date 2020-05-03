import app

app.enable_console_logging()    
org = input("Enter a github org to search: ")
token = input("Enter a github token (or enter to use GITHUB_TOKEN environment variable: ")
output = input("Enter a file location if you want to output to a csv: ")
app.run(org, token, output)