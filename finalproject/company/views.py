from django.shortcuts import render
from django.shortcuts import render
from django.http import Http404
from django.db import connection

# 輔助函式：將 SQL 查詢結果轉換成 Dictionary，方便前端 Template 讀取
def dictfetchall(cursor):
    "將游標返回的每一行轉為字典格式"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def search_companies(request):
    # 從 URL GET 請求中獲取多個過濾參數
    query = request.GET.get('q', '').strip()
    industry_param = request.GET.get('industry', '').strip()
    location_param = request.GET.get('location', '').strip()
    
    # 開啟資料庫游標
    with connection.cursor() as cursor:
        # 使用 1=1 作為基底條件，方便後續動態拼接 SQL
        sql = """
            SELECT company_id, name, industry_category, industry_subcategory, description, location_city, location_district, website 
            FROM companies 
            WHERE 1=1
        """
        params = []
        
        # 1. 處理關鍵字條件 (搜尋公司名稱 或 描述)
        if query:
            sql += " AND (name LIKE %s OR description LIKE %s)"
            params.extend([f"%{query}%", f"%{query}%"])
            
        # 2. 處理多選「產業類型」條件 (支援逗號分隔)
        if industry_param:
            industries = [i.strip() for i in industry_param.split(',') if i.strip()]
            if industries:
                industry_conditions = []
                for ind in industries:
                    if '-' in ind:
                        # 包含子分類的精確比對 (例如 "科技-軟體工程")
                        cat, sub = ind.split('-', 1)
                        industry_conditions.append("(industry_category = %s AND industry_subcategory = %s)")
                        params.extend([cat, sub])
                    else:
                        # 只有大分類的比對 (例如 "科技")
                        industry_conditions.append("industry_category = %s")
                        params.append(ind)
                # 將多個產業條件用 OR 串聯，並用括號包起來
                sql += f" AND ({' OR '.join(industry_conditions)})"
                
        # 3. 處理多選「地點」條件 (支援逗號分隔)
        if location_param:
            locations = [loc.strip() for loc in location_param.split(',') if loc.strip()]
            if locations:
                location_conditions = []
                for loc in locations:
                    if '-' in loc:
                        # 包含行政區的精確比對 (例如 "台北市-中正區")
                        city, dist = loc.split('-', 1)
                        location_conditions.append("(location_city = %s AND location_district = %s)")
                        params.extend([city, dist])
                    else:
                        # 只有城市的比對 (例如 "台北市")
                        location_conditions.append("location_city = %s")
                        params.append(loc)
                # 將多個地點條件用 OR 串聯，並用括號包起來
                sql += f" AND ({' OR '.join(location_conditions)})"
            
        # 執行最後組合完成的 SQL
        cursor.execute(sql, params)
        companies_data = dictfetchall(cursor)
        
    context = {
        'companies': companies_data,
        'query': query,
        'sel_industry': industry_param,  # 將選中的產業回傳給 Template，維持 Modal 勾選狀態
        'sel_location': location_param,  # 將選中的地點回傳給 Template，維持 Modal 勾選狀態
    }
    
    return render(request, 'company/company_search.html', context)

def company_detail(request, company_id):
    with connection.cursor() as cursor:
        # 透過 company_id 查詢單一公司資料
        sql = """
            SELECT company_id, name, industry_category, industry_subcategory, description, location_city, location_district, website 
            FROM companies 
            WHERE company_id = %s
        """
        cursor.execute(sql, [company_id])
        row = cursor.fetchone()
        
        # 如果找不到該公司，回傳 404 錯誤頁面
        if not row:
            raise Http404("找不到該公司資料")
            
        # 將單筆查詢結果 (Tuple) 轉換為 Dictionary
        columns = [col[0] for col in cursor.description]
        company_data = dict(zip(columns, row))
        
    context = {
        'company': company_data
    }
    
    return render(request, 'company/company_detail.html', context)