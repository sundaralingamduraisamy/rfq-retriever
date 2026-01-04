const BASE = import.meta.env.VITE_BACKEND_URL;
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
