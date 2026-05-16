# Hinglish Healthcare Search — Local Prototype

A working semantic search demo that handles English, Hindi, and Hinglish queries.
Modeled after how Blinkit, Swiggy Instamart, and Pristyn Care handle multilingual search.

## What it does

Type queries like:
- `bawasir ka ilaj` → returns Piles Treatment
- `ghutne mein dard` → returns Knee Replacement
- `chashma hatana` → returns LASIK
- `bacha nahi ho raha` → returns IVF
- `pet me jalan` → returns Acidity Treatment

No keyword matching — pure semantic understanding via multilingual embeddings.

## Requirements

- Python 3.9+
- ~1GB free disk space (for the embedding model)
- Internet on first run only (to download the model)

## Setup (5 minutes)

```bash
# 1. Install dependencies
pip install sentence-transformers fastapi uvicorn

# 2. Run the app
python app.py
```

First run takes 2–3 minutes (downloads ~470MB embedding model from Hugging Face).
After that, startup is ~10 seconds.

## Use it

Open http://localhost:8000 in your browser. Type queries in any of:
- English: "piles treatment"
- Hindi: "बवासीर का इलाज"
- Hinglish: "bawasir ka ilaj"

All return the same result. That's the magic of multilingual embeddings.

## How it works

1. **Catalog** (`catalog.py`): 40 synthetic treatments with English name, Hindi name,
   Hinglish search terms, symptoms, descriptions. Each treatment gets rolled into one
   rich text string for embedding.

2. **Embedding model** (`search.py`): Uses `paraphrase-multilingual-MiniLM-L12-v2`,
   a small multilingual model (50+ languages). Converts every treatment text into a
   384-dimensional vector. Stored in-memory as a NumPy array.

3. **Search**: User query → embedding → cosine similarity vs. all catalog vectors →
   return top-k. Sub-100ms latency.

4. **UI** (`app.py`): FastAPI serves a single HTML page with debounced live search.

## Files

- `catalog.py` — synthetic treatment catalog
- `search.py` — embedding-based search engine (also runs as standalone CLI test)
- `app.py` — FastAPI web server + UI

## Try a CLI test (no UI)

```bash
python search.py
```

Runs 8 sample Hinglish queries and prints results in terminal.

## Going from prototype to production

What this prototype does NOT have:
- Hybrid search (BM25 + semantic) — keyword search is still needed for brand names
- Re-ranking layer — for business logic (popularity, location, stock)
- Real vector DB (pgvector / Qdrant / Pinecone) — NumPy works for 40 items, not 40k
- Query understanding — intent classification, spell correction
- Personalization — user history, location, time of day
- A/B testing infra — measure search quality

For Pristyn Care scale (~hundreds of treatments), you'd add:
1. pgvector or Qdrant for vector storage
2. OpenSearch/Elasticsearch for keyword fallback
3. A learning-to-rank model on click data
4. Query expansion using LLM (Claude/GPT) for long-tail queries

But the core insight — multilingual embeddings give you 80% of the magic — stays the same.
