import json
import os
import time
import shutil
from glob import glob
import requests
import classes
from bs4 import BeautifulSoup

GITHUB_API = "https://api.github.com"
REPO = os.environ["GITHUB_REPOSITORY"]
# branch comes as refs/heads/<branch>
RAW_BRANCH = os.environ["GITHUB_REF"]
BRANCH = RAW_BRANCH.split("/")[-1]
print(f"Working on branch {BRANCH}...")
headers = {"X-GitHub-Api-Version" : "2022-11-28"}
VERSION = "1.1"  # Version of SadeWiki, used for cache busting CSS
# TODO: Make VERSION dynamic based on git tag or commit hash

system_header = f"""
<header>\n
<nav>\n
<a href='/index.html'>Home</a> | \n
<a href='https://github.com/{REPO}'>Source</a>\n
</nav>\n
</header>
"""

index_footer =f"""
<p>Made with <3 by the community using <a href='https://github.com/hinkleydev/SadeWiki'>SadeWiki</a> - <a href='https://github.com/{REPO}'>Contribute on GitHub</a></p>\n
<a href="https://github.com/{REPO}/new/{BRANCH}">Add new page</a><br>\n
"""

system_footer = f"""
{index_footer}
<a href="https://github.com/{REPO}/edit/{BRANCH}/(file)">Edit this page</a>\n
"""

def check_status(response):
    """
    When a response is passed to this, this function will ensure the request is checked for any potential issues.
    A rate limit header reaching 0 will cause the code to pause for the required period. And any non 200 status code will cause the code to exit
    :param response:
    :return None:
    """
    response_headers = response.headers
    if response_headers["x-ratelimit-remaining"] == '0':
        print("Rate limit hit, waiting to avoid ban...")
        ratelimit_reset = response_headers["x-ratelimit-reset"]
        current_time = time.time()
        wait_time = int(ratelimit_reset) - int(current_time)
        print(f"Rate limit hit, will resume in {wait_time} seconds...")
        time.sleep(wait_time)
        # TODO: This works, but the lack of output makes it a bit annoying. Could do with a loop to output current wait time
    elif not response.ok:
        raise classes.GitHubApiError(f"{response.status_code} {response.reason} returned on {response.request.method} request {response.url} - View GitHub REST API docs for more guidance")

def get_files():
    """
    Get markdown files from the source directory
    :return List of filenames as strings:
    """
    files = glob("*.md")
    #files = glob("*/*.md") # TODO: Make recursive files work correctly, right now it fails on write #16
    return files

def recursively_get_files(path):
    return glob('*/*.md', recursive=True)

def get(path):
    """
    Makes a GET request to the given path using the API headers
    :param path:
    :return response object:
    """
    r = requests.get(GITHUB_API + path, headers=headers)
    check_status(r)
    return r

def post(path, data):
    """
    Makes a POST request to the given path using the API headers and data. JSON data must be formatted using json.dumps
    :param path:
    :param data:
    :return response object:
    """
    r = requests.post(GITHUB_API + path, headers=headers, data=data)
    check_status(r)
    return r

def get_html(markdown):
    """
    Makes a request to the Github API to change markdown into HTML
    :param markdown:
    :return HTML as string:
    """
    content_json = {"text": markdown, "context": REPO, "mode": "gfm"}
    r = post("/markdown", data=json.dumps(content_json))
    return r.text

def authenticate(token):
    """
    Prompts the user for a token and exits if token is not correct
    :return user object:
    """
    headers["Authorization"] = "Bearer " + token
    check_auth = get("/user")
    if not check_auth.ok:
        raise classes.InvalidToken(f"Error on authenticating, please check token. Status code: {check_auth.status_code} returned")
    else :
        user_object = check_auth.json()
        return user_object


if __name__ == "__main__":
    css_file = "styles.css"
    #token = os.environ["SADE_GH_TOKEN"]
    output_directory = os.environ["GITHUB_WORKSPACE"] + "/docs"
    files = get_files()
    print(f"Found {len(files)} markdown files to process")
    #auth = authenticate(token)

    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
    shutil.copy("/" + css_file, output_directory + "/" + css_file)

    if os.path.exists("favicon.ico"):
        shutil.copy("favicon.ico", output_directory + "/favicon.ico")

    # custom header and footer
    header_html = ""
    try :
        with open("_header.md", "r") as header_file:
            header_md = header_file.read()
            header_html = get_html(header_md)
    except FileNotFoundError:
        print("No header file found, continuing without custom header")

    footer_html = ""
    try :
        with open("_footer.md", "r") as footer_file:
            footer_md = footer_file.read()
            footer_html = get_html(footer_md)
    except FileNotFoundError:
        print("No footer file found, continuing without custom footer")

    index = []
    for each_file in files:
        if each_file.startswith("_"): # ignore meta files
            continue
        handler = open(each_file, "r")
        content = handler.read()
        html = get_html(content)
        soup = BeautifulSoup(html, 'html.parser')
        titles = soup.find_all("h1")
        title = ""
        if len(titles) > 0:  # if there is a H1, set it as a title
            title = "<title>" + titles[0].string + "</title>\n"
        output_file = each_file.replace(".md", ".html")
        index.append(output_file)

        with open(output_directory + "/" + output_file, "w") as f:
            f.write("<!DOCTYPE html>\n")
            f.write("<html lang='en'>\n")
            f.write("<head>\n")
            f.write(title)
            f.write('<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n')
            f.write(f'<link rel="stylesheet" href="{css_file}?v={VERSION}">\n')
            f.write("<body>\n")

            # Header
            f.write(system_header)
            f.write(header_html)

            # Main content
            f.write("<main>\n")
            f.write(html + '\n')
            f.write("</main>\n")

            # Footer
            f.write("</body>\n")
            f.write("<footer>")
            f.write(footer_html)
            f.write(system_footer.replace("(file)", each_file))
            f.write("</footer>\n")
            f.write("</html>\n")

    with open(output_directory + "/index.html", "w") as index_file:
        index_file.write('<meta name="viewport" content="width=device-width, initial-scale=1.0" />')
        index_file.write(f'<link rel="stylesheet" href="{css_file}?v={VERSION}">\n') # TODO: This should use an absolute URL
        index_file.write(system_header)
        index_file.write(header_html)
        index_file.write("<ul>\n")
        for link in index :
            index_file.write(f"<li><a href='{link}'>{link}</a></li>\n") # TODO: This should use an absolute URL
        index_file.write("</ul>\n")
        index_file.write("<footer>")
        index_file.write(footer_html)
        index_file.write(index_footer)
        index_file.write("</footer>\n")

    print("Done!")