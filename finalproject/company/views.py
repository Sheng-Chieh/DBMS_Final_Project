from django.shortcuts import render
from django.http import Http404
from django.conf import settings
from .models import Company

import jieba
import jieba.analyse

from functools import lru_cache
from pathlib import Path
import json
import os
import re
import time

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from .rag_lc.retriever import CompanyRetrieverLC

RAG_PERSIST_DIR = str(Path(settings.BASE_DIR) / "rag_data_lc")
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "shibing624/text2vec-base-chinese")

RAG_SYNONYMS = {
    "單車": ["自行車", "腳踏車", "bike", "bicycle"],
    "自行車": ["單車", "腳踏車", "bike", "bicycle"],
    "腳踏車": ["單車", "自行車", "bike", "bicycle"],
}


def _normalize_keyword(keyword: str) -> str:
    return (keyword or "").strip().lower()


def expand_keywords(keywords):
    expanded = []
    for kw in keywords:
        k = _normalize_keyword(kw)
        if not k:
            continue
        if k not in expanded:
            expanded.append(k)
        for syn in RAG_SYNONYMS.get(k, []):
            s = _normalize_keyword(syn)
            if s and s not in expanded:
                expanded.append(s)
    return expanded


def extract_evidence_snippet(evidence: str) -> str:
    if not evidence:
        return ""
    for line in evidence.splitlines():
        line = line.strip()
        if line.startswith("簡介:"):
            return line.replace("簡介:", "", 1).strip()
    return evidence.strip()


def build_fallback_why(result, display_keywords):
    matched = result.get("matched_keywords") or []
    industry = result.get("industry_category") or ""
    sub = result.get("industry_subcategory") or ""
    location = result.get("location_city") or ""
    snippet = extract_evidence_snippet(result.get("evidence") or "")
    snippet = re.sub(r"\s+", " ", snippet)

    pieces = []
    if matched:
        pieces.append(f"涵蓋關鍵字「{'、'.join(matched[:3])}」")
    elif display_keywords:
        pieces.append(f"與「{'、'.join(display_keywords[:2])}」需求相關")

    if industry:
        if sub:
            pieces.append(f"{industry}/{sub}產業")
        else:
            pieces.append(f"{industry}產業")

    if location:
        pieces.append(f"位於{location}")

    if snippet:
        pieces.append(f"簡介提到「{snippet[:40]}」")

    if not pieces:
        return "符合您的條件。"

    return "，".join(pieces) + "。"


@lru_cache(maxsize=1)
def get_retriever():
    return CompanyRetrieverLC(persist_dir=RAG_PERSIST_DIR, model_name=RAG_EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_llm():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite-preview",
        google_api_key=api_key,
        temperature=0.2,
    )

def search_companies(request):
    # 從 URL GET 請求中獲取多個過濾參數
    query = request.GET.get('q', '').strip()
    industry_param = request.GET.get('industry', '').strip()
    location_param = request.GET.get('location', '').strip()

    has_search_criteria = bool(query or industry_param or location_param)
    
    # 呼叫寫在 models.py 裡的 SQL 查詢方法
    companies_data = Company.objects.search_with_raw_sql(query, industry_param, location_param)

    display_companies = companies_data if has_search_criteria else companies_data[:5]
        
    context = {
        'companies': display_companies,
        'query': query,
        'sel_industry': industry_param,  
        'sel_location': location_param,  
        'has_search_criteria': has_search_criteria,
    }
    
    return render(request, 'company/company_search.html', context)


def company_detail(request, company_id):
    # 呼叫寫在 models.py 裡的 SQL 查詢方法
    company_data = Company.objects.get_detail_with_raw_sql(company_id)
        
    # 如果回傳 None 代表找不到該公司，觸發 404
    if not company_data:
        raise Http404("找不到該公司資料")
        
    context = {
        'company': company_data
    }
    
    return render(request, 'company/company_detail.html', context)

def normalize_llm_text(text):
    """將 LLM 回傳的物件 (可能為 LangChain AIMessage、Gemini List 結構等) 正規化為純文字字串"""
    if hasattr(text, "content"):
        text = text.content
        
    if isinstance(text, list):
        parts = []
        for item in text:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item.get("text") or ""))
            else:
                parts.append(str(item))
        return "\n".join([p for p in parts if p])
        
    if isinstance(text, dict) and "text" in text:
        return str(text.get("text") or "")
        
    return str(text)

def extract_json_array(text):
    try:
        cleaned = (text or "").strip()
        if not cleaned:
            return []
        cleaned = re.sub(r"^```(?:json)?\s*|```$", "", cleaned, flags=re.MULTILINE).strip()
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        return json.loads(cleaned)
    except Exception:
        return []


def repair_json_array(llm, raw_text: str) -> str:
    if not llm:
        return "[]"
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是 JSON 修復助手。請把使用者提供的內容修正成『純 JSON 陣列』，只輸出 JSON。",
            ),
            ("user", "請將以下內容修正成 JSON 陣列：\n{raw_text}"),
        ]
    )
    msg = prompt.format_messages(raw_text=raw_text)
    return normalize_llm_text(llm.invoke(msg))

