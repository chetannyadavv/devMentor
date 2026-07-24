// In dev (npm run dev), talk directly to the local api container.
// In production, the built files are served by Caddy on the same
// origin, which proxies /api -- so a relative path works without
// needing to know the real domain at build time.
const API_BASE = import.meta.env.DEV ? "http://localhost:8000" : "/api";
const WS_BASE = import.meta.env.DEV
  ? "ws://localhost:8000"
  : `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`;

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
