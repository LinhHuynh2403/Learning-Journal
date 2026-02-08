# backend/ollama_client.py
import os
import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

async def get_embedding(text: str) -> list[float]:
    """
    Calls Ollama /api/embeddings to turn text into a vector.
    Use a dedicated embedding model like 'nomic-embed-text'.
    """
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": OLLAMA_EMBED_MODEL, "prompt": text}

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["embedding"]

async def ollama_chat_json(system: str, user: str) -> dict:
    """
    Calls Ollama /api/chat and asks it to output JSON.
    Returns parsed JSON dict.
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        # optional: nudge for consistency
        "options": {"temperature": 0.4},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()

    # Ollama returns: { message: { content: "..." }, ... }
    content = data.get("message", {}).get("content", "").strip()

    # Try parse JSON (model might add extra text; we’ll harden a bit)
    import json
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: extract first {...} block
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start : end + 1])
        raise
