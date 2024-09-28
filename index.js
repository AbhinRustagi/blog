import fs from "fs";
import matter from "gray-matter";
import { discoverPosts } from "./lib/discoverPosts.js";
import { generateAndSaveReadme } from "./lib/generateReadme.js";
import { postToDevTo } from "./lib/postToDevTo.js";
import { postToMedium } from "./lib/postToMedium.js";

function recursiveUnwrapIndex(index, posts) {
  for (const key in index) {
    if (index[key] instanceof Array) {
      posts.push(...index[key]);
    } else {
      recursiveUnwrapIndex(index[key], posts);
    }
  }
  return posts;
}

async function main() {
  let availablePosts = discoverPosts("posts");
  availablePosts = recursiveUnwrapIndex(availablePosts, []);
  const indexedPosts = JSON.parse(fs.readFileSync("index.json", "utf-8"));
  const indexedPostsFlattened = recursiveUnwrapIndex(indexedPosts, []);

  let diff = new Set(availablePosts.map(({ title }) => title)).difference(
    new Set(indexedPostsFlattened.map(({ title }) => title))
  );
  diff = Array.from(diff);

  if (diff.length === 0) {
    console.log("No new posts to post");
    return;
  }

  diff = availablePosts.filter((post) => diff.includes(post.title));

  const promises = [];

  diff.forEach((post) => {
    const postFile = fs.readFileSync(post.path, "utf8");
    const { data: frontmatter, content } = matter(postFile);
    const data = {
      title: frontmatter.title,
      content,
      tags: frontmatter.tags,
      canonicalUrl: frontmatter.canonicalUrl,
    };

    promises.push(postToMedium(data));
    promises.push(postToDevTo(data));
  });

  await Promise.all(promises).then((responses) => {
    responses.forEach((response, index) => {
      // Medium response
      if (index % 2 === 0) {
        diff[Math.floor(index / 2)]["medium"] = response?.data?.url;
      } else {
        diff[Math.floor(index / 2)]["devto"] = response?.url;
      }
    });
  });

  fs.readFile("index.json", "utf8", function readFileCallback(err, data) {
    if (err) {
      console.log(err);
    } else {
      diff.forEach((post) => {
        const date = new Date(post.date);
        const year = date.getFullYear();
        const month =
          date.getMonth() + 1 < 10
            ? `0${date.getMonth() + 1}`
            : date.getMonth() + 1;

        if (!indexedPosts[year])
          indexedPosts[year] = {
            [month]: [],
          };
        else if (!indexedPosts[year][month]) indexedPosts[year][month] = [];

        indexedPosts[year][month].push(post);
      });
      fs.writeFileSync(
        "index.json",
        JSON.stringify(indexedPosts, null, 2),
        "utf8"
      ); // write it back
    }
    console.log("All posts have been posted to Medium and Dev.to");
  });

  generateAndSaveReadme(indexedPosts);
  console.log("README.md has been updated");
}

main();
