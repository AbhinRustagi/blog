const BASE_URL = "https://dev.to/api/articles";

const postToDevTo = async (post) => {
  const { title, content, tags, canonicalUrl } = post;
  const url = BASE_URL;

  const data = {
    article: {
      title,
      body_markdown: content,
      tags,
      canonical_url: canonicalUrl,
    },
  };

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "api-key": process.env.DEV_TO_API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  return response.json();
};

export { postToDevTo };
