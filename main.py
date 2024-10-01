import os
import json
import yaml
import markdown
import requests
from slugify import slugify

MONTHS = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}


PLATFORM_MEDIUM = "medium"
PLATFORM_DEV_TO = "dev.to"


MEDIUM_BASE_URL = "https://api.medium.com/v1/"
MEDIUM_USER_ID = os.environ.get("MEDIUM_USER_ID")
MEDIUM_TOKEN = os.environ.get("MEDIUM_TOKEN")
PERSONAL_WEBSITE = "https://www.abhin.dev/"


def parse_markdown(file_path):
    '''
    Parse a markdown file and return the metadata and HTML content.
    '''
    # Open and read the markdown file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Separate metadata and markdown content
    if content.startswith('---'):
        # Find the end of the metadata section
        end_metadata = content.find('---', 3)
        metadata_raw = content[3:end_metadata].strip()
        markdown_content = content[end_metadata+3:].strip()

        # Parse metadata as YAML
        metadata = yaml.safe_load(metadata_raw)
    else:
        metadata = {}
        markdown_content = content

    # Convert markdown content to HTML
    html_content = markdown.markdown(markdown_content)

    return metadata, html_content


def discover_posts(directory):
    '''
    Discover all posts in the given directory and return them as a dictionary.
    '''
    files = {}

    for year in os.listdir(directory):
        month_path = os.path.join(directory, year)
        year_posts = {}

        for month in os.listdir(month_path):
            post_path = os.path.join(month_path, month)
            year_posts[month] = []
            for post in os.listdir(post_path):
                frontmatter, _ = parse_markdown(os.path.join(post_path, post))
                data = {
                    "title": frontmatter.get("title"),
                    "date": frontmatter.get("date").strftime("%Y-%m-%d"),
                    "description": frontmatter.get("description"),
                    "path": os.path.join(post_path, post),
                    "platforms": frontmatter.get("platforms")
                }
                year_posts[month].append(data)
        files[year] = year_posts

    return files


def generate_and_save_readme(files: dict):
    '''
    Generate a README.md file with the given posts and save it.
    '''
    readme_title = "# Blog"
    readme_description = '''
    A blog about software development and other things.
     I use this repository as a source for my website [abhin.dev/](https://www.abhin.dev/),
     and for automatic deploys to [Medium](https://www.medium.com/@abhinr).'''

    readme_content = f'{readme_title}\n\n{readme_description}\n\n'
    years = sorted(files.keys(), reverse=True)

    for year in years:
        readme_content += f'## {year}\n\n'

        for month in sorted(files[year].keys(), reverse=True):
            readme_content += f'### {MONTHS[month]}\n\n'

            for post in files[year][month]:
                readme_content += f'[{post.get("title")}]({post.get("path")})\n\n'

        readme_content += '\n'

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)


def post_to_medium(post):
    '''
    Post a blog post to Medium.
    '''
    data = {
        "title": post["title"],
        "contentFormat": "markdown",
        "content": post["content"],
        "tags": post["tags"],
        "canonical_url": post["canonical_url"]
    }

    url = MEDIUM_BASE_URL + "users/" + MEDIUM_USER_ID + "/posts"
    response = requests.post(url, headers={
        "Authorization": f"Bearer {MEDIUM_TOKEN}",
        "Content-Type": "application/json"
    }, json=data, timeout=10)

    return response.json()


def recursive_unwrap_index(index, posts):
    '''
    Unwrap the index.json file into a flat list of posts.
    '''
    for key in index:
        if isinstance(index[key], list):
            posts.extend(index[key])
        else:
            recursive_unwrap_index(index[key], posts)
    return posts


def post_to_platforms(posts):
    promises = []

    for index, post in enumerate(diff):
        metadata, content = parse_markdown(post["path"])
        slug = slugify(metadata.get("title"))
        diff[index]["slug"] = slug
        data = {
            "title": metadata.get("title"),
            "content": content,
            "tags": metadata.get("tags"),
            "canonical_url": PERSONAL_WEBSITE + "blog/" + slug,
        }

        platforms = metadata.get("platforms", [])
        for platform in platforms:
            if platform == PLATFORM_MEDIUM:
                promises.append(post_to_medium(data))

    return promises


def main():
    '''
    Main function to discover new posts, post them to Medium, and update the index and README.
    '''
    available_posts = discover_posts("posts")
    available_posts = recursive_unwrap_index(available_posts, [])
    indexed_posts = json.loads(
        open("index.json", "r", encoding='utf-8').read())
    indexed_posts_flattened = recursive_unwrap_index(indexed_posts, [])

    diff = set(post["title"] for post in available_posts).difference(
        set(post["title"] for post in indexed_posts_flattened)
    )
    diff = list(diff)

    if len(diff) == 0:
        print("No new posts to post")
        return

    diff = [post for post in available_posts if post["title"] in diff]

    if any(len(post.get("platforms", [])) > 0 for post in diff):
        promises = post_to_platforms(diff)
        for index, response in enumerate(promises):
            diff[index]["medium"] = response.get("data", {}).get("url")

    with open("index.json", "w", encoding='utf-8') as f:
        for post in diff:
            year = post["date"][0:4]
            month = post["date"][5:7]

            if year not in indexed_posts:
                indexed_posts[year] = {
                    month: [],
                }
            elif month not in indexed_posts[year].keys():
                indexed_posts[year][month] = []

            indexed_posts[year][month].append(post)

        json.dump(indexed_posts, f, indent=2, ensure_ascii=False,)
        print("index.json has been updated")

    generate_and_save_readme(indexed_posts)
    print("README.md has been updated")


main()
