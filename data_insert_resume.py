import argparse
import csv
import pymysql

# 1. 資料庫連線設定（請確保與 settings.py 的設定一致）
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '215864',
    'database': 'final_project',
    'charset': 'utf8mb4'
}


def import_resume_data():
    try:
        print("連線至資料庫...")
        connection = pymysql.connect(**DB_CONFIG)

        with connection.cursor() as cursor:
            print("重建履歷相關資料表...")

            # 注意：因為其他表會依賴 users，所以刪除順序要先刪子表
            cursor.execute("DROP TABLE IF EXISTS course_record_tags;")
            cursor.execute("DROP TABLE IF EXISTS course_tags;")
            cursor.execute("DROP TABLE IF EXISTS course_records;")
            cursor.execute("DROP TABLE IF EXISTS work_experiences;")
            cursor.execute("DROP TABLE IF EXISTS activities;")
            cursor.execute("DROP TABLE IF EXISTS users;")
            cursor.execute("DROP TABLE IF EXISTS departments;")

            create_departments_sql = """
            CREATE TABLE departments (
                department_id INT AUTO_INCREMENT PRIMARY KEY,
                department_name VARCHAR(100) NOT NULL UNIQUE
            );
            """

            create_users_sql = """
            CREATE TABLE users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                role ENUM('student', 'alumni') NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,

                department_id INT,
                enrollment_year INT,
                graduation_year INT,

                company_id INT,
                current_job_title VARCHAR(100),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_profile_completed BOOLEAN DEFAULT FALSE,

                FOREIGN KEY (department_id) REFERENCES departments(department_id),
                FOREIGN KEY (company_id) REFERENCES companies(company_id)
            );
            """

            create_activities_sql = """
            CREATE TABLE activities (
                activity_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                category ENUM('社團', '競賽', '專案', '研究', '志工', '活動籌辦', '學生組織', '其他') NOT NULL,
                title VARCHAR(100) NOT NULL,
                role VARCHAR(100),
                start_date DATE,
                end_date DATE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                ON DELETE CASCADE
            );
            """

            create_work_sql = """
            CREATE TABLE work_experiences (
                work_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                company_id INT NOT NULL,
                job_type ENUM('實習', '全職', '兼職', '工讀', '自由接案', '其他'),
                job_title VARCHAR(100),
                start_date DATE,
                end_date DATE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                ON DELETE CASCADE,
                FOREIGN KEY (company_id) REFERENCES companies(company_id)
                ON DELETE CASCADE
            );
            """

            create_course_sql = """
            CREATE TABLE course_records (
                course_record_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                course_name VARCHAR(100) NOT NULL,
                semester VARCHAR(50),
                grade VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                ON DELETE CASCADE
            );
            """

            create_course_tags_sql = """
            CREATE TABLE course_tags (
                tag_id INT AUTO_INCREMENT PRIMARY KEY,
                tag_name VARCHAR(50) NOT NULL UNIQUE
            );
            """
            create_course_record_tags_sql = """
            CREATE TABLE course_record_tags (
                course_record_id INT NOT NULL,
                tag_id INT NOT NULL,
                PRIMARY KEY (course_record_id, tag_id),
                FOREIGN KEY (course_record_id) REFERENCES course_records(course_record_id)
                ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES course_tags(tag_id)
                ON DELETE CASCADE
            );
            """
            cursor.execute(create_departments_sql)
            cursor.execute(create_users_sql)
            cursor.execute(create_activities_sql)
            cursor.execute(create_work_sql)
            cursor.execute(create_course_sql)
            cursor.execute(create_course_tags_sql)
            cursor.execute(create_course_record_tags_sql)
            print("履歷相關資料表已重建完成。")

            import_departments(cursor, "dataset/departments.csv")
            import_users(cursor, "dataset/users.csv")
            import_activities(cursor, "dataset/activities.csv")
            import_work_experiences(cursor, "dataset/work_experiences.csv")
            import_course_records(cursor, "dataset/course_records.csv")
            import_course_tags(cursor, "dataset/course_tags.csv")
            import_course_record_tags(cursor, "dataset/course_record_tags.csv")

        connection.commit()
        print("成功！已完成履歷假資料匯入。")

    except FileNotFoundError as e:
        print(f"找不到檔案：{e.filename}，請確認檔案名稱與路徑是否正確。")
    except pymysql.MySQLError as e:
        print(f"資料庫操作失敗：{e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()


def empty_to_none(value):
    if value is None:
        return None
    value = value.strip()
    if value == "" or value.upper() == "NULL":
        return None
    return value

def import_departments(cursor, csv_filepath):
    print(f"正在讀取檔案 {csv_filepath} ...")

    sql = """
    INSERT INTO departments (
        department_name
    )
    VALUES (%s)
    """

    with open(csv_filepath, mode='r', encoding='utf-8-sig', newline='') as file:
        csv_reader = csv.DictReader(file)

        values_list = []
        for row in csv_reader:
            values = (
                row.get('department_name') or '',
            )
            values_list.append(values)

        if values_list:
            cursor.executemany(sql, values_list)

    print(f"departments 匯入完成，共 {len(values_list)} 筆。")

def import_users(cursor, csv_filepath):
    print(f"正在讀取檔案 {csv_filepath} ...")

    sql = """
    INSERT INTO users (
        name,
        email,
        password,
        role,
        department_id,
        enrollment_year,
        graduation_year,
        current_job_title,
        company_id,
        is_profile_completed
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    with open(csv_filepath, mode='r', encoding='utf-8-sig', newline='') as file:
        csv_reader = csv.DictReader(file)

        values_list = []
        for row in csv_reader:
            values = (
                row.get('name') or '',
                row.get('email') or '',
                row.get('password') or '',
                row.get('role') or '',
                empty_to_none(row.get('department_id')),
                empty_to_none(row.get('enrollment_year')),
                empty_to_none(row.get('graduation_year')),
                empty_to_none(row.get('current_job_title')),
                empty_to_none(row.get('company_id')),
                row.get('is_profile_completed') or 0
            )
            values_list.append(values)

        if values_list:
            cursor.executemany(sql, values_list)

    print(f"users 匯入完成，共 {len(values_list)} 筆。")


def import_activities(cursor, csv_filepath):
    print(f"正在讀取檔案 {csv_filepath} ...")

    sql = """
    INSERT INTO activities (
        user_id,
        category,
        title,
        role,
        start_date,
        end_date,
        description
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    with open(csv_filepath, mode='r', encoding='utf-8-sig', newline='') as file:
        csv_reader = csv.DictReader(file)

        values_list = []
        for row in csv_reader:
            values = (
                row.get('user_id'),
                row.get('category') or '',
                row.get('title') or '',
                row.get('role') or '',
                empty_to_none(row.get('start_date')),
                empty_to_none(row.get('end_date')),
                row.get('description') or ''
            )
            values_list.append(values)

        if values_list:
            cursor.executemany(sql, values_list)

    print(f"activities 匯入完成，共 {len(values_list)} 筆。")


def import_work_experiences(cursor, csv_filepath):
    print(f"正在讀取檔案 {csv_filepath} ...")

    sql = """
    INSERT INTO work_experiences (
        user_id,
        company_id,
        job_type,
        job_title,
        start_date,
        end_date,
        description
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    with open(csv_filepath, mode='r', encoding='utf-8-sig', newline='') as file:
        csv_reader = csv.DictReader(file)

        values_list = []
        for row in csv_reader:
            values = (
                row.get('user_id'),
                row.get('company_id') or '',
                row.get('job_type') or '',
                row.get('job_title') or '',
                empty_to_none(row.get('start_date')),
                empty_to_none(row.get('end_date')),
                row.get('description') or ''
            )
            values_list.append(values)

        if values_list:
            cursor.executemany(sql, values_list)

    print(f"work_experiences 匯入完成，共 {len(values_list)} 筆。")


def import_course_records(cursor, csv_filepath):
    print(f"正在讀取檔案 {csv_filepath} ...")

    sql = """
    INSERT INTO course_records (
        user_id,
        course_name,
        semester,
        grade
    )
    VALUES (%s, %s, %s, %s)
    """

    with open(csv_filepath, mode='r', encoding='utf-8-sig', newline='') as file:
        csv_reader = csv.DictReader(file)

        values_list = []
        for row in csv_reader:
            values = (
                row.get('user_id'),
                row.get('course_name') or '',
                row.get('semester') or '',
                row.get('grade') or ''
            )
            values_list.append(values)

        if values_list:
            cursor.executemany(sql, values_list)

    print(f"course_records 匯入完成，共 {len(values_list)} 筆。")

def import_course_tags(cursor, csv_filepath):
    print(f"正在讀取檔案 {csv_filepath} ...")

    sql = """
    INSERT INTO course_tags (
        tag_name
    )
    VALUES (%s)
    """

    with open(csv_filepath, mode='r', encoding='utf-8-sig', newline='') as file:
        csv_reader = csv.DictReader(file)

        values_list = []

        for row in csv_reader:
            values = (
                row.get('tag_name') or '',
            )
            values_list.append(values)

        if values_list:
            cursor.executemany(sql, values_list)

    print(f"course_tags 匯入完成，共 {len(values_list)} 筆。")

def import_course_record_tags(cursor, csv_filepath):
    print(f"正在讀取檔案 {csv_filepath} ...")

    sql = """
    INSERT INTO course_record_tags (
        course_record_id,
        tag_id
    )
    VALUES (%s, %s)
    """

    with open(csv_filepath, mode='r', encoding='utf-8-sig', newline='') as file:
        csv_reader = csv.DictReader(file)

        values_list = []

        for row in csv_reader:
            values = (
                row.get('course_record_id'),
                row.get('tag_id')
            )
            values_list.append(values)

        if values_list:
            cursor.executemany(sql, values_list)

    print(f"course_record_tags 匯入完成，共 {len(values_list)} 筆。")


if __name__ == '__main__':
    import_resume_data()