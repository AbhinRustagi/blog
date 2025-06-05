from datetime import datetime

import requests

from .utils import (MEDIUM_BASE_URL, MEDIUM_TOKEN, MEDIUM_USER_ID,
                    PERSONAL_WEBSITE, PLATFORM_MEDIUM)


class Post:
    '''
    A class to represent a blog post
    '''

    def __init__(self, metadata, content):
        self.title = metadata.get("title")
        self.date = metadata.get("date", datetime.now())
        self.description = metadata.get("description", "")
        self.tags = metadata.get("tags", [])
        self.reading_time = metadata.get("reading_time", 0)
        # Populated for new posts automatically
        self.slug = metadata.get("path").split("/")[-1].replace(".md", "")
        self.canonical_url = metadata.get(
            "canonical_url", PERSONAL_WEBSITE + "blog/" + self.slug)
        self.platforms = metadata.get("platforms", [])
        self.platform_names = []
        for platform in self.platforms:
            self.platform_names.extend(platform.keys())
        self.published = metadata.get("published", False)
        self.path = metadata.get("path")

        self.content = content

    def __str__(self):
        return f"{self.slug} - {self.date.strftime('%Y-%m-%d')}"

    def __repr__(self):
        return f"<{self.title} - {self.date.strftime('%Y-%m-%d')}>"

    def metadata(self):
        '''
        Return the metadata of the post
        '''
        return {
            "title": self.title,
            "date": self.date,
            "canonical_url": self.canonical_url,
            "description": self.description,
            "tags": self.tags,
            "platforms": self.platforms
        }

    def __eq__(self, value) -> bool:
        return self.title == value.title and self.date == value.date and self.slug == value.slug

    def __ne__(self, value):
        return self.title != value.title or self.date != value.date or self.slug != value.slug

    def file_repr(self):
        '''
        Return the string representation of the post for the file
        '''
        file_repr = "---\n"
        file_repr += f"title: {self.title}\n"
        file_repr += f"date: {self.date}\n"
        file_repr += f"canonical_url: {self.canonical_url}\n"
        file_repr += f"description: {self.description}\n"
        file_repr += f"reading_time: {self.reading_time}\n"
        file_repr += f"slug: {self.slug}\n"
        file_repr += f"published: {self.published}\n"
        if self.tags:
            file_repr += "tags:\n"
            for tag in self.tags:
                file_repr += f"  - {tag}\n"
        if self.platforms:
            file_repr += "platforms:\n"
            for platform in self.platforms:
                for name, link in platform.items():
                    file_repr += f"  - {name}: {link}\n"
        file_repr += "---\n"
        file_repr += f"{self.content}"
        return file_repr

    def save(self):
        '''
        Save the post to a file
        '''
        with open(self.path, "w", encoding='utf-8') as f:
            f.write(self.file_repr())
            f.close()

    def publish(self):
        '''
        Publish the post to all platforms
        '''
        if self.published:
            return

        if PLATFORM_MEDIUM in self.platform_names:
            self.post_to_medium()
        self.published = True
        self.save()

    def post_to_medium(self):
        '''
        Post a blog post to Medium.
        '''
        if self.published:
            return

        url = MEDIUM_BASE_URL + "users/" + MEDIUM_USER_ID + "/posts"
        data = {
            "title": self.title,
            "contentFormat": "markdown",
            "content": self.content,
            "canonicalUrl": self.canonical_url,
            "tags": self.tags,
            "publishStatus": "public"
        }

        response = requests.post(url, headers={
            "Authorization": f"Bearer {MEDIUM_TOKEN}",
            "Content-Type": "application/json"
        }, json=data, timeout=10)

        if response.status_code == 201:
            self.published = True
            index = self.platform_names.index(PLATFORM_MEDIUM)
            self.platforms[index][PLATFORM_MEDIUM] = response.json().get("url")
        else:
            print(response.json())
            response.raise_for_status()

    def index_data(self):
        '''
        Return the data to be stored in the index.json file
        '''
        return {
            "title": self.title,
            "date": self.date.strftime("%Y-%m-%d"),
            "slug": self.slug,
            "path": self.path,
            "canonical_url": self.canonical_url,
            "tags": self.tags,
            "reading_time": self.reading_time,
            "platforms": self.platforms,
            "published": self.published
        }
