const BASE_URL = "https://api.medium.com/v1/";

const postToMedium = async (post) => {
  const { title, content, tags, canonicalUrl } = post;
  const url = `${BASE_URL}users/${process.env.MEDIUM_USER_ID}/posts`;

  const data = {
    title,
    contentFormat: "markdown",
    content,
    tags,
    canonicalUrl,
  };

  // const response = await fetch(url, {
  //   method: "POST",
  //   headers: {
  //     Authorization: `Bearer ${process.env.MEDIUM_TOKEN}`,
  //     "Content-Type": "application/json",
  //   },
  //   body: JSON.stringify(data),
  // });

  // return response.json();
  return { data: { url: "https://medium.com" } };
};

export { postToMedium };
