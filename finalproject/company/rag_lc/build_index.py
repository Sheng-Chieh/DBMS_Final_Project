from __future__ import annotations
import os
import sys
import django
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finalproject.settings")
django.setup()

from django.conf import settings
from django.db import connection

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

EMBEDDING_MODEL = settings.RAG_EMBEDDING_MODEL


def fetch_companies():
    sql = """
        SELECT company_id, name, industry_category, industry_subcategory,
               description, description_detail, location_city, location_district, website
        FROM companies
    """
    with connection.cursor() as cursor:
        cursor.execute(sql)
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


def to_doc(c):
    detail = c.get("description_detail") or c.get("description") or ""
    text = (
        f"公司名稱: {c['name']}\n"
        f"產業: {c['industry_category']} / {c['industry_subcategory']}\n"
        f"地點: {c['location_city']}{c['location_district']}\n"
        f"網站: {c.get('website') or ''}\n"
        f"簡介: {detail}\n"
    )
    return Document(
        page_content=text,
        metadata={
            "company_id": int(c["company_id"]),
            "name": c["name"],
            "industry_category": c["industry_category"],
            "industry_subcategory": c["industry_subcategory"],
            "location_city": c["location_city"],
            "location_district": c["location_district"],
            "website": c.get("website") or "",
        },
    )


def main():
    persist_dir = str(Path(settings.BASE_DIR) / "rag_data_lc")
    embedding = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    companies = fetch_companies()
    docs = [to_doc(c) for c in companies]

    vs = Chroma.from_documents(
        documents=docs,
        embedding=embedding,
        persist_directory=persist_dir,
        collection_name="companies",
    )
    vs.persist()
    print(f"Indexed {len(docs)} companies into {persist_dir} using {EMBEDDING_MODEL}")


if __name__ == "__main__":
    main()