@csrf_exempt
def chat_recommend_companies_lc(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
        
    payload = json.loads(request.body or "{}")
    messages = payload.get("messages") or []
    user_query = (payload.get("message") or "").strip()
    
    # 若無最新查詢，嘗試從歷史對話中尋找最後一句 user 發言
    if not user_query:
        for m in reversed(messages):
            if m.get("role") == "user" and m.get("content", "").strip():
                user_query = m["content"].strip()
                break
                    
    if not user_query:
        return JsonResponse({"error": "請提供查詢內容"}, status=400)

    def event_stream():
        def send_progress(text):
            """回傳當前處理進度給前端 (SSE 格式)"""
            return f"data: {json.dumps({'type': 'progress', 'text': text}, ensure_ascii=False)}\n\n"

        def send_result(payload):
            """回傳最終處理結果給前端 (SSE 格式)"""
            return f"data: {json.dumps({'type': 'result', 'payload': payload}, ensure_ascii=False)}\n\n"

        def send_error(text):
            """回傳錯誤訊息給前端 (SSE 格式)"""
            return f"data: {json.dumps({'type': 'error', 'text': text}, ensure_ascii=False)}\n\n"

        try:
            # =========================================================
            # Step 1: 需求分析與關鍵字擷取 (Jieba)
            # =========================================================
            yield send_progress("正在分析您的需求與擷取關鍵字...")
            
            keywords = jieba.analyse.extract_tags(user_query, topK=5)
            if not keywords:
                keywords = [word for word in jieba.lcut(user_query) if len(word.strip()) > 1]

            display_keywords = keywords[:]
            expanded_keywords = expand_keywords(keywords)

            search_context = f"使用者查詢：{user_query} | 關鍵字：{', '.join(display_keywords)}" if display_keywords else f"使用者查詢：{user_query}"

            # =========================================================
            # Step 2: 向量資料庫檢索 (ChromaDB + Hybrid Search)
            # =========================================================
            yield send_progress(f"正在資料庫中搜尋相符的公司 (分析了 {len(expanded_keywords)} 個特徵)...")
            
            retriever = get_retriever()
            
            # 使用較嚴格的門檻 (distance_threshold=0.9 或至少命中1個關鍵字) 搜尋
            retrieved = retriever.search(
                query=user_query, top_k=3, keywords=expanded_keywords, fetch_k=30,
                min_keyword_hits=1, distance_threshold=0.9
            )

            # 若查無結果，放寬門檻再試一次 (distance_threshold=1.2)
            if not retrieved and expanded_keywords:
                retrieved = retriever.search(
                    query=user_query, top_k=3, keywords=expanded_keywords, fetch_k=30,
                    min_keyword_hits=0, distance_threshold=1.2
                )

            if not retrieved:
                yield send_result({
                    "answer": "抱歉，目前找不到符合條件的公司。",
                    "assistant_message": "抱歉，目前找不到符合條件的公司。",
                    "recommendations": [],
                })
                return

            # =========================================================
            # Step 3: 交給 Gemini LLM 腦力激盪並生成推薦理由
            # =========================================================
            yield send_progress(f"已找到 {len(retrieved)} 家相關公司，正在請 AI 腦力激盪並撰寫推薦理由...")
            
            llm = get_llm()
            resp = "[]"
            
            if llm:
                prompt = ChatPromptTemplate.from_messages([
                    ("system",
                     "你是一個專業的台灣企業推薦助手。請根據檢索到的公司資料，以繁體中文回答。\n"
                     "請回傳純 JSON 陣列，不要有 markdown 標記，格式如下：\n"
                     "[\n  {{\n    \"company_id\": 1,\n    \"why\": \"推薦這家公司的理由(約30字)\"\n  }}\n]\n"
                     "注意：回傳的 JSON 必須包含所有傳入的公司，並且只輸出 JSON 陣列。"
                    ),
                    ("user", "搜索脈絡：{search_context}\n\n檢索到的公司：\n{companies_json}\n\n請根據上述資料給出推薦理由 JSON：")
                ])

                # 準備傳給 LLM 參考的 JSON (不含不必要的欄位以節省 Token)
                llm_candidates = [
                    {k: r.get(k) for k in ("company_id", "name", "industry_category", "industry_subcategory", "location_city", "location_district", "evidence")} 
                    for r in retrieved
                ]
                msg = prompt.format_messages(search_context=search_context, companies_json=json.dumps(llm_candidates, ensure_ascii=False))
                
                try:
                    resp = normalize_llm_text(llm.invoke(msg))
                except Exception as e:
                    print(f"LLM 呼叫失敗: {e}")
            else:
                print("GEMINI_API_KEY not set; using fallback reasons only.")

            # =========================================================
            # Step 4: 解析回傳結果與容錯處理 (Fallback)
            # =========================================================
            yield send_progress("正在整理最後的推薦結果出來給您...")
            time.sleep(1) # 假裝處理時間，讓前端有機會顯示進度訊息

            why_map = {}
            try:
                arr = extract_json_array(resp)
                
                # 如果首次解析失敗，嘗試修復 JSON
                if not arr and llm:
                    arr = extract_json_array(repair_json_array(llm, resp))

                if isinstance(arr, list):
                    for item in arr:
                        if isinstance(item, dict) and item.get("company_id") and item.get("why"):
                            try:
                                why_map[int(item["company_id"])] = str(item["why"]).strip()
                            except (TypeError, ValueError):
                                pass
            except Exception as e:
                print(f"LLM 回應解析失敗: {e}, 原始回應內容: {resp}")

            # 依解析出來的 JSON 寫回各公司物件中，若沒匹配到則使用內建邏輯 (build_fallback_why) 產生理由
            for r in retrieved:
                company_id = int(r["company_id"])
                r["why"] = why_map.get(company_id) or build_fallback_why(r, display_keywords)

            # =========================================================
            # Step 5: 回傳最終推薦清單
            # =========================================================
            yield send_result({
                "answer": "這是我為您找到的推薦公司：",
                "assistant_message": f"收到，我已經根據「{search_context}」為您找到最適合的公司。",
                "recommendations": retrieved,
            })

        except Exception as e:
            print(f"Streaming error: {e}")
            yield send_error("發生未知的錯誤，未能完成推薦。")

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

@ensure_csrf_cookie
def company_chat_page(request):
    return render(request, "company/company_chat.html")