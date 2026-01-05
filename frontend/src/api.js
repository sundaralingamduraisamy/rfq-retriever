const BASE = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";
export const API_BASE_URL = BASE;

export async function chat(payload) {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function getRfqs() {
  const res = await fetch(`${BASE}/rfqs`);
  return res.json();
}

export async function login(username, password) {
  const res = await fetch(`${BASE}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Login failed");
  return res.json();
}

export async function getConfig() {
  const res = await fetch(`${BASE}/api/config`);
  return res.json();
}
