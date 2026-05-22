from __future__ import annotations
from typing import List, Dict, Optional
from functools import lru_cache
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


def _get_setting(name: str, default=None):
    if not settings.configured:
        return default
    return getattr(settings, name, default)


def _get_default_embedding_model() -> str:
    return _get_setting("RAG_EMBEDDING_MODEL", "") or ""


def _normalize_persist_dir(persist_dir: str) -> str:
    return str(Path(persist_dir).expanduser().resolve())


@lru_cache(maxsize=2)
def _get_embedding(model_name: str) -> HuggingFaceEmbeddings:
    rag_device = _get_setting("RAG_DEVICE")
    hf_token = _get_setting("HF_TOKEN")
    model_kwargs = {'device': rag_device, 'token': hf_token}
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
        self.model_name = model_name or _get_default_embedding_model()
        if not self.model_name:
            raise ImproperlyConfigured("RAG_EMBEDDING_MODEL is required to initialize CompanyRetrieverLC")
        self.vs = _get_vectorstore(self.persist_dir, self.model_name)
        
    def search(self, query: str, top_k: int = 3, max_distance: Optional[float] = None) -> List[Dict]:
        """
        向量相似度搜尋：
        - Chroma similarity_search_with_score 回傳的 score 通常是 distance
        - distance 越小代表越相似
        - 若設定 max_distance，會過濾掉距離過大的結果
        """
        raw = self.vs.similarity_search_with_score(query, k=top_k)

        results = []
        for d, score in raw:
            score = float(score)

            # 如果有設定距離門檻，且距離太大，就跳過
            if max_distance is not None and score > max_distance:
                continue

            m = d.metadata
            evidence = d.page_content[:300]

            results.append(
                {
                    "company_id": m.get("company_id"),
                    "name": m.get("name"),
                    "industry_category": m.get("industry_category"),
                    "industry_subcategory": m.get("industry_subcategory"),
                    "location_city": m.get("location_city"),
                    "location_district": m.get("location_district"),
                    "website": m.get("website"),
                    "evidence": evidence,
                    "vector_distance": score,
                }
            )

        return results
