from django.shortcuts import render
from django.http import Http404
from .models import Company

import json
import os
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from .rag_lc.retriever import CompanyRetrieverLC

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

@csrf_exempt
def chat_recommend_companies_lc(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    payload = json.loads(request.body or "{}")
    messages = payload.get("messages") or []
    user_query = (payload.get("message") or "").strip()

    if not user_query:
        for m in reversed(messages):
            if m.get("role") == "user":
                content = (m.get("content") or "").strip()
                if content:
                    user_query = content
                    break

    if not user_query:
        return JsonResponse({"error": "至少需要輸入一個需求描述"}, status=400)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2,
    )

    def extract_json_array(text: str):
        # Try exact JSON first, then extract the first top-level array.
        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"\[.*\]", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    def normalize_keywords(items):
        keywords = []
        if not isinstance(items, list):
            return keywords
        for item in items:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned and cleaned not in keywords:
                    keywords.append(cleaned)
        return keywords

    def fallback_keywords(text: str):
        keywords = []
        parts = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+", text)
        for part in parts:
            if re.match(r"^[A-Za-z0-9]+$", part):
                if part not in keywords:
                    keywords.append(part)
            else:
                if len(part) <= 2:
                    if part not in keywords:
                        keywords.append(part)
                else:
                    for i in range(len(part) - 1):
                        piece = part[i : i + 2]
                        if piece not in keywords:
                            keywords.append(piece)
        return keywords

    keyword_prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "你是關鍵字擷取助手。只輸出 JSON 陣列，元素為關鍵字字串。不要輸出其他內容。"),
            ("user", "使用者輸入：{user_text}"),
        ]
    )

    kw_msg = keyword_prompt.format_messages(user_text=user_query)
    kw_resp = llm.invoke(kw_msg).content.strip()
    kw_arr = extract_json_array(kw_resp)
    keywords = normalize_keywords(kw_arr)
    if not keywords:
        keywords = fallback_keywords(user_query)
    keywords = keywords[:8]

    # 1) MySQL 硬篩選（使用關鍵字擷取結果）
    candidates = Company.objects.search_chat_with_keywords(keywords)[:200]
    candidate_ids = [c["company_id"] for c in candidates]
    
    if not candidate_ids:
        return JsonResponse({
            "answer": "很抱歉，無法找到符合條件的公司。",
            "assistant_message": "很抱歉，沒有找到符合條件的公司。你可以換個條件再試試。",
            "recommendations": [],
        })

    if keywords:
        full_search_context = f"需求：{user_query}；關鍵字：{', '.join(keywords)}"
    else:
        full_search_context = f"需求：{user_query}"

    # 2) LangChain Retriever
    retriever = CompanyRetrieverLC(persist_dir="rag_data_lc")
    retrieved = retriever.search(user_query, top_k=5, candidate_ids=candidate_ids)

    # 3) Gemini 產生推薦理由
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "你是公司推薦助理。根據使用者需求和提供的公司資料進行推薦。\n"
             "請輸出 JSON 陣列，每個元素必須含以下欄位：\n"
             "- company_id: 公司ID\n"
             "- why: 推薦理由（1~2句，說明為什麼推薦這家公司）\n"
             "只輸出有效的 JSON 陣列，不要輸出其他內容。"),
            ("user",
             "使用者條件：{search_context}\n\n"
             "符合初步篩選的公司資料：\n{companies_json}\n\n"
             "請根據使用者的需求和公司資料，為每家公司提供推薦理由。"),
        ]
    )

    companies_json = json.dumps(retrieved, ensure_ascii=False, indent=2)
    msg = prompt.format_messages(search_context=full_search_context, companies_json=companies_json)
    resp = llm.invoke(msg).content.strip()

    why_map = {}
    try:
        # 嘗試從 JSON 回應中提取推薦理由
        arr = extract_json_array(resp)
        if not isinstance(arr, list):
            raise ValueError("LLM response is not a JSON array")
        why_map = {int(x["company_id"]): x["why"] for x in arr if "company_id" in x and "why" in x}
    except Exception as e:
        # 如果 JSON 解析失敗，記錄並使用默認理由
        print(f"LLM 回應解析失敗: {e}, 回應內容: {resp}")

    # 修復 3: 改進推薦理由展示，使用 evidence 補充
    for r in retrieved:
        company_id = int(r["company_id"])
        if company_id in why_map:
            r["why"] = why_map[company_id]
        else:
            # 使用基於 evidence 的默認理由
            evidence = r.get("evidence", "")
            industry = r.get("industry_category", "")
            location = r.get("location_city", "")
            default_why = f"符合您的條件。{industry}産業"
            if location:
                default_why += f"位於{location}"
            if evidence:
                default_why += f"，特別是{evidence[:50]}"
            r["why"] = default_why

    assistant_message = f"收到，我會根據「{full_search_context}」提供推薦。以下是較符合的公司與理由。"

    return JsonResponse({
        "answer": "以下是推薦公司與理由：",
        "assistant_message": assistant_message,
        "search_context": full_search_context,
        "recommendations": retrieved,
    })

@ensure_csrf_cookie
def company_chat_page(request):
    return render(request, "company/company_chat.html")