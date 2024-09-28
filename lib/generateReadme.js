import fs from "fs";

const months = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const title = "# Blog";
const description =
  "A blog about software development and other things. I use this repository as a source for my website [abhin.dev/](https://www.abhin.dev/), and for automatic deploys to [dev.to](https://dev.to/abhinrustagi) and [Medium](https://www.medium.com/@abhinr).";

const generateAndSaveReadme = (files) => {
  let readme = `${title}\n\n${description}\n\n`;
  const years = Object.keys(files).sort().reverse();

  years.forEach((year) => {
    readme += `## ${year}\n\n`;

    for (const month of Object.keys(files[year]).sort()) {
      readme += `### ${months[month - 1]}\n\n`;

      for (const post of files[year][month]) {
        readme += `- [${post.title}](${post.path})\n`;
      }

      readme += "\n";
    }
  });

  fs.writeFileSync("README.md", readme);
};

export { generateAndSaveReadme };
