"""
Semantic search engine using OpenAI embeddings.
Handles English, Hindi, Hinglish queries seamlessly.
"""

import os
import re
from collections import Counter

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from catalog import CATALOG, get_searchable_text


load_dotenv(override=True)

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072
OPENAI_BATCH_SIZE = 2048
SEMANTIC_WEIGHT = 0.75
BM25_WEIGHT = 0.25
BM25_K1 = 1.5
BM25_B = 0.75


def tokenize(text):
    """Tokenize Roman/Hinglish/English text for lexical matching."""
    return re.findall(r"[\w]+", text.lower(), flags=re.UNICODE)


class SemanticSearch:
    def __init__(self, model_name=EMBEDDING_MODEL):
        print(f"Loading model: {model_name}")
        print("(Using OpenAI Embeddings API. Requires OPENAI_API_KEY.)")
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.catalog = CATALOG
        self.embeddings = None
        self.documents = []
        self.doc_freqs = []
        self.doc_lengths = []
        self.idf = {}
        self.avg_doc_length = 0.0
        self._index_catalog()

    @staticmethod
    def _normalize(embeddings):
        """Normalize vectors so dot product remains cosine similarity."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / np.maximum(norms, 1e-12)

    def _embed_texts(self, texts):
        """Create embeddings in batches using OpenAI's embeddings API."""
        vectors = []
        for start in range(0, len(texts), OPENAI_BATCH_SIZE):
            batch = texts[start:start + OPENAI_BATCH_SIZE]
            response = self.client.embeddings.create(
                model=self.model_name,
                input=batch,
                dimensions=EMBEDDING_DIMENSIONS,
            )
            vectors.extend(item.embedding for item in response.data)
        return self._normalize(np.array(vectors, dtype=np.float32))

    def _index_catalog(self):
        """Pre-compute embeddings for all catalog items."""
        print(f"Indexing {len(self.catalog)} items...")
        texts = [get_searchable_text(item) for item in self.catalog]
        self.embeddings = self._embed_texts(texts)
        self._index_bm25(texts)
        print(f"Indexed. Embedding shape: {self.embeddings.shape}")

    def _index_bm25(self, texts):
        """Build a small in-memory BM25 index for exact Hinglish/symptom matches."""
        self.documents = [tokenize(text) for text in texts]
        self.doc_freqs = [Counter(document) for document in self.documents]
        self.doc_lengths = [len(document) for document in self.documents]
        self.avg_doc_length = float(np.mean(self.doc_lengths)) if self.doc_lengths else 0.0

        document_counts = Counter()
        for document in self.documents:
            document_counts.update(set(document))

        doc_count = len(self.documents)
        self.idf = {
            term: float(np.log(1 + (doc_count - freq + 0.5) / (freq + 0.5)))
            for term, freq in document_counts.items()
        }

    def _bm25_scores(self, query):
        query_terms = tokenize(query)
        scores = np.zeros(len(self.catalog), dtype=np.float32)
        if not query_terms or not self.avg_doc_length:
            return scores

        for idx, frequencies in enumerate(self.doc_freqs):
            doc_length = self.doc_lengths[idx]
            score = 0.0
            for term in query_terms:
                term_freq = frequencies.get(term, 0)
                if not term_freq:
                    continue
                numerator = term_freq * (BM25_K1 + 1)
                denominator = term_freq + BM25_K1 * (1 - BM25_B + BM25_B * doc_length / self.avg_doc_length)
                score += self.idf.get(term, 0.0) * numerator / denominator
            scores[idx] = score
        return scores

    @staticmethod
    def _min_max_normalize(scores):
        min_score = float(np.min(scores))
        max_score = float(np.max(scores))
        if max_score <= min_score:
            return np.zeros_like(scores, dtype=np.float32)
        return (scores - min_score) / (max_score - min_score)

    def search(self, query, top_k=5):
        """Search the catalog and return top-k most relevant items."""
        query_embedding = self._embed_texts([query])[0]
        # Cosine similarity = dot product (since both are normalized)
        semantic_scores = np.dot(self.embeddings, query_embedding)
        bm25_scores = self._bm25_scores(query)
        scores = (
            SEMANTIC_WEIGHT * self._min_max_normalize(semantic_scores)
            + BM25_WEIGHT * self._min_max_normalize(bm25_scores)
        )
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            item = dict(self.catalog[idx])
            item["score"] = float(scores[idx])
            item["semantic_score"] = float(semantic_scores[idx])
            item["bm25_score"] = float(bm25_scores[idx])
            results.append(item)
        return results


if __name__ == "__main__":
    # Quick CLI test
    engine = SemanticSearch()
    test_queries = [
        "bawasir ka ilaj",
        "ghutne mein dard",
        "pet ki pathri",
        "chashma hatana",
        "bacha nahi ho raha",
        "naak band rehti hai",
        "kharrate ka ilaj",
        "wazan kam karna hai",
    ]
    for q in test_queries:
        print(f"\n=== Query: {q} ===")
        results = engine.search(q, top_k=3)
        for r in results:
            print(f"  [{r['score']:.3f}] {r['name']} ({r['category']})")
