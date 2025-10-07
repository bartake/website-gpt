"""
Ingest crawled pages: chunk, embed, store in Chroma.
Run after: scrapy crawl protolabs (from crawler/)
"""
import json
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
PAGES_FILE = DATA_DIR / "pages.jsonl"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks by words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def main():
    if not PAGES_FILE.exists():
        print(f"Error: {PAGES_FILE} not found. Run the crawler first:")
        print("  cd crawler && scrapy crawl protolabs")
        return 1

    print(f"Loading pages from {PAGES_FILE}...")
    documents = []
    metadatas = []
    ids = []

    with open(PAGES_FILE, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            url = doc.get("url", "")
            title = doc.get("title", "")
            text = doc.get("text", "")

            chunks = chunk_text(text)
            for j, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "url": url[:500],  # Chroma metadata length limit
                    "title": title[:100],
                    "chunk": j,
                })
                ids.append(f"{i}_{j}")

    if not documents:
        print("No documents to ingest.")
        return 1

    print(f"Embedding {len(documents)} chunks with {EMBEDDING_MODEL}...")
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        "protolabs",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    # Add in batches (Chroma handles batching internally, but large batches can be slow)
    batch_size = 100
    for start in range(0, len(documents), batch_size):
        end = min(start + batch_size, len(documents))
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  Added {end}/{len(documents)} chunks")

    print(f"Done. Chroma DB at {CHROMA_DIR}")
    return 0


if __name__ == "__main__":
    exit(main())
