const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

/**
 * Update these paths once we confirm your FastAPI routers.
 * For now, it tries a reasonable guess:
 *   POST /mentor/chat  { message: "..." }
 */
export async function mentorChat({ message }) {
    const res = await fetch(`${API_BASE}/mentor/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
    });

    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`Request failed ${res.status}: ${text || res.statusText}`);
    }
    return await res.json();
}
