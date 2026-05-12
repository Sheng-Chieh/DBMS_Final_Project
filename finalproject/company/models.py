from django.db import models, connection


COMPANY_SELECT_SQL = """
    SELECT company_id, name, industry_category, industry_subcategory, description, description_detail,
           location_city, location_district, website
    FROM companies
"""

def dictfetch(cursor, one=False):
    "將游標結果轉為字典格式；one=True 時只回傳單筆資料"
    if not cursor.description:
        return None if one else []

    columns = [col[0] for col in cursor.description]

    if one:
        row = cursor.fetchone()
        if not row:
            return None
        return dict(zip(columns, row))

    return [dict(zip(columns, row)) for row in cursor.fetchall()]

# 建立自定義的 Manager 來處理原生 SQL 查詢
class CompanyManager(models.Manager["Company"]):

    @staticmethod
    def _split_csv_values(raw_values):
        """把前端傳入的逗號分隔字串拆成乾淨的清單"""
        return [value.strip() for value in (raw_values or "").split(",") if value.strip()]

    @staticmethod
    def _escape_like(value):
        """轉義 LIKE 查詢中會被當成萬用字元的字元"""
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def _build_keyword_clause(self, query):
        """建立關鍵字搜尋條件，避免使用者輸入影響 LIKE 模式"""
        if not query:
            return "", []

        # 先轉義再包成 %keyword% 模式，讓搜尋只比對文字內容
        keyword = self._escape_like(query)
        pattern = f"%{keyword}%"
        clause = "(name LIKE %s OR description LIKE %s OR description_detail LIKE %s)"
        return clause, [pattern, pattern, pattern]

    def _build_choice_clause(self, raw_values, single_field, pair_fields):
        """建立單選或雙欄位組合的多選條件"""
        values = self._split_csv_values(raw_values)
        if not values:
            return "", []

        clauses = []
        params = []

        # 每個值都保持參數化，不直接拼進 SQL 字串
        for value in values:
            if "-" in value:
                first_value, second_value = (part.strip() for part in value.split("-", 1))
                clauses.append(f"({pair_fields[0]} = %s AND {pair_fields[1]} = %s)")
                params.extend([first_value, second_value])
            else:
                clauses.append(f"{single_field} = %s")
                params.append(value)

        return f"({' OR '.join(clauses)})", params
    
    def search_with_raw_sql(self, query, industry_param, location_param):
        """處理多條件搜尋的 SQL 邏輯"""
        with connection.cursor() as cursor:
            # 1. 先放入固定的 SELECT 區塊，避免重複寫欄位清單
            sql = COMPANY_SELECT_SQL
            params = []

            # 2. 用 clauses 暫存每一段條件，最後再用 AND 串起來
            clauses = []

            # 3. 加入關鍵字搜尋條件
            keyword_clause, keyword_params = self._build_keyword_clause(query)
            if keyword_clause:
                clauses.append(keyword_clause)
                params.extend(keyword_params)

            # 4. 加入產業條件：支援單一產業或「分類-子分類」
            industry_clause, industry_params = self._build_choice_clause(
                industry_param,
                "industry_category",
                ("industry_category", "industry_subcategory"),
            )
            if industry_clause:
                clauses.append(industry_clause)
                params.extend(industry_params)

            # 5. 加入地點條件：支援單一城市或「城市-行政區」
            location_clause, location_params = self._build_choice_clause(
                location_param,
                "location_city",
                ("location_city", "location_district"),
            )
            if location_clause:
                clauses.append(location_clause)
                params.extend(location_params)

            # 6. 如果有任何條件，就接到 WHERE 後面；沒有條件就查全部
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)

            # 7. 以參數化方式執行查詢，避免 SQL injection
            cursor.execute(sql, params)
            return dictfetch(cursor)


    def get_detail_with_raw_sql(self, company_id):
        """處理單一公司詳細資料的 SQL 邏輯"""
        with connection.cursor() as cursor:
            # 1. 重用相同的欄位清單，避免列表不一致
            sql = COMPANY_SELECT_SQL + " WHERE company_id = %s"

            # 2. company_id 也透過參數傳入，不直接拼接
            cursor.execute(sql, [company_id])

            # 3. 轉成單筆字典資料，方便 view 和 template 使用
            return dictfetch(cursor, one=True)

# 建立一個簡單的 Model，並掛載上面的自定義 Manager
class Company(models.Model):
    class Meta:
        db_table = 'companies'  # 對應資料庫實際的資料表名稱
        managed = False         # 由於我們使用原生 SQL，Django 不需要管理這個表的結構

    # 將自定義的 Manager 賦予 objects
    objects: CompanyManager = CompanyManager()