from django.shortcuts import render
from django.http import Http404
from .models import Company

def search_companies(request):
    # 從 URL GET 請求中獲取多個過濾參數
    query = request.GET.get('q', '').strip()
    industry_param = request.GET.get('industry', '').strip()
    location_param = request.GET.get('location', '').strip()
    
    # 呼叫寫在 models.py 裡的 SQL 查詢方法
    companies_data = Company.objects.search_with_raw_sql(query, industry_param, location_param)
        
    context = {
        'companies': companies_data,
        'query': query,
        'sel_industry': industry_param,  
        'sel_location': location_param,  
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