import json
import os
from typing import List

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

    return metadata, markdown_content


def discover_posts(directory):
    '''
    Discover all posts in the given directory and return them as a dictionary.
    '''
    files = {}
    years = os.listdir(directory)

    for year in years:
        year_posts = {}
        months = os.listdir(os.path.join(directory, year))
        for month in months:
            posts = os.listdir(os.path.join(directory, year, month))
            year_posts[month] = []
            for post_file in posts:
                path = os.path.join(directory, year, month, post_file)
                frontmatter, content = parse_markdown(path)
                frontmatter["path"] = path
                post = Post(frontmatter, content)
                year_posts[month].append(post)
        files[year] = year_posts

    return files


def generate_and_save_index(files: List[Post]):
    '''
    Generate an index.json file with the given posts and save it.
    '''
    files.sort(key=lambda x: x.date, reverse=True)
    with open("index.json", "w", encoding="utf-8") as f:
        json.dump([post.index_data()
                  for post in files], f, ensure_ascii=False, indent=2)
        print("index.json has been updated")


def generate_and_save_readme(files: dict):
    '''
    Generate a README.md file with the given posts and save it.
    '''
    readme_title = "# Blog"
    readme_description = 'A blog about software development and other things. I use this repository as a source for my website [abhin.dev/](https://www.abhin.dev/blog), and for automatic deploys to [Medium](https://www.medium.com/@abhinr).'

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
                if post.medium:
                    line += f'[[Medium]]({post.medium})'
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


def publish_new_posts(posts: list[Post], available_posts_flattened):
    '''
    Publish new posts to Medium and update the available posts list.
    '''
    for post in posts:
        print(f"New post found: {post.title}")
        post.publish()
        # replace the post with the updated version
        available_posts_flattened = [post if p == post else p for p in available_posts_flattened]
    return available_posts_flattened


def main():
    '''
    Main function to discover new posts, post them to Medium, and update the index and README.
    '''
    available_posts = discover_posts("posts")
    available_posts_flattened = recursive_unwrap_index(available_posts, [])

    unpublished_posts = [post for post in available_posts_flattened if not post.published]

    if len(unpublished_posts) > 0:
        print(f"Found {len(unpublished_posts)} unpublished posts.")
        available_posts_flattened = publish_new_posts(unpublished_posts, available_posts_flattened)

    generate_and_save_readme(available_posts)
    generate_and_save_index(available_posts_flattened)

main()
