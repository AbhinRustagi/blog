import fs from "fs";
import path from "path";
import matter from "gray-matter";

// Iteratively read all files in the blog directory
// Avoid recursive because nesting is only 2 levels deep
export const discoverPosts = (dir) => {
  let files = {};

  fs.readdirSync(dir).forEach((year) => {
    const monthPath = path.join(dir, year);
    const yearPosts = {};

    fs.readdirSync(monthPath).forEach((month) => {
      const postPath = path.join(monthPath, month);
      yearPosts[month] = [];
      fs.readdirSync(postPath).forEach((post) => {
        const file = fs.readFileSync(path.join(postPath, post), "utf8");
        const { data: frontmatter } = matter(file);
        const data = {
          title: frontmatter?.title,
          date: frontmatter?.publishDate,
          canonicalUrl: frontmatter?.canonicalUrl,
          description: frontmatter?.description,
          medium: frontmatter?.medium,
          devto: frontmatter?.devto,
          path: path.join(postPath, post),
        };
        yearPosts[month].push(data);
      });
    });

    files[year] = yearPosts;
  });

  return files;
};
