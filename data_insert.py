import csv
import pymysql

# 1. 資料庫連線設定 (自動對應您 settings.py 的設定)
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'a062271545',
    'database': 'final_project',
    'charset': 'utf8mb4'
}

def import_companies_from_csv(csv_filepath):
    try:
        # 建立資料庫連線
        print("正在連線至資料庫...")
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:

            cursor.execute("DELETE FROM final_project.companies;")

            # 準備 SQL INSERT 語法
            # 這裡使用 ON DUPLICATE KEY UPDATE，如果 company_id 已經存在，就自動更新資料
            sql = """
                INSERT INTO companies (company_id, name, industry, description, location, website, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    name=VALUES(name), 
                    industry=VALUES(industry), 
                    description=VALUES(description), 
                    location=VALUES(location), 
                    website=VALUES(website);
            """
            
            print(f"正在讀取檔案 {csv_filepath} ...")
            # 開啟 CSV 檔案
            with open(csv_filepath, mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                count = 0
                for row in csv_reader:
                    # 將 CSV 欄位對應到 SQL 參數
                    values = (
                        row['company_id'],
                        row['name'],
                        row['industry'],
                        row['description'],
                        row['location'],
                        row['website'],
                        row['created_at']
                    )
                    
                    # 執行插入
                    cursor.execute(sql, values)
                    count += 1
            
            # 提交變更，讓資料正式寫入資料庫
            connection.commit()
            print(f"成功！已成功匯入 / 更新 {count} 筆公司資料。")
            
    except FileNotFoundError:
        print(f"找不到檔案: {csv_filepath}，請確認檔案名稱與路徑是否正確。")
    except pymysql.MySQLError as e:
        print(f"資料庫操作失敗: {e}")
    finally:
        # 確保關閉資料庫連線
        if 'connection' in locals() and connection.open:
            connection.close()
            print("資料庫連線已關閉。")

if __name__ == '__main__':
    # 執行匯入，請確保 CSV 檔名與下方一致
    csv_file_name = 'DBMS_Final_Project/dataset/company.csv' 
    import_companies_from_csv(csv_file_name)