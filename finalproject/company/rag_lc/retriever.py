from __future__ import annotations
from typing import List, Dict, Optional, Iterable, Tuple
from functools import lru_cache
from pathlib import Path
import os
import re

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

DEFAULT_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "shibing624/text2vec-base-chinese")


def _normalize_persist_dir(persist_dir: str) -> str:
    return str(Path(persist_dir).expanduser().resolve())


@lru_cache(maxsize=2)
def _get_embedding(model_name: str) -> HuggingFaceEmbeddings:
    model_kwargs = {'device': 'mps'} # 'cuda' for NVIDIA GPU, 'mps' for Apple Silicon
    encode_kwargs = {'normalize_embeddings': False}
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )


@lru_cache(maxsize=4)
def _get_vectorstore(persist_dir: str, model_name: str) -> Chroma:
    embedding = _get_embedding(model_name)
    return Chroma(
        embedding_function=embedding,
        persist_directory=persist_dir,
        collection_name="companies",
    )

class CompanyRetrieverLC:
    def __init__(self, persist_dir: str, model_name: Optional[str] = None):
        self.persist_dir = _normalize_persist_dir(persist_dir)
        self.model_name = model_name or DEFAULT_EMBEDDING_MODEL
        self.vs = _get_vectorstore(self.persist_dir, self.model_name)

    def _combine_text(self, meta: Dict, evidence: str) -> str:
        parts = [
            meta.get("name") or "",
            meta.get("industry_category") or "",
            meta.get("industry_subcategory") or "",
            meta.get("location_city") or "",
            meta.get("location_district") or "",
            evidence or "",
        ]
        return " ".join(parts).lower()

    def _keyword_hits(self, text: str, keywords: Iterable[str]) -> Tuple[int, List[str]]:
        hits: List[str] = []
        for kw in keywords:
            k = (kw or "").strip().lower()
            if not k:
                continue
            if k in text:
                hits.append(k)
        return len(hits), hits

    def _normalize_keywords(self, keywords: Optional[Iterable[str]]) -> List[str]:
        if not keywords:
            return []
            
        out = []
        for kw in keywords:
            if not isinstance(kw, str):
                continue
            k = kw.strip().lower()
            if k and k not in out:
                out.append(k)
        return out

    def search(
        self,
        query: str,
        top_k: int = 5,
        keywords: Optional[Iterable[str]] = None,
        fetch_k: Optional[int] = None,
        min_keyword_hits: int = 0,
        distance_threshold: float = 1.2,
    ) -> List[Dict]:
        
        # 1. 直接進行純向量相似度檢索
        fetch_k = fetch_k or max(top_k * 4, 20)
        raw = self.vs.similarity_search_with_score(query, k=fetch_k)
        
        # 2. 關鍵字正規化
        norm_keywords = self._normalize_keywords(keywords)

        scored: List[Tuple[int, float, Dict]] = []
        for d, score in raw:
            m = d.metadata
            evidence = d.page_content[:300]
            text = self._combine_text(m, evidence)
            
            # 計算關鍵字命中數
            hit_count, matched_keywords = self._keyword_hits(text, norm_keywords)
            
            scored.append(
                (
                    hit_count,
                    score, # ChromaDB 的 L2 距離分數 (通常越小越相似)
                    {
                        "company_id": m.get("company_id"),
                        "name": m.get("name"),
                        "industry_category": m.get("industry_category"),
                        "industry_subcategory": m.get("industry_subcategory"),
                        "location_city": m.get("location_city"),
                        "location_district": m.get("location_district"),
                        "website": m.get("website"),
                        "evidence": evidence,
                        "matched_keywords": matched_keywords,
                        "vector_distance": float(score),
                    },
                )
            )

        # 3. 混合排序邏輯 (Hybrid Re-ranking)
        # 排序規則：優先比較「關鍵字命中數」(降冪，越高越好)
        # 若命中數相同，再比較「向量距離分數」(升冪，越小越相似)
        scored.sort(key=lambda x: (-x[0], x[1]))

        filtered = scored
        # 如果有傳入關鍵字，設定篩選門檻
        if norm_keywords:
            # 只要命中關鍵字達標，或是雖然沒命中關鍵字但向量距離夠近，就保留
            # 這樣可以包容同義詞 (如：單車 vs 自行車)
            filtered = [
                item
                for item in filtered
                if item[0] >= min_keyword_hits or item[1] < distance_threshold
            ]

        # 4. 回傳最終的 Top K
        return [item[2] for item in filtered[:top_k]]