// Requests to the application which serves this page.

async function request(method, path, body) {
  const options = { method, headers: {}, credentials: "same-origin" };
  if (body !== undefined) {
    // The marker header is what tells the application that this page, and
    // not a page of another site, sent the request.
    options.headers = { "Content-Type": "application/json", "X-Git-Mirror": "1" };
    options.body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new Error("The server does not answer. Is git-mirror still running?");
  }
  let data = {};
  try {
    data = await response.json();
  } catch {
    // An answer without JSON is reported by its status below.
  }
  if (!response.ok) throw new Error(data.error || `The request failed (${response.status}).`);
  return data;
}

export const api = {
  session: () => request("GET", "/api/session"),
  storage: () => request("GET", "/api/storage"),
  clearStorage: () => request("POST", "/api/storage/clear", {}),
  repositories: (host, owner) => request("POST", "/api/repositories", { host, owner }),
  start: (job) => request("POST", "/api/jobs", job),
  job: (id) => request("GET", `/api/jobs/${encodeURIComponent(id)}`),
};
