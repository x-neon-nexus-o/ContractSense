"""Contract-scoped retrieval: ChromaDB when installed, deterministic local lexical ranking otherwise."""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Any

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9'-]{1,}")


def hashed_embedding(text: str, dims: int = 384) -> list[float]:
    counts = [0.0] * dims
    for token in TOKEN_RE.findall(text.lower()):
        digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "little") % dims
        sign = 1.0 if digest[4] & 1 else -1.0
        counts[index] += sign
    norm = math.sqrt(sum(v * v for v in counts)) or 1.0
    return [v / norm for v in counts]


class ContractRetriever:
    def __init__(self, repository, settings):
        self.repository = repository
        self.client = None
        self.collection = None
        self.mode = "local_lexical"
        if settings.enable_chroma:
            try:
                import chromadb
                settings.chroma_path.mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(path=str(settings.chroma_path))
                self.collection = self.client.get_or_create_collection(
                    name="contract_clauses_v1", metadata={"hnsw:space": "cosine"})
                self.mode = "chroma_hashed_embedding_baseline"
            except Exception:
                self.client = self.collection = None
                self.mode = "local_lexical"

    def index(self, contract_id: str, user_id: str, clauses: list[dict[str, Any]]) -> None:
        self.repository.save_chunks(contract_id, user_id, clauses)
        if self.collection is None:
            return
        try:
            self.collection.delete(where={"contract_id": contract_id})
            if clauses:
                ids = [f"{contract_id}:{i}" for i in range(len(clauses))]
                self.collection.add(ids=ids, embeddings=[hashed_embedding(c["text"]) for c in clauses],
                    documents=[c["text"] for c in clauses],
                    metadatas=[{"contract_id": contract_id, "user_id": user_id,
                                "clause_id": c.get("id", ids[i]), "page": int(c.get("page", 0)),
                                "title": str(c.get("title", ""))[:200], "source": "uploaded_contract"}
                               for i, c in enumerate(clauses)])
        except Exception:
            self.mode = "local_lexical"

    def delete(self, contract_id: str, user_id: str) -> None:
        """Remove persisted vector copies when a user deletes an uploaded contract."""
        if self.collection is None:
            return
        try:
            self.collection.delete(where={"$and": [
                {"contract_id": {"$eq": contract_id}},
                {"user_id": {"$eq": user_id}},
            ]})
        except Exception:
            # The primary DB/upload deletion must still succeed if optional Chroma
            # storage is unavailable; log at the API boundary for operator action.
            self.mode = "local_lexical"
            raise

    def search(self, contract_id: str, user_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if self.collection is not None:
            try:
                results = self.collection.query(query_embeddings=[hashed_embedding(query)],
                    n_results=max(1, min(limit, 10)), where={"$and": [
                        {"contract_id": {"$eq": contract_id}},
                        {"user_id": {"$eq": user_id}},
                    ]})
                docs = (results.get("documents") or [[]])[0]
                metas = (results.get("metadatas") or [[]])[0]
                distances = (results.get("distances") or [[]])[0]
                if docs:
                    return [{"text": doc, "clause_id": meta.get("clause_id", ""),
                             "page": meta.get("page", 0), "title": meta.get("title", ""),
                             "score": round(1.0 - float(distances[i]), 4), "source": "uploaded_contract"}
                            for i, (doc, meta) in enumerate(zip(docs, metas))]
            except Exception:
                self.mode = "local_lexical"
        chunks = self.repository.get_chunks(contract_id, user_id)
        terms = [t for t in TOKEN_RE.findall(query.lower()) if len(t) > 2]
        if not terms:
            return []
        query_counts = Counter(terms)
        ranked = []
        total = max(1, len(chunks))
        doc_freq = Counter()
        tokenized = []
        for chunk in chunks:
            words = TOKEN_RE.findall(chunk["text"].lower())
            counts = Counter(words)
            tokenized.append((chunk, words, counts))
            for term in set(terms):
                if counts[term]:
                    doc_freq[term] += 1
        for chunk, words, counts in tokenized:
            score = 0.0
            for term, qcount in query_counts.items():
                tf = counts[term]
                if tf:
                    idf = math.log(1 + (total - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
                    score += idf * (tf * 2.2) / (tf + 1.2) * qcount
            if score:
                ranked.append((score, chunk))
        ranked.sort(key=lambda x: x[0], reverse=True)
        if not ranked:
            return []
        max_score = ranked[0][0] or 1.0
        return [{"text": row["text"], "clause_id": f"clause-{row['index']+1:04d}",
                 "page": row["page"], "title": "", "score": round(score / max_score, 4),
                 "source": "uploaded_contract"}
                for score, row in ranked[:limit]]
