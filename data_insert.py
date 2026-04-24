import csv
import pymysql

# 1. 資料庫連線設定 (請確保與您 settings.py 的設定一致)
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '0000',
    'database': 'final_project',
    'charset': 'utf8mb4'
}

def import_companies_from_csv(csv_filepath):
    try:
        # 建立資料庫連線
        print("連線至資料庫...")
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            print("重建 companies 資料表以確保欄位結構正確...")
            cursor.execute("DROP TABLE IF EXISTS companies;")
            create_table_sql = """
            CREATE TABLE companies (
                company_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                industry_category VARCHAR(50),
                industry_subcategory VARCHAR(50),
                description TEXT,
                location_city VARCHAR(50),
                location_district VARCHAR(50),
                website VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_table_sql)
            print("companies 資料表已重建完成。")

            print("準備匯入新資料...")

            # 準備 SQL INSERT 語法
            sql = """
            INSERT INTO companies (name, industry_category, industry_subcategory, description, location_city, location_district, website)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name=VALUES(name),
                industry_category=VALUES(industry_category),
                industry_subcategory=VALUES(industry_subcategory),
                description=VALUES(description),
                location_city=VALUES(location_city),
                location_district=VALUES(location_district),
                website=VALUES(website);
            """
            
            print(f"正在讀取檔案 {csv_filepath} ...")
            with open(csv_filepath, mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                count = 0
                for row in csv_reader:
                    # 將 CSV 欄位對應到 SQL 參數
                    values = (
                        row['name'],
                        row['industry_category'],
                        row['industry_subcategory'],
                        row['description'],
                        row['location_city'],
                        row['location_district'],
                        row['website']
                    )
                    
                    # 執行插入
                    cursor.execute(sql, values)
                    count += 1
            
            # 提交變更，讓資料正式寫入資料庫
            connection.commit()
            print(f"成功！已成功匯入 {count} 筆擁有完整分類（產業、地區）的公司資料。")
            
    except FileNotFoundError:
        print(f"找不到檔案: {csv_filepath}，請確認檔案名稱與路徑是否正確。")
    except pymysql.MySQLError as e:
        print(f"資料庫操作失敗: {e}")
    finally:
        # 確保關閉資料庫連線
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == '__main__':
    import_companies_from_csv('company.csv')