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

export async function saveRfq(payload) {
  const res = await fetch(`${BASE}/rfqs/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Save failed");
  return res.json();
}

export async function updateRfqStatus(id, status) {
  const res = await fetch(`${BASE}/rfqs/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error("Status update failed");
  return res.json();
}

export async function getRfqDetail(id) {
  const res = await fetch(`${BASE}/rfqs/${id}`);
  if (!res.ok) throw new Error("Failed to load RFQ");
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

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Upload failed");
  }

  return res.json();
}

export async function deleteDocument(docId) {
  const res = await fetch(`${BASE}/documents/${docId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Delete failed");
  return res.json();
}

export async function deleteRfq(id) {
  const res = await fetch(`${BASE}/rfqs/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Delete API failed");
  return res.json();
}
