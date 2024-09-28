import os
import json
import markdown
import requests
import yaml

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


MEDIUM_BASE_URL = "https://api.medium.com/v1/"
MEDIUM_USER_ID = os.environ.get("MEDIUM_USER_ID")
MEDIUM_TOKEN = os.environ.get("MEDIUM_TOKEN")
PERSONAL_WEBSITE = "https://www.abhin.dev/"


def parse_markdown(file_path):
    # Open and read the markdown file
    with open(file_path, 'r') as f:
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
        metadata = None
        markdown_content = content

    # Convert markdown content to HTML
    html_content = markdown.markdown(markdown_content)

    return metadata, html_content


def discover_posts(dir):
    files = {}

    for year in os.listdir(dir):
        monthPath = os.path.join(dir, year)
        yearPosts = {}

        for month in os.listdir(monthPath):
            postPath = os.path.join(monthPath, month)
            yearPosts[month] = []
            for post in os.listdir(postPath):
                frontmatter, _ = parse_markdown(os.path.join(postPath, post))
                data = {
                    "title": frontmatter.get("title"),
                    "date": frontmatter.get("date").strftime("%Y-%m-%d"),
                    "description": frontmatter.get("description"),
                    "path": os.path.join(postPath, post),
                }
                yearPosts[month].append(data)
        files[year] = yearPosts

    return files


README_TITLE = "# Blog"
README_DESCRIPTION = '''A blog about software development and other things. I use this repository as a source for my website [abhin.dev/](https://www.abhin.dev/), and for automatic deploys to [Medium](https://www.medium.com/@abhinr).'''


def generate_and_save_readme(files: dict):
    readme_content = f'{README_TITLE}\n\n{README_DESCRIPTION}\n\n'
    years = sorted(files.keys(), reverse=True)

    for year in years:
        readme_content += f'## {year}\n\n'

        for month in sorted(files[year].keys(), reverse=True):
            readme_content += f'### {MONTHS[month]}\n\n'

            for post in files[year][month]:
                readme_content += f'[{post.get("title")}]({post.get("path")})\n\n'

        readme_content += '\n'

    open("README.md", "w", encoding="utf-8").write(readme_content)


def post_to_medium(post):
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
    for key in index:
        if isinstance(index[key], list):
            posts.extend(index[key])
        else:
            recursive_unwrap_index(index[key], posts)
    return posts


def main():
    available_posts = discover_posts("posts")
    available_posts = recursive_unwrap_index(available_posts, [])
    indexed_posts = json.loads(open("index.json", "r").read())
    indexed_posts_flattened = recursive_unwrap_index(indexed_posts, [])

    diff = set(post["title"] for post in available_posts).difference(
        set(post["title"] for post in indexed_posts_flattened)
    )
    diff = list(diff)

    if len(diff) == 0:
        print("No new posts to post")
        return

    diff = [post for post in available_posts if post["title"] in diff]

    promises = []

    for post in diff:
        metadata, content = parse_markdown(post["path"])
        data = {
            "title": metadata.get("title"),
            "content": content,
            "tags": metadata.get("tags"),
            "canonical_url": PERSONAL_WEBSITE + "blog/" + metadata.get("slug"),
        }

        promises.append(post_to_medium(data))

    for index, response in enumerate(promises):
        diff[index]["medium"] = response.get("data", {}).get("url")

    with open("index.json", "w") as f:
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
        
        json.dump(indexed_posts, f, indent=2)
        print("index.json has been updated")

    generate_and_save_readme(indexed_posts)
    print("README.md has been updated")

main()
