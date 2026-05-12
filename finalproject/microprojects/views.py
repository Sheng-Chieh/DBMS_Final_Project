from django.shortcuts import render, redirect
from django.db import connection

def project_list(request):
    # 1. 取得網址列上的搜尋參數 (預設為空字串)
    search_industry = request.GET.get('industry', '')
    search_company = request.GET.get('company', '')
    search_tag = request.GET.get('tag', '')

    with connection.cursor() as cursor:
        # 2. 撈取過濾器下拉選單所需的選項資料
        cursor.execute("SELECT DISTINCT industry_category FROM companies WHERE industry_category IS NOT NULL ORDER BY industry_category")
        filter_industries = [row[0] for row in cursor.fetchall()]

        # 多撈出 industry_category 給前端的 JavaScript 使用
        cursor.execute("SELECT company_id, name, industry_category FROM companies ORDER BY name")
        filter_companies = cursor.fetchall()

        cursor.execute("SELECT tag_id, tag_name FROM tag_dictionary ORDER BY tag_category, tag_name")
        filter_tags = cursor.fetchall()

        # 3. 動態組合 SQL 語法 (經典技巧：WHERE 1=1 方便後面一直接 AND)
        sql = """
            SELECT 
                m.project_id, 
                m.title, 
                m.description, 
                c.industry_category, 
                c.name, 
                GROUP_CONCAT(t.tag_name SEPARATOR ', ') as tags
            FROM micro_project m
            LEFT JOIN project_tag_mapping ptm ON m.project_id = ptm.project_id
            LEFT JOIN tag_dictionary t ON ptm.tag_id = t.tag_id
            LEFT JOIN companies c ON m.company_id = c.company_id
            WHERE 1=1 
        """
        params = []

        # 如果使用者有選擇「產業」
        if search_industry:
            sql += " AND c.industry_category = %s"
            params.append(search_industry)

        # 如果使用者有選擇「公司」
        if search_company:
            sql += " AND c.company_id = %s"
            params.append(search_company)

        # 如果使用者有選擇「標籤」(使用子查詢，確保篩選後依然能顯示該專案的"所有"標籤)
        if search_tag:
            sql += " AND m.project_id IN (SELECT project_id FROM project_tag_mapping WHERE tag_id = %s)"
            params.append(search_tag)

        # 最後加上群組與排序，讓最新的任務排在前面
        sql += " GROUP BY m.project_id ORDER BY m.created_at DESC"

        cursor.execute(sql, params)
        raw_projects = cursor.fetchall()

        projects = []
        for p in raw_projects:
            p_list = list(p) 
            if p_list[5]:    
                p_list[5] = p_list[5].split(', ') 
            projects.append(p_list)

    return render(request, 'microproject/microproject_list.html', {
        'projects': projects,
        # 傳遞過濾器選項
        'filter_industries': filter_industries,
        'filter_companies': filter_companies,
        'filter_tags': filter_tags,
        # 傳回目前的搜尋狀態，讓前端下拉選單可以保持在被選取的狀態
        'current_industry': search_industry,
        'current_company': search_company,
        'current_tag': search_tag,
    })


def project_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        company_id = request.POST.get('company_id') # 🚀 接收選單選中的公司 ID
        selected_tags = request.POST.getlist('tags') 
        
        alumni_id = 1 # 暫時寫死

        with connection.cursor() as cursor:
            # 寫入時，存入 company_id
            sql_insert_project = """
                INSERT INTO micro_project (alumni_id, company_id, title, description) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_insert_project, [alumni_id, company_id, title, description])
            
            new_project_id = cursor.lastrowid
            
            if selected_tags:
                sql_insert_tags = "INSERT INTO project_tag_mapping (project_id, tag_id) VALUES (%s, %s)"
                tag_data = [(new_project_id, tag_id) for tag_id in selected_tags]
                cursor.executemany(sql_insert_tags, tag_data)
            
        return redirect('/projects/') 


    # 當使用者剛點進發布頁面時 (GET)
    with connection.cursor() as cursor:
        # 1. 撈出所有標籤給 Checkbox 用
        cursor.execute("SELECT tag_id, tag_name FROM tag_dictionary")
        all_tags = cursor.fetchall()
        
        # 🚀 2. 新增：撈出所有「不重複」的產業類別 (給第一個選單用)
        cursor.execute("SELECT DISTINCT industry_category FROM companies WHERE industry_category IS NOT NULL ORDER BY industry_category")
        industries = [row[0] for row in cursor.fetchall()] # 把結果轉成簡單的 List
        
        # 3. 撈出所有公司給第二個選單用 (我們偷偷把產業別藏在資料裡讓前端 JS 去抓)
        cursor.execute("SELECT company_id, name, industry_category FROM companies ORDER BY name")
        all_companies = cursor.fetchall()
        
    return render(request, 'microproject/microproject_create.html', {
        'tags': all_tags,
        'industries': industries,   # 🚀 記得把產業清單也傳給 HTML
        'companies': all_companies

    })