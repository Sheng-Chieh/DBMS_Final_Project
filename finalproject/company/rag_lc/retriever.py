from __future__ import annotations
from typing import List, Dict, Optional

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

    def search(self, query: str, top_k: int = 5, candidate_ids: Optional[List[int]] = None) -> List[Dict]:
        filt = None
        if candidate_ids:
            filt = {"company_id": {"$in": [int(x) for x in candidate_ids]}}

        docs = self.vs.similarity_search(query, k=top_k, filter=filt)

        out = []
        for d in docs:
            m = d.metadata
            out.append(
                {
                    "company_id": m.get("company_id"),
                    "name": m.get("name"),
                    "industry_category": m.get("industry_category"),
                    "industry_subcategory": m.get("industry_subcategory"),
                    "location_city": m.get("location_city"),
                    "location_district": m.get("location_district"),
                    "website": m.get("website"),
                    "evidence": d.page_content[:300],
                }
            )
        return out