const API_BASE = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";

export function getToken() {
  return localStorage.getItem("devmentor_token");
}

export function submissionWsUrl(submissionId) {
  return `${WS_BASE}/ws/submissions/${submissionId}?token=${getToken()}`;
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("devmentor_token", token);
  } else {
    localStorage.removeItem("devmentor_token");
  }
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // response wasn't JSON -- fall back to statusText
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  get: (path) => request(path),
  post: (path, body) =>
    request(path, {
      method: "POST",
      body: body instanceof URLSearchParams ? body : JSON.stringify(body),
    }),
  patch: (path, body) => request(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: "DELETE" }),
};
