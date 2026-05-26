from django.shortcuts import render
from django.http import Http404
from django.conf import settings
from .models import Company
from accounts.views import login_required

from functools import lru_cache
from pathlib import Path
import json
import re

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from .rag_lc.retriever import CompanyRetrieverLC

import torch
import torch.nn as nn
from langchain_huggingface import HuggingFaceEmbeddings

RAG_PERSIST_DIR = str(Path(settings.BASE_DIR) / "rag_data_lc")
RAG_EMBEDDING_MODEL = settings.RAG_EMBEDDING_MODEL


@login_required
def search_companies(request):
    # 從 URL GET 請求中獲取多個過濾參數
    query = request.GET.get('q', '').strip()
    industry_param = request.GET.get('industry', '').strip()
    location_param = request.GET.get('location', '').strip()

    has_search_criteria = bool(query or industry_param or location_param)
    
    # 呼叫寫在 models.py 裡的 SQL 查詢方法
    companies_data = Company.objects.search_with_raw_sql(query, industry_param, location_param) or []

    display_companies = companies_data if has_search_criteria else companies_data[:5]
        
    context = {
        'companies': display_companies,
        'query': query,
        'sel_industry': industry_param,  
        'sel_location': location_param,  
        'has_search_criteria': has_search_criteria,
    }
    
    return render(request, 'company/company_search.html', context)


@login_required
def company_detail(request, company_id):
    # 呼叫寫在 models.py 裡的 SQL 查詢方法
    company_data = Company.objects.get_detail_with_raw_sql(company_id)
        
    # 如果回傳 None 代表找不到該公司，觸發 404
    if not company_data:
        raise Http404("找不到該公司資料")
        
    # 獲取當前登入使用者的 user_id
    user_id = request.session.get('user_id')
    
    # 查詢與使用者同系所，且在該公司工作或服務過的校友名單
    alumni_list = []
    if user_id:
        alumni_list = Company.objects.get_alumni_by_department_and_company(user_id, company_id) or []
        
    context = {
        'company': company_data,
        'alumni_list': alumni_list
    }
    
    return render(request, 'company/company_detail.html', context)


# ======================== RAG ==================================

def build_fallback_why(result):
    return "依照這個條件，目前找不到類似的公司。"


@lru_cache(maxsize=1)
def get_retriever():
    return CompanyRetrieverLC(persist_dir=RAG_PERSIST_DIR, model_name=RAG_EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_llm():
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return None
    return ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=api_key,
        temperature=0.2,
    )


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


def build_no_results_message(user_query):
    llm = get_llm()
    if not llm:
        return "依照這個條件，目前找不到類似的公司。"

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一個專業的台灣企業推薦助手。請用正式語氣回答。\n"
         "目前沒有符合條件的公司，請產生一句簡潔回覆（約20-30字），" 
         "需要呼應使用者條件，但不要捏造公司名稱。只回傳純文字。"
        ),
        ("user", "使用者查詢：{search_context}\n\n請產生回覆：")
    ])

    msg = prompt.format_messages(search_context=user_query)
    try:
        text = normalize_llm_text(llm.invoke(msg))
        return (text or "").strip() or "依照這個條件，目前找不到類似的公司。"
    except Exception as e:
        print(f"LLM 呼叫失敗: {e}")
        return "依照這個條件，目前找不到類似的公司。"

@login_required
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
            return f"data: {json.dumps({'type': 'progress', 'text': text}, ensure_ascii=False)}\n\n".encode("utf-8")

        def send_result(payload):
            """回傳最終處理結果給前端 (SSE 格式)"""
            return f"data: {json.dumps({'type': 'result', 'payload': payload}, ensure_ascii=False)}\n\n".encode("utf-8")

        def send_error(text):
            """回傳錯誤訊息給前端 (SSE 格式)"""
            return f"data: {json.dumps({'type': 'error', 'text': text}, ensure_ascii=False)}\n\n".encode("utf-8")

        try:
            yield send_progress("正在資料庫中搜尋相符的公司...")
            
            retriever = get_retriever()
            retrieved = retriever.search(query=user_query, top_k=3)

            if not retrieved:
                no_results_message = build_no_results_message(user_query)
                yield send_result({
                    "answer": no_results_message,
                    "assistant_message": no_results_message,
                    "recommendations": [],
                })
                return

            yield send_progress(f"已找到 {len(retrieved)} 家相關公司，正在整理推薦理由...")
            
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
                msg = prompt.format_messages(search_context=user_query, companies_json=json.dumps(llm_candidates, ensure_ascii=False))
                
                try:
                    resp = normalize_llm_text(llm.invoke(msg))
                except Exception as e:
                    print(f"LLM 呼叫失敗: {e}")
            else:
                print("GEMINI_API_KEY not set; using fallback reasons only.")

            yield send_progress("正在整理最後的推薦結果出來給您...")

            why_map = {}
            try:
                arr = extract_json_array(resp)

                if isinstance(arr, list):
                    for item in arr:
                        if isinstance(item, dict) and item.get("company_id") and item.get("why"):
                            try:
                                why_map[int(item["company_id"])] = str(item["why"]).strip()
                            except (TypeError, ValueError):
                                pass
            except Exception as e:
                print(f"LLM 回應解析失敗: {e}, 原始回應內容: {resp}")

            for r in retrieved:
                company_id = int(r["company_id"])
                r["why"] = why_map.get(company_id) or build_fallback_why(r)

            yield send_result({
                "answer": "這是我為您找到的推薦公司：",
                "assistant_message": f"收到，我已經為您找到適合的公司。",
                "recommendations": retrieved,
            })

        except Exception as e:
            print(f"Streaming error: {e}")
            yield send_error("發生未知的錯誤，未能完成推薦。")

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

@login_required
@ensure_csrf_cookie
def company_chat_page(request):
    return render(request, "company/company_chat.html")