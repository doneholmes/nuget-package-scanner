import app

app.enable_console_logging()    
org = input("Enter a github org to search: ")
token = input("Enter a github token (or enter to use GITHUB_TOKEN environment variable: ")
app.run(org, token)