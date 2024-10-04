import json
import os
from typing import List

import markdown
import yaml

from lib import MONTHS, Post
from lib.utils import PLATFORM_MEDIUM


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
            for post_file in os.listdir(post_path):
                post_path = os.path.join(post_path, post_file)
                frontmatter, _ = parse_markdown(post_path)
                frontmatter["path"] = post_path
                post = Post(frontmatter, _)
                year_posts[month].append(post)
        files[year] = year_posts

    return files


def generate_and_save_index(files: List[Post]):
    '''
    Generate an index.json file with the given posts and save it.
    '''
    with open("index.json", "w", encoding="utf-16") as f:
        json.dump([post.index_data() for post in files], f, ensure_ascii=False, indent=2)
        print("index.json has been updated")


def generate_and_save_readme(files: dict):
    '''
    Generate a README.md file with the given posts and save it.
    '''
    readme_title = "# Blog"
    readme_description = 'A blog about software development and other things. I use this repository as a source for my website [abhin.dev/](https://www.abhin.dev/), and for automatic deploys to [Medium](https://www.medium.com/@abhinr).'

    readme_content = f'{readme_title}\n\n{readme_description}\n\n'
    years = sorted(files.keys(), reverse=True)

    for year in years:
        readme_content += f'## {year}\n\n'

        for month in sorted(files[year].keys(), reverse=True):
            readme_content += f'### {MONTHS[month]}\n\n'

            for post in files[year][month]:
                line = f'- {post.title} '
                line += f'[[Markdown]]({post.path})'
                line += f'[[Website]]({post.canonical_url})'
                if PLATFORM_MEDIUM in post.platform_names:
                    index = post.platform_names.index(PLATFORM_MEDIUM)
                    line += f'[[Medium]]({post.platforms[index][PLATFORM_MEDIUM]})'
                line += '\n\n'
                readme_content += line

        readme_content += '\n'

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
        print("README.md has been updated")


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


def main():
    '''
    Main function to discover new posts, post them to Medium, and update the index and README.
    '''
    available_posts = discover_posts("posts")
    available_posts_flattened = recursive_unwrap_index(available_posts, [])

    unpublished_posts = [post for post in available_posts_flattened if not post.published]

    if len(unpublished_posts) == 0:
        print("No new posts to post")
        return

    for post in unpublished_posts:
        print(f"New post found: {post.title}")
        post.publish()
        # replace the post with the updated version
        available_posts_flattened = [post if p == post else p for p in available_posts_flattened]

    generate_and_save_readme(available_posts)
    generate_and_save_index(available_posts_flattened)


main()
