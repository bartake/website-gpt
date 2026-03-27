"""
RAG query: retrieve from Chroma, optionally rerank, generate with Ollama.
Requires: ollama serve (and ollama pull llama3.2)
"""
import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
import requests

# Optional: reranker
try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parent
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

TOP_K = 20
RERANK_TOP = 5


def get_collection():
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection("my_company", embedding_function=ef)


def retrieve(collection, query: str, top_k: int = TOP_K, rerank_top: int = RERANK_TOP):
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas"],
    )
    docs = results["documents"][0]
    metas = results["metadatas"][0]

    if RERANKER_AVAILABLE and len(docs) > rerank_top:
        reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        pairs = [[query, d] for d in docs]
        scores = reranker.predict(pairs)
        ranked = sorted(zip(docs, metas, scores), key=lambda x: x[2], reverse=True)
        docs = [r[0] for r in ranked[:rerank_top]]
        metas = [r[1] for r in ranked[:rerank_top]]
    else:
        docs = docs[:rerank_top]
        metas = metas[:rerank_top]

    return docs, metas


def ask(query: str, use_reranker: bool = True) -> str:
    collection = get_collection()
    context_chunks, metas = retrieve(collection, query)
    context = "\n\n---\n\n".join(context_chunks)

    prompt = f"""Use only the context below to answer the question. If the answer is not in the context, say so.

Context:
{context}

Question: {query}

Answer:"""

    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=300,
        )
        r.raise_for_status()
        return r.json()["response"]
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Is it running? (ollama serve)"
    except requests.exceptions.HTTPError as e:
        return f"Error: {e}. Try: ollama pull {OLLAMA_MODEL}"
    except Exception as e:
        return f"Error: {e}"


def main():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print("Usage: python rag.py <question> [--retrieve-only]")
        print("Example: python rag.py 'What services does My Company offer?'")
        print("  --retrieve-only: show retrieved chunks only (no LLM call)")
        return 1

    args = sys.argv[1:]
    retrieve_only = "--retrieve-only" in args
    if retrieve_only:
        args.remove("--retrieve-only")
    query = " ".join(args)

    print(f"Query: {query}\n")
    if retrieve_only:
        collection = get_collection()
        docs, metas = retrieve(collection, query)
        print("--- Retrieved chunks (top 5) ---\n")
        for i, (doc, meta) in enumerate(zip(docs, metas), 1):
            print(f"[{i}] {meta.get('title', '')} | {meta.get('url', '')}\n{doc[:500]}...\n")
        return 0
    answer = ask(query)
    print(answer)
    return 0


if __name__ == "__main__":
    exit(main())
