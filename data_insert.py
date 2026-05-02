import argparse
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
                description_detail TEXT,
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
            INSERT INTO companies (
                name,
                industry_category,
                industry_subcategory,
                description,
                description_detail,
                location_city,
                location_district,
                website
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            print(f"正在讀取檔案 {csv_filepath} ...")
            with open(csv_filepath, mode='r', encoding='utf-8-sig', newline='') as file:
                csv_reader = csv.DictReader(file)
                
                values_list = []
                for row in csv_reader:
                    # 將 CSV 欄位對應到 SQL 參數
                    values = (
                        row.get('name') or '',
                        row.get('industry_category') or '',
                        row.get('industry_subcategory') or '',
                        row.get('description') or '',
                        row.get('description_detail') or '',
                        row.get('location_city') or '',
                        row.get('location_district') or '',
                        row.get('website') or ''
                    )

                    values_list.append(values)

                # 批次插入
                if values_list:
                    cursor.executemany(sql, values_list)
            
            # 提交變更，讓資料正式寫入資料庫
            connection.commit()
            print(f"成功！已成功匯入 {len(values_list)} 筆公司資料。")
            
    except FileNotFoundError:
        print(f"找不到檔案: {csv_filepath}，請確認檔案名稱與路徑是否正確。")
    except pymysql.MySQLError as e:
        print(f"資料庫操作失敗: {e}")
    finally:
        # 確保關閉資料庫連線
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Import companies CSV into MySQL.")
    parser.add_argument(
        "csv",
        nargs="?",
        default="dataset/company_102_dataset_clean.csv",
        help="CSV path, default: dataset/company_102_dataset_clean.csv",
    )
    args = parser.parse_args()
    import_companies_from_csv(args.csv)