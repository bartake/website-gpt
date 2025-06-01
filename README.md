# Protolabs RAG Pipeline

Crawl protolabs.com, embed content, and query it with a local LLM. **100% free and open source.**

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) (for local LLM)

## Setup

```bash
cd protolabs-rag
pip install -r requirements.txt
ollama pull llama3.2
```

## Usage

### 1. Crawl the website

```bash
python run_crawl.py
```

Output: `data/pages.jsonl` (one JSON object per page)

### 2. Ingest into vector DB

```bash
python ingest.py
```

Downloads `all-MiniLM-L6-v2` (~80MB) on first run. Creates `chroma_db/`.

### 3. Query

```bash
python rag.py "What CNC machining tolerances does Protolabs offer?"
python rag.py "What materials are available for injection molding?"
```

Ensure Ollama is running (`ollama serve` or `ollama run llama3.2`).

## Project structure

```
protolabs-rag/
├── crawler/              # Scrapy project
│   └── protolabs_spider/
│       └── spiders/
│           └── protolabs.py
├── data/
│   └── pages.jsonl      # Crawled pages (created by crawl)
├── chroma_db/           # Vector DB (created by ingest)
├── run_crawl.py         # Run crawler
├── ingest.py            # Chunk → embed → Chroma
├── rag.py               # Query + Ollama
└── requirements.txt
```

## Stack

| Component | Tool |
|-----------|------|
| Crawler | Scrapy |
| Content extraction | Trafilatura |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | Chroma |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 (optional) |
| LLM | Ollama + Llama 3.2 |

## AWS Bedrock Option

Use **Bedrock Knowledge Base** + **Bedrock LLM** instead of Chroma + Ollama:

1. Create a Knowledge Base in AWS Bedrock (see [BEDROCK_SETUP.md](BEDROCK_SETUP.md))
2. Set `BEDROCK_KNOWLEDGE_BASE_ID`, `BEDROCK_DATA_SOURCE_ID`, `BEDROCK_S3_BUCKET` in `config_bedrock.py` or env
3. Run `python ingest_bedrock.py` to upload and sync documents
4. Run `python rag_bedrock.py "your question"` to query
