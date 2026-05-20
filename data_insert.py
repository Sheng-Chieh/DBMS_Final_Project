import argparse
import csv
import pymysql

# 資料庫連線設定
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '215864',
    'database': 'final_project',
    'charset': 'utf8mb4'
}


def import_companies_from_csv(csv_filepath):
    try:
        # 建立資料庫連線
        print("連線至資料庫...")
        connection = pymysql.connect(**DB_CONFIG)

        with connection.cursor() as cursor:

            # 清空 companies 資料
            print("清空 companies 資料...")

            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute("DELETE FROM companies;")
            cursor.execute("ALTER TABLE companies AUTO_INCREMENT = 1;")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            print("準備匯入新資料...")

            # SQL INSERT 語法
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

            # 提交變更
            connection.commit()

            print(f"成功！已成功匯入 {len(values_list)} 筆公司資料。")

    except FileNotFoundError:
        print(f"找不到檔案: {csv_filepath}，請確認檔案名稱與路徑是否正確。")

    except pymysql.MySQLError as e:
        print(f"資料庫操作失敗: {e}")

    finally:
        # 關閉資料庫連線
        if 'connection' in locals() and connection.open:
            connection.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Import companies CSV into MySQL."
    )

    parser.add_argument(
        "csv",
        nargs="?",
        default="dataset/company_102_dataset_clean.csv",
        help="CSV path, default: dataset/company_102_dataset_clean.csv",
    )

    args = parser.parse_args()

    import_companies_from_csv(args.csv)