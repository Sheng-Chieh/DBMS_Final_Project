from django.db import models, connection

def dictfetchall(cursor):
    "將游標返回的每一行轉為字典格式"
    if not cursor.description:
        return []
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

# 建立自定義的 Manager 來處理原生 SQL 查詢
class CompanyManager(models.Manager["Company"]):
    
    def search_with_raw_sql(self, query, industry_param, location_param):
        """處理多條件搜尋的 SQL 邏輯"""
        with connection.cursor() as cursor:
            sql = """
                SELECT company_id, name, industry_category, industry_subcategory, description, location_city, location_district, website 
                FROM companies 
                WHERE 1=1
            """
            params = []
            
            # 1. 處理關鍵字條件
            if query:
                sql += " AND (name LIKE %s OR description LIKE %s)"
                params.extend([f"%{query}%", f"%{query}%"])
                
            # 2. 處理多選「產業類型」條件
            if industry_param:
                industries = [i.strip() for i in industry_param.split(',') if i.strip()]
                if industries:
                    industry_conditions = []
                    for ind in industries:
                        if '-' in ind:
                            cat, sub = ind.split('-', 1)
                            industry_conditions.append("(industry_category = %s AND industry_subcategory = %s)")
                            params.extend([cat, sub])
                        else:
                            industry_conditions.append("industry_category = %s")
                            params.append(ind)
                    sql += f" AND ({' OR '.join(industry_conditions)})"
                    
            # 3. 處理多選「地點」條件
            if location_param:
                locations = [loc.strip() for loc in location_param.split(',') if loc.strip()]
                if locations:
                    location_conditions = []
                    for loc in locations:
                        if '-' in loc:
                            city, dist = loc.split('-', 1)
                            location_conditions.append("(location_city = %s AND location_district = %s)")
                            params.extend([city, dist])
                        else:
                            location_conditions.append("location_city = %s")
                            params.append(loc)
                    sql += f" AND ({' OR '.join(location_conditions)})"
                
            cursor.execute(sql, params)
            return dictfetchall(cursor)

    def get_detail_with_raw_sql(self, company_id):
        """處理單一公司詳細資料的 SQL 邏輯"""
        with connection.cursor() as cursor:
            sql = """
                SELECT company_id, name, industry_category, industry_subcategory, description, location_city, location_district, website 
                FROM companies 
                WHERE company_id = %s
            """
            cursor.execute(sql, [company_id])
            row = cursor.fetchone()
            
            if not row:
                return None
                
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return {}

# 建立一個簡單的 Model，並掛載上面的自定義 Manager
class Company(models.Model):
    class Meta:
        db_table = 'companies'  # 對應資料庫實際的資料表名稱
        managed = False         # 由於我們使用原生 SQL，Django 不需要管理這個表的結構

    # 將自定義的 Manager 賦予 objects
    objects: CompanyManager = CompanyManager()