from django.shortcuts import render
from django.shortcuts import render
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
    # 獲取 GET 請求中的搜尋字串 'q'
    query = request.GET.get('q', '')
    
    # 開啟資料庫游標 (連線到你 settings.py 設定的 final_project)
    with connection.cursor() as cursor:
        if query:
            # 準備純 SQL 語法，使用 %s 防止 SQL Injection
            sql = """
                SELECT company_id, name, industry, description, location, website 
                FROM companies 
                WHERE name LIKE %s OR industry LIKE %s
            """
            search_param = f"%{query}%"
            # 執行 SQL
            cursor.execute(sql, [search_param, search_param])
        else:
            # 沒有搜尋條件時，列出所有公司
            sql = "SELECT company_id, name, industry, description, location, website FROM companies"
            cursor.execute(sql)
            
        # 取得所有資料
        companies_data = dictfetchall(cursor)
        
    context = {
        'companies': companies_data,
        'query': query,
    }
    
    return render(request, 'company/company_search.html', context)