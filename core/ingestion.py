import os
import json
from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def load_pdf(path):
    text = ""
    reader = PdfReader(path)
    for p in reader.pages:
        text += p.extract_text() or ""
    return text

def load_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def chunk_text(text, size=900, overlap=700):
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start+size]
        chunks.append(chunk)
        start += overlap
    return chunks

def ingest(folder="data"):
    if os.path.exists("chunk_index.json"):
        print("Indexes already exist")
        return

    entries = []

    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)

        if fname.endswith(".pdf"):
            text = load_pdf(path)
        elif fname.endswith(".docx"):
            text = load_docx(path)
        else:
            continue

        text_chunks = chunk_text(text)

        embeddings = model.encode(text_chunks)

        for i, chunk in enumerate(text_chunks):
            entries.append({
                "file": fname,
                "chunk_id": i,
                "text": chunk,
                "embedding": embeddings[i].tolist()
            })

    with open("chunk_index.json", "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print("Chunk Index Created Successfully")
