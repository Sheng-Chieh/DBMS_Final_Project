import pymysql

# 1. 資料庫連線設定 (與你同學的設定一致)
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '0000',
    'database': 'final_project',
    'charset': 'utf8mb4'
}

def seed_database():
    try:
        print("連線至資料庫...")
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            # ==========================================
            # 階段一：清除舊表與建立新表 (DDL)
            # ==========================================
            print("關閉外鍵檢查並重建微任務相關資料表...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            
            cursor.execute("DROP TABLE IF EXISTS project_tag_mapping;")
            cursor.execute("DROP TABLE IF EXISTS micro_project;")
            cursor.execute("DROP TABLE IF EXISTS tag_dictionary;")
            
            create_tables_sql = """
            CREATE TABLE tag_dictionary (
                tag_id INT AUTO_INCREMENT PRIMARY KEY,
                tag_name VARCHAR(50) NOT NULL UNIQUE COMMENT '標籤名稱',
                tag_category VARCHAR(50) NOT NULL COMMENT '標籤分類'
            );

            CREATE TABLE micro_project (
                project_id INT AUTO_INCREMENT PRIMARY KEY,
                alumni_id INT NOT NULL COMMENT '發布專案的校友ID',
                title VARCHAR(100) NOT NULL COMMENT '專案名稱',
                description TEXT NOT NULL COMMENT '專案詳細內容與需求',
                industry VARCHAR(50) NOT NULL COMMENT '產業類別',
                status ENUM('Active', 'Draft', 'Cancelled', 'Completed') DEFAULT 'Active' COMMENT '專案狀態',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );

            CREATE TABLE project_tag_mapping (
                project_id INT NOT NULL,
                tag_id INT NOT NULL,
                PRIMARY KEY (project_id, tag_id),
                FOREIGN KEY (project_id) REFERENCES micro_project(project_id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tag_dictionary(tag_id) ON DELETE CASCADE
            );
            """
            # pymysql 預設一次執行單一語法，若要執行多行字串，需要切割或分次執行
            # 這裡我們將字串以 ';' 切割後逐一執行
            for statement in create_tables_sql.split(';'):
                if statement.strip():
                    cursor.execute(statement)
            
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            print("資料表重建完成。")

            # ==========================================
            # 階段二：塞入測試用假資料 (DML)
            # ==========================================
            print("準備匯入測試資料...")

            # 1. 寫入標籤字典
            tags = [
                ('Python', 'Skill'),
                ('SQL', 'Skill'),
                ('商業分析', 'Domain'),
                ('行銷企劃', 'Domain')
            ]
            cursor.executemany(
                "INSERT INTO tag_dictionary (tag_name, tag_category) VALUES (%s, %s)", 
                tags
            )

            # 2. 寫入微任務主表
            projects = [
                (101, '社群趨勢洞察報告', '需要具備社群行銷認知與基礎數據撈取能力，協助分析競品粉專近三個月的互動成效。', '科技業', 'Active'),
                (102, '銷售數據儀表板製作', '利用 SQL 撈取既有銷售資料，並製作視覺化儀表板供業務團隊參考。', '零售業', 'Active'),
                (103, '校園品牌大使招募企劃', '協助發想針對大學生的品牌推廣活動，並撰寫企劃書。', 'FMCG', 'Active')
            ]
            cursor.executemany(
                "INSERT INTO micro_project (alumni_id, title, description, industry, status) VALUES (%s, %s, %s, %s, %s)", 
                projects
            )

            # 3. 寫入任務與標籤的關聯表 (對應上面的 ID)
            # 專案1 綁定 行銷企劃(4)
            # 專案2 綁定 SQL(2), 商業分析(3)
            # 專案3 綁定 行銷企劃(4)
            mappings = [
                (1, 4), 
                (2, 2), 
                (2, 3),
                (3, 4)
            ]
            cursor.executemany(
                "INSERT INTO project_tag_mapping (project_id, tag_id) VALUES (%s, %s)", 
                mappings
            )
            
            # 提交變更，讓資料正式寫入資料庫
            connection.commit()
            print("成功！已成功匯入微任務相關的三張表與測試資料。")
            
    except pymysql.MySQLError as e:
        print(f"資料庫操作失敗: {e}")
    finally:
        # 確保關閉資料庫連線
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == '__main__':
    seed_database()