const BASE = "http://localhost:8000/api/v1";

export async function searchProducts({ keyword, useAI = true, sortBy = "relevancy" }) {
  const res = await fetch(`${BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ keyword, use_ai: useAI, sort_by: sortBy, limit: 10 }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}