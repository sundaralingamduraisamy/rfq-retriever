import os
import json
import numpy as np
from PyPDF2 import PdfReader

from settings import settings

CHUNK_FILE = settings.CHUNK_INDEX_FILE


# --------------------------------
# Safe Load Chunk Index
# --------------------------------
def load_chunks():
    if not os.path.exists(CHUNK_FILE):
        print("❌ chunk_index.json not found. You MUST run ingestion first.")
        return []

    with open(CHUNK_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ensure every chunk has required keys
    safe_chunks = []
    for i, c in enumerate(data):
        safe_chunks.append({
            "text": c.get("text", ""),
            "file": c.get("file", "UNKNOWN_FILE"),
            "chunk_id": c.get("chunk_id", i),
            "embedding": c.get("embedding", [])
        })

    print(f"✅ Loaded {len(safe_chunks)} chunks")
    return safe_chunks


CHUNKS = load_chunks()


# --------------------------------
# Cosine Similarity
# --------------------------------
def cosine(a, b):
    a = np.array(a)
    b = np.array(b)

    if len(a) == 0 or len(b) == 0:
        return 0.0

    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# --------------------------------
# Hybrid Search
# --------------------------------
def hybrid_search(query):
    from core.embedding import get_embedding

    if not CHUNKS:
        return []

    query_vec = get_embedding(query)

    scored = []

    for c in CHUNKS:
        emb = c["embedding"]

        # Fix stored as string
        if isinstance(emb, str):
            try:
                emb = json.loads(emb)
            except:
                emb = []

        score = cosine(query_vec, emb)

        scored.append({
            "text": c["text"],
            "relevance": round(score * 100, 2),
            "source": {
                "file": c["file"],
                "chunk_id": c["chunk_id"]
            }
        })

    scored.sort(key=lambda x: x["relevance"], reverse=True)

    # Deduplicate by file (return only the highest scoring chunk per file)
    unique_results = []
    seen_files = set()

    for item in scored:
        fname = item["source"]["file"]
        if fname not in seen_files:
            unique_results.append(item)
            seen_files.add(fname)
        
        if len(unique_results) >= settings.RETRIEVER_TOP_K:
            break

    return unique_results


# --------------------------------
# Read Full RFQ
# --------------------------------
def get_full_rfq(filename):
    path = os.path.join(settings.DATA_DIR, filename)

    if not os.path.exists(path):
        return "RFQ file not found."

    reader = PdfReader(path)
    text = ""

    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"

    return text.strip()
