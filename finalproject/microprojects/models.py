from django.db import models, connection

# 自定義 Manager
class MicroProjectManager(models.Manager):

    def get_filter_options(self):
        """撈取發布頁面與列表頁面所需的下拉選單/標籤資料"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT industry_category FROM companies WHERE industry_category IS NOT NULL ORDER BY industry_category")
            filter_industries = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT company_id, name, industry_category FROM companies ORDER BY name")
            filter_companies = cursor.fetchall()

            cursor.execute("SELECT tag_id, tag_name FROM tag_dictionary ORDER BY tag_category, tag_name")
            filter_tags = cursor.fetchall()
            
        return filter_industries, filter_companies, filter_tags

    def search_projects(self, search_industry, search_company, search_tag):
        """處理列表頁的多條件搜尋 SQL 邏輯"""
        with connection.cursor() as cursor:
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

            if search_industry:
                sql += " AND c.industry_category = %s"
                params.append(search_industry)

            if search_company:
                sql += " AND c.company_id = %s"
                params.append(search_company)

            if search_tag:
                sql += " AND m.project_id IN (SELECT project_id FROM project_tag_mapping WHERE tag_id = %s)"
                params.append(search_tag)

            sql += " GROUP BY m.project_id ORDER BY m.created_at DESC"

            cursor.execute(sql, params)
            raw_projects = cursor.fetchall()

            projects = []
            for p in raw_projects:
                p_list = list(p) 
                if p_list[5]:    
                    p_list[5] = p_list[5].split(', ') 
                projects.append(p_list)
                
            return projects

    def create_project_with_tags(self, alumni_id, company_id, title, description, selected_tags):
        """處理新增微任務與綁定標籤的 SQL 邏輯"""
        with connection.cursor() as cursor:
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

class MicroProject(models.Model):
    class Meta:
        db_table = 'micro_project'
        managed = False  

    objects = MicroProjectManager()