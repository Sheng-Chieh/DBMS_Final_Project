from __future__ import annotations
from typing import List, Dict, Optional, Iterable, Tuple
import re

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


class CompanyRetrieverLC:
    def __init__(self, persist_dir: str):
        self.embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vs = Chroma(
            embedding_function=self.embedding,
            persist_directory=persist_dir,
            collection_name="companies",
        )

    def _combine_text(self, meta: Dict, evidence: str) -> str:
        parts = [
            meta.get("name") or "",
            meta.get("industry_category") or "",
            meta.get("industry_subcategory") or "",
            meta.get("location_city") or "",
            meta.get("location_district") or "",
            meta.get("website") or "",
            evidence or "",
        ]
        return " ".join(parts).lower()

    def _keyword_hits(self, text: str, keywords: Iterable[str]) -> int:
        hits = 0
        for kw in keywords:
            k = (kw or "").strip().lower()
            if not k:
                continue
            if k in text:
                hits += 1
        return hits

    def _normalize_keywords(self, keywords: Optional[Iterable[str]]) -> List[str]:
        if not keywords:
            return []
        out = []
        for kw in keywords:
            if not isinstance(kw, str):
                continue
            cleaned = re.sub(r"\s+", " ", kw.strip())
            if cleaned and cleaned not in out:
                out.append(cleaned)
        return out

    def search(
        self,
        query: str,
        top_k: int = 5,
        candidate_ids: Optional[List[int]] = None,
        keywords: Optional[Iterable[str]] = None,
        fetch_k: Optional[int] = None,
        max_score: Optional[float] = None,
    ) -> List[Dict]:
        filt = None
        if candidate_ids:
            filt = {"company_id": {"$in": [int(x) for x in candidate_ids]}}

        fetch_k = fetch_k or max(top_k * 4, 20)
        raw = self.vs.similarity_search_with_score(query, k=fetch_k, filter=filt)
        norm_keywords = self._normalize_keywords(keywords)

        scored: List[Tuple[int, float, Dict]] = []
        for d, score in raw:
            m = d.metadata
            evidence = d.page_content[:300]
            text = self._combine_text(m, evidence)
            hit_count = self._keyword_hits(text, norm_keywords)
            scored.append(
                (
                    hit_count,
                    score,
                    {
                        "company_id": m.get("company_id"),
                        "name": m.get("name"),
                        "industry_category": m.get("industry_category"),
                        "industry_subcategory": m.get("industry_subcategory"),
                        "location_city": m.get("location_city"),
                        "location_district": m.get("location_district"),
                        "website": m.get("website"),
                        "evidence": evidence,
                    },
                )
            )

        scored.sort(key=lambda x: (-x[0], x[1]))

        filtered = scored

        if norm_keywords:
            filtered = [item for item in filtered if item[0] > 0]

        return [item[2] for item in filtered[:top_k]]