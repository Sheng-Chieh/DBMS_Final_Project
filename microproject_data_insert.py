import os
import csv
import pymysql

# 1. 資料庫連線設定
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '215864',
    'database': 'final_project',
    'charset': 'utf8mb4'
}

def reset_and_import_database():
    # 自動抓取目前的資料夾路徑，並指向 dataset 資料夾
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tag_csv = os.path.join(base_dir, 'dataset', 'tag_dictionary.csv')
    project_csv = os.path.join(base_dir, 'dataset', 'micro_project.csv')
    mapping_csv = os.path.join(base_dir, 'dataset', 'project_tag_mapping.csv')

    try:
        print("連線至資料庫...")
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            # ==========================================
            # 階段一：清除舊表與建立最新架構的表 (DDL)
            # ==========================================
            print("關閉外鍵檢查並重建微任務相關資料表 (已更新為最新 company_id 架構)...")
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
                company_id INT COMMENT '關聯公司ID',
                title VARCHAR(100) NOT NULL COMMENT '專案名稱',
                description TEXT NOT NULL COMMENT '專案詳細內容與需求',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE SET NULL
            );

            CREATE TABLE project_tag_mapping (
                project_id INT NOT NULL,
                tag_id INT NOT NULL,
                PRIMARY KEY (project_id, tag_id),
                FOREIGN KEY (project_id) REFERENCES micro_project(project_id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tag_dictionary(tag_id) ON DELETE CASCADE
            );
            """
            for statement in create_tables_sql.split(';'):
                if statement.strip():
                    cursor.execute(statement)
            
            print("資料表重建完成。")

            # ==========================================
            # 階段二：從 CSV 讀取並塞入資料 (DML)
            # ==========================================
            print("準備從 dataset 資料夾匯入 CSV 備份資料...")

            # 1. 匯入標籤字典
            if os.path.exists(tag_csv):
                print(f"正在讀取 {tag_csv} ...")
                with open(tag_csv, mode='r', encoding='utf-8-sig', newline='') as file:
                    reader = csv.DictReader(file)
                    tag_data = [(row['tag_id'], row['tag_name'], row['tag_category']) for row in reader]
                if tag_data:
                    cursor.executemany("INSERT INTO tag_dictionary (tag_id, tag_name, tag_category) VALUES (%s, %s, %s)", tag_data)
                    print(f"成功匯入 {len(tag_data)} 筆標籤字典資料！")
            else:
                print(f"找不到 {tag_csv}，跳過匯入。")

            # 2. 匯入微任務主表
            if os.path.exists(project_csv):
                print(f"正在讀取 {project_csv} ...")
                with open(project_csv, mode='r', encoding='utf-8-sig', newline='') as file:
                    reader = csv.DictReader(file)
                    project_data = []
                    for row in reader:
                        # 處理 CSV 匯出時可能出現的字串 'NULL' 或空白
                        company_id = row.get('company_id')
                        if not company_id or company_id.strip().upper() == 'NULL':
                            company_id = None
                        project_data.append((row['project_id'], row['alumni_id'], company_id, row['title'], row['description']))
                if project_data:
                    sql_project = """
                    INSERT INTO micro_project (project_id, alumni_id, company_id, title, description) 
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.executemany(sql_project, project_data)
                    print(f"成功匯入 {len(project_data)} 筆微任務主檔！")
            else:
                print(f"找不到 {project_csv}，跳過匯入。")

            # 3. 匯入任務與標籤的關聯表
            if os.path.exists(mapping_csv):
                print(f"正在讀取 {mapping_csv} ...")
                with open(mapping_csv, mode='r', encoding='utf-8-sig', newline='') as file:
                    reader = csv.DictReader(file)
                    mapping_data = [(row['project_id'], row['tag_id']) for row in reader]
                if mapping_data:
                    cursor.executemany("INSERT INTO project_tag_mapping (project_id, tag_id) VALUES (%s, %s)", mapping_data)
                    print(f"成功匯入 {len(mapping_data)} 筆標籤關聯資料！")
            else:
                print(f"找不到 {mapping_csv}，跳過匯入。")
            
            # 把外鍵檢查開回來
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            connection.commit()
            print("恭喜！所有資料庫結構與 CSV 備份資料已完美還原。")
            
    except pymysql.MySQLError as e:
        print(f"資料庫操作失敗: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == '__main__':
    reset_and_import_database()