import os
import csv
import pymysql
from dotenv import load_dotenv

# 1. 載入 .env 檔案中的環境變數
load_dotenv()

# 2. 從環境變數讀取資料庫連線資訊
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'autocommit': False
}

# 按照依賴順序定義要建置的資料表定義
# 按照依賴順序定義要建置的資料表定義
TABLES_SCHEMA = {
    "companies": """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "departments": """
        CREATE TABLE departments (
            department_id INT AUTO_INCREMENT PRIMARY KEY,
            department_name VARCHAR(100) NOT NULL UNIQUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "users": """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "activities": """
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
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "work_experiences": """
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
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "course_records": """
        CREATE TABLE course_records (
            course_record_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            course_name VARCHAR(100) NOT NULL,
            semester VARCHAR(50),
            grade VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "course_tags": """
        CREATE TABLE course_tags (
            tag_id INT AUTO_INCREMENT PRIMARY KEY,
            tag_name VARCHAR(50) NOT NULL UNIQUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "course_record_tags": """
        CREATE TABLE course_record_tags (
            course_record_id INT NOT NULL,
            tag_id INT NOT NULL,
            PRIMARY KEY (course_record_id, tag_id),
            FOREIGN KEY (course_record_id) REFERENCES course_records(course_record_id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES course_tags(tag_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "coffee_chat_config": """
        CREATE TABLE coffee_chat_config (
            id INT NOT NULL AUTO_INCREMENT,
            alumni_id INT NOT NULL COMMENT '發布校友的 user_id',
            location_type ENUM('online','offline') NOT NULL,
            location_detail VARCHAR(255) DEFAULT NULL,
            date DATE NOT NULL COMMENT '對談日期',
            start_time TIME NOT NULL COMMENT '開始時間',
            end_time TIME NOT NULL COMMENT '結束時間',
            duration INT NOT NULL COMMENT '對談時長(分鐘)',
            target_departments VARCHAR(255) DEFAULT NULL,
            resume_match_rate INT DEFAULT '0',
            is_published TINYINT(1) DEFAULT '0' COMMENT '0=儲存, 1=發布',
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            FOREIGN KEY (alumni_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "coffee_chat_application": """
        CREATE TABLE coffee_chat_application (
            id INT NOT NULL AUTO_INCREMENT,
            coffee_chat_id INT NOT NULL COMMENT '對應的 Coffee Chat ID',
            student_id INT NOT NULL COMMENT '申請學生的 user_id',
            experience_summary TEXT,
            question_outline TEXT,
            status VARCHAR(20) DEFAULT 'pending' COMMENT '狀態: pending/accepted/rejected',
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            FOREIGN KEY (coffee_chat_id) REFERENCES coffee_chat_config(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "tag_dictionary": """
        CREATE TABLE tag_dictionary (
            tag_id INT AUTO_INCREMENT PRIMARY KEY,
            tag_name VARCHAR(50) NOT NULL UNIQUE COMMENT '標籤名稱'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "micro_project": """
        CREATE TABLE micro_project (
            project_id INT AUTO_INCREMENT PRIMARY KEY,
            alumni_id INT NOT NULL COMMENT '發布專案的校友ID',
            company_id INT COMMENT '關聯公司ID',
            title VARCHAR(100) NOT NULL COMMENT '專案名稱',
            description TEXT NOT NULL COMMENT '專案詳細內容與需求',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (alumni_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "project_tag_mapping": """
        CREATE TABLE project_tag_mapping (
            project_id INT NOT NULL,
            tag_id INT NOT NULL,
            PRIMARY KEY (project_id, tag_id),
            FOREIGN KEY (project_id) REFERENCES micro_project(project_id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tag_dictionary(tag_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
}


# CSV 假資料匯入封裝 Class
class CSVImporter:
    
    def __init__(self, dataset_dir="dataset"):
        self.dataset_dir = dataset_dir

    def _clean_int(self, val):
        """實例內部的清理工具：將字串安全轉為 int 或 None"""
        if not val or val.strip() == "" or val.upper() == "NAN":
            return None
        try:
            return int(float(val.strip()))
        except:
            return None

    def _clean_str(self, val):
        """實例內部的清理工具：將字串前後去空白，若為空則回傳 None"""
        if val is None:
            return None
        s = val.strip()
        return s if s != "" else None

    def _get_path(self, filename):
        """獲取 CSV 檔案的完整相對路徑"""
        return os.path.join(self.dataset_dir, filename)

    def insert_companies(self, cursor):
        path = self._get_path("company.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                if not row.get('name') or not row.get('name').strip(): continue
                data.append((
                    row.get('name').strip(), self._clean_str(row.get('industry_category')),
                    self._clean_str(row.get('industry_subcategory')), self._clean_str(row.get('description')),
                    self._clean_str(row.get('description_detail')), self._clean_str(row.get('location_city')),
                    self._clean_str(row.get('location_district')), self._clean_str(row.get('website'))
                ))
        if data:
            sql = """INSERT INTO companies (name, industry_category, industry_subcategory, description, description_detail, location_city, location_district, website) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.executemany(sql, data)
            print(f"  [OK] companies 成功匯入 {len(data)} 筆資料。")
        return True

    def insert_departments(self, cursor):
        path = self._get_path("departments.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = [(row.get('department_name').strip(),) for row in reader if row.get('department_name')]
        if data:
            sql = "INSERT INTO departments (department_name) VALUES (%s)"
            cursor.executemany(sql, data)
            print(f"  [OK] departments 成功匯入 {len(data)} 筆資料。")
        return True

    def insert_users(self, cursor):
        path = self._get_path("users.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                if not row.get('name') or not row.get('email'): continue
                data.append((
                    row.get('role', 'student').strip(), row.get('name').strip(),
                    row.get('email').strip(), row.get('password', '123456').strip(),
                    self._clean_int(row.get('department_id')), self._clean_int(row.get('enrollment_year')),
                    self._clean_int(row.get('graduation_year')), self._clean_int(row.get('company_id')),
                    self._clean_str(row.get('current_job_title')),
                    self._clean_int(row.get('is_profile_completed')) if row.get('is_profile_completed') else 0
                ))
        if data:
            sql = """INSERT INTO users (role, name, email, password, department_id, enrollment_year, graduation_year, company_id, current_job_title, is_profile_completed) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.executemany(sql, data)
            print(f"  [OK] users 成功匯入 {len(data)} 筆資料。")
        return True

    def insert_activities(self, cursor):
        path = self._get_path("activities.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                if not row.get('user_id') or not row.get('title'): continue
                data.append((
                    self._clean_int(row.get('user_id')), row.get('category', '其他').strip(),
                    row.get('title').strip(), self._clean_str(row.get('role')),
                    self._clean_str(row.get('start_date')), self._clean_str(row.get('end_date')),
                    self._clean_str(row.get('description'))
                ))
        if data:
            sql = """INSERT INTO activities (user_id, category, title, role, start_date, end_date, description) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.executemany(sql, data)
            print(f"  [OK] activities 成功匯入 {len(data)} 筆資料。")
        return True

    def insert_work_experiences(self, cursor):
        path = self._get_path("work_experiences.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                if not row.get('user_id') or not row.get('company_id'): continue
                data.append((
                    self._clean_int(row.get('user_id')), self._clean_int(row.get('company_id')),
                    row.get('job_type', '其他').strip(), self._clean_str(row.get('job_title')),
                    self._clean_str(row.get('start_date')), self._clean_str(row.get('end_date')),
                    self._clean_str(row.get('description'))
                ))
        if data:
            sql = """INSERT INTO work_experiences (user_id, company_id, job_type, job_title, start_date, end_date, description) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.executemany(sql, data)
            print(f"  [OK] work_experiences 成功匯入 {len(data)} 筆資料。")
        return True

    def insert_course_records(self, cursor):
        path = self._get_path("course_records.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                if not row.get('user_id') or not row.get('course_name'): continue
                data.append((
                    self._clean_int(row.get('user_id')), row.get('course_name').strip(),
                    self._clean_str(row.get('semester')), self._clean_str(row.get('grade'))
                ))
        if data:
            sql = "INSERT INTO course_records (user_id, course_name, semester, grade) VALUES (%s, %s, %s, %s)"
            cursor.executemany(sql, data)
            print(f"  [OK] course_records 成功匯入 {len(data)} 筆資料。")
        return True

    def insert_course_tags(self, cursor):
        path = self._get_path("course_tags.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                if not row.get('tag_name'): continue
                data.append((self._clean_int(row.get('tag_id')), row.get('tag_name').strip()))
        if data:
            sql = "INSERT INTO course_tags (tag_id, tag_name) VALUES (%s, %s)"
            cursor.executemany(sql, data)
            print(f"  [OK] course_tags 成功匯入 {len(data)} 筆資料。")
        return True

    def insert_course_record_tags(self, cursor):
        path = self._get_path("course_record_tags.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                pid = self._clean_int(row.get('course_record_id'))
                tid = self._clean_int(row.get('tag_id'))
                if pid and tid: data.append((pid, tid))
        if data:
            sql = "INSERT INTO course_record_tags (course_record_id, tag_id) VALUES (%s, %s)"
            cursor.executemany(sql, data)
            print(f"  [OK] course_record_tags 成功匯入 {len(data)} 筆資料。")
        return True
    
    def insert_tag_dictionary(self, cursor):
        path = self._get_path("tag_dictionary.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                # 1. 這裡只檢查 tag_name，徹底移除 tag_category 的檢查
                if not row.get('tag_name'): continue
                
                data.append((
                    self._clean_int(row.get('tag_id')),
                    row.get('tag_name').strip()
                ))
                
        if data:
            # 如果 CSV 內有提供 tag_id 則帶入，否則讓資料庫自增
            if data[0][0] is not None:
                sql = "INSERT INTO tag_dictionary (tag_id, tag_name) VALUES (%s, %s)"
            else:
                # 2. 這裡的 SQL 徹底拿掉 tag_category
                sql = "INSERT INTO tag_dictionary (tag_name) VALUES (%s)"
                # 3. 這裡只抓 r[1] (也就是 tag_name)，注意單一元素的 tuple 需要加逗號
                data = [(r[1],) for r in data]
                
            cursor.executemany(sql, data)
            print(f"  [OK] tag_dictionary 成功匯入 {len(data)} 筆資料。")
        return True


    def insert_micro_project(self, cursor):
        path = self._get_path("micro_project.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                if not row.get('alumni_id') or not row.get('title') or not row.get('description'): continue
                data.append((
                    self._clean_int(row.get('project_id')),
                    self._clean_int(row.get('alumni_id')),
                    self._clean_int(row.get('company_id')),
                    row.get('title').strip(),
                    row.get('description').strip()
                ))
        if data:
            if data[0][0] is not None:
                sql = "INSERT INTO micro_project (project_id, alumni_id, company_id, title, description) VALUES (%s, %s, %s, %s, %s)"
            else:
                sql = "INSERT INTO micro_project (alumni_id, company_id, title, description) VALUES (%s, %s, %s, %s)"
                data = [(r[1], r[2], r[3], r[4]) for r in data]
            cursor.executemany(sql, data)
            print(f"  [OK] micro_project 成功匯入 {len(data)} 筆資料。")
        return True

    def insert_project_tag_mapping(self, cursor):
        path = self._get_path("project_tag_mapping.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                pid = self._clean_int(row.get('project_id'))
                tid = self._clean_int(row.get('tag_id'))
                if pid and tid: data.append((pid, tid))
        if data:
            sql = "INSERT INTO project_tag_mapping (project_id, tag_id) VALUES (%s, %s)"
            cursor.executemany(sql, data)
            print(f"  [OK] project_tag_mapping 成功匯入 {len(data)} 筆資料。")
        return True
    
    def insert_coffee_chat_config(self, cursor):
        path = self._get_path("coffee_chat_config.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                if not row.get('alumni_id'): continue
                data.append((
                    self._clean_int(row.get('id')),
                    self._clean_int(row.get('alumni_id')),
                    row.get('location_type').strip(),
                    self._clean_str(row.get('location_detail')),
                    self._clean_str(row.get('date')),
                    self._clean_str(row.get('start_time')),
                    self._clean_str(row.get('end_time')),
                    self._clean_int(row.get('duration')),
                    self._clean_str(row.get('target_departments')),
                    self._clean_int(row.get('resume_match_rate')),
                    self._clean_int(row.get('is_published'))
                ))
        if data:
            if data[0][0] is not None:
                sql = """INSERT INTO coffee_chat_config 
                         (id, alumni_id, location_type, location_detail, date, start_time, end_time, duration, target_departments, resume_match_rate, is_published) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            else:
                sql = """INSERT INTO coffee_chat_config 
                         (alumni_id, location_type, location_detail, date, start_time, end_time, duration, target_departments, resume_match_rate, is_published) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                data = [(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10]) for r in data]
            cursor.executemany(sql, data)
            print(f"  [OK] coffee_chat_config 成功匯入 {len(data)} 筆資料。")
        return True

    def insert_coffee_chat_application(self, cursor):
        path = self._get_path("coffee_chat_application.csv")
        if not os.path.exists(path): return False
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                if not row.get('student_id'): continue
                data.append((
                    self._clean_int(row.get('id')),
                    self._clean_int(row.get('coffee_chat_id')),
                    self._clean_int(row.get('student_id')),
                    self._clean_str(row.get('experience_summary')),
                    self._clean_str(row.get('question_outline')),
                    row.get('status', 'pending').strip()
                ))
        if data:
            if data[0][0] is not None:
                sql = """INSERT INTO coffee_chat_application 
                         (id, coffee_chat_id, student_id, experience_summary, question_outline, status) 
                         VALUES (%s, %s, %s, %s, %s, %s)"""
            else:
                sql = """INSERT INTO coffee_chat_application 
                         (coffee_chat_id, student_id, experience_summary, question_outline, status) 
                         VALUES (%s, %s, %s, %s, %s)"""
                data = [(r[1], r[2], r[3], r[4], r[5]) for r in data]
            cursor.executemany(sql, data)
            print(f"  [OK] coffee_chat_application 成功匯入 {len(data)} 筆資料。")
        return True

    def insert_all(self, cursor):
        """一鍵全部匯入方法 (嚴格依照外鍵順序)"""
        self.insert_companies(cursor)
        self.insert_departments(cursor)
        self.insert_users(cursor)
        self.insert_activities(cursor)
        self.insert_work_experiences(cursor)
        self.insert_course_records(cursor)
        self.insert_course_tags(cursor)
        self.insert_course_record_tags(cursor)
        self.insert_tag_dictionary(cursor)
        self.insert_micro_project(cursor)
        self.insert_project_tag_mapping(cursor)
        self.insert_coffee_chat_config(cursor)
        self.insert_coffee_chat_application(cursor)

# 資料表清空管理類別
class DataTruncator:

    def _truncate(self, cursor, table_name):
        """內部的通用清空工具"""
        cursor.execute(f"TRUNCATE TABLE `{table_name}`;")
        print(f"  [Clean] 已清空資料表資料: {table_name}")
        return True

    def clear_companies(self, cursor):
        return self._truncate(cursor, "companies")

    def clear_departments(self, cursor):
        return self._truncate(cursor, "departments")

    def clear_users(self, cursor):
        return self._truncate(cursor, "users")

    def clear_activities(self, cursor):
        return self._truncate(cursor, "activities")

    def clear_work_experiences(self, cursor):
        return self._truncate(cursor, "work_experiences")

    def clear_course_records(self, cursor):
        return self._truncate(cursor, "course_records")

    def clear_course_tags(self, cursor):
        return self._truncate(cursor, "course_tags")

    def clear_course_record_tags(self, cursor):
        return self._truncate(cursor, "course_record_tags")

    def clear_coffee_chat_config(self, cursor):
        return self._truncate(cursor, "coffee_chat_config")

    def clear_coffee_chat_application(self, cursor):
        return self._truncate(cursor, "coffee_chat_application")
    
    def clear_tag_dictionary(self, cursor):
        return self._truncate(cursor, "tag_dictionary")

    def clear_micro_project(self, cursor):
        return self._truncate(cursor, "micro_project")

    def clear_project_tag_mapping(self, cursor):
        return self._truncate(cursor, "project_tag_mapping")

    def clear_all(self, cursor):
        """一鍵全部清空方法 (嚴格依照外鍵反向順序避免衝突)"""
        print("  正在執行全量清空作業...")
        tables_to_clear = [
            "project_tag_mapping", "micro_project", "tag_dictionary",
            "coffee_chat_application", "coffee_chat_config", 
            "course_record_tags", "course_tags", "course_records", 
            "work_experiences", "activities", "users", 
            "departments", "companies"
        ]
        for table in tables_to_clear:
            self._truncate(cursor, table)
        return True

# 資料表建置與中央調度控制
def create_tables():
    connection = None
    try:
        print(f"正在連線至 MySQL 資料庫 ({db_config['host']}:{db_config['port']})...")
        connection = pymysql.connect(**db_config)
        
        with connection.cursor() as cursor:
            print("連線成功！開始準備資料表...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            for table_name in TABLES_SCHEMA.keys():
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
                print(f"已清理資料表 (如果存在): {table_name}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            print("----------------------------------------")

            for table_name, create_query in TABLES_SCHEMA.items():
                cursor.execute(create_query)
                print(f"資料表建置成功: {table_name}")

            connection.commit()
            print("----------------------------------------")
            print("所有資料表重新建置完成！")
    except Exception as e:
        print(f"資料庫操作失敗，原因: {e}")
        if connection: connection.rollback()
    finally:
        if connection: connection.close()


def execute(target_method_name=None, func_name="全部資料"):
    """中央事務調度：動態識別並呼叫 CSVImporter 或 DataTruncator 內的方法"""
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            print(f"\n開始執行【{func_name}】作業...")
            
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            
            if target_method_name:
                # 💡 判斷：如果是 clear_ 開頭，就實例化 DataTruncator；否則使用 CSVImporter
                if target_method_name.startswith("clear_"):
                    executor = DataTruncator()
                else:
                    executor = CSVImporter(dataset_dir="dataset")
                
                method = getattr(executor, target_method_name)
                success = method(cursor)
                if not success:
                    print("執行對應操作時失敗。")
            else:
                # 若完全沒傳方法名稱，預設為 CSV 的全量匯入
                importer = CSVImporter(dataset_dir="dataset")
                importer.insert_all(cursor)
                
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            connection.commit()
            print(f"【{func_name}】作業成功，已將變更儲存至資料庫！")
    except Exception as e:
        print(f"執行中途發生錯誤: {e}")
        if connection:
            connection.rollback()
            print("已自動執行交易回滾（Rollback）。")
    finally:
        if connection: connection.close()



# 使用者互動選單
def import_submenu():
    sub_menu = (
        "\n-------------------------------------------------------------\n"
        "                      資料庫假資料管理                      \n"
        "-------------------------------------------------------------\n"
        " 【單表資料操作】                【單表清空操作 (不刪結構)】 \n"
        " [1]  匯入 companies             [1c] 清空 companies\n"
        " [2]  匯入 departments           [2c] 清空 departments\n"
        " [3]  匯入 users                 [3c] 清空 users\n"
        " [4]  匯入 activities            [4c] 清空 activities\n"
        " [5]  匯入 work_experiences      [5c] 清空 work_experiences\n"
        " [6]  匯入 course_records        [6c] 清空 course_records\n"
        " [7]  匯入 course_tags           [7c] 清空 course_tags\n"
        " [8]  匯入 course_record_tags    [8c] 清空 course_record_tags\n"
        " [9]  匯入 tag_dictionary        [9c] 清空 tag_dictionary\n"
        " [10] 匯入 micro_project         [10c]清空 micro_project\n"
        " [11] 匯入 project_tag_mapping   [11c]清空 project_tag_mapping\n"
        " [12] 匯入 coffee_chat_config    [12c]清空 coffee_chat_config\n"
        " [13] 匯入 coffee_chat_app...    [13c]清空 coffee_chat_application\n"
        "-------------------------------------------------------------\n"
        " [A]  一鍵全部匯入 (所有 CSV 檔案)\n"
        " [C]  一鍵清空所有資料表資料 (保留結構)\n"
        " [B]  返回主選單\n"
        "-------------------------------------------------------------\n"
    )
    
    mapping = {
        # 匯入部分
        "1": ("insert_companies", "匯入 companies"),
        "2": ("insert_departments", "匯入 departments"),
        "3": ("insert_users", "匯入 users"),
        "4": ("insert_activities", "匯入 activities"),
        "5": ("insert_work_experiences", "匯入 work_experiences"),
        "6": ("insert_course_records", "匯入 course_records"),
        "7": ("insert_course_tags", "匯入 course_tags"),
        "8": ("insert_course_record_tags", "匯入 course_record_tags"),
        "9": ("insert_tag_dictionary", "匯入 tag_dictionary"),
        "10": ("insert_micro_project", "匯入 micro_project"),
        "11": ("insert_project_tag_mapping", "匯入 project_tag_mapping"),
        "12": ("insert_coffee_chat_config", "匯入 coffee_chat_config"),
        "13": ("insert_coffee_chat_application", "匯入 coffee_chat_application"),
        # 清空部分
        "1c": ("clear_companies", "清空 companies"),
        "2c": ("clear_departments", "清空 departments"),
        "3c": ("clear_users", "清空 users"),
        "4c": ("clear_activities", "清空 activities"),
        "5c": ("clear_work_experiences", "清空 work_experiences"),
        "6c": ("clear_course_records", "清空 course_records"),
        "7c": ("clear_course_tags", "清空 course_tags"),
        "8c": ("clear_course_record_tags", "清空 course_record_tags"),
        "9c": ("clear_tag_dictionary", "清空 tag_dictionary"),
        "10c": ("clear_micro_project", "清空 micro_project"),
        "11c": ("clear_project_tag_mapping", "清空 project_tag_mapping"),
        "12c": ("clear_coffee_chat_config", "清空 coffee_chat_config"),
        "13c": ("clear_coffee_chat_application", "清空 coffee_chat_application")
    }
    
    while True:
        print(sub_menu)
        choice = input("請輸入操作指令: ").strip().lower()
        if choice in mapping:
            method_name, show_name = mapping[choice]
            execute(target_method_name=method_name, func_name=show_name)
        elif choice == "a":
            execute(target_method_name=None, func_name="全量 CSV 匯入")
        elif choice == "c":
            confirm = input("確定要一鍵清空所有資料表嗎？(y/n): ").strip().lower()
            if confirm == 'y':
                execute(target_method_name="clear_all", func_name="全量清空資料")
            else:
                print("操作已取消。")
        elif choice == "b":
            print("已回到主選單。")
            break
        else:
            print("輸入無效，請重新選擇。")

def user_selected():
    menu = (
        "\n=============================\n"
        "      資料庫管理工具選單     \n"
        "=============================\n"
        "[1] 重新建置所有資料表 (會清空舊資料)\n"
        "[2] 進入假資料匯入專區\n"
        "[exit] 離開程式\n"
        "-----------------------------\n"
    )
    
    while True:
        print(menu)
        user_input = input("請輸入操作代號: ").strip().lower()
        
        if user_input == "1":
            confirm = input("這將刪除現有資料表並清空資料，確定嗎？(y/n): ").strip().lower()
            if confirm == 'y':
                create_tables()
            else:
                print("操作已取消。")
        elif user_input == "2":
            import_submenu()
        elif user_input == "exit":
            print("程式已關閉。")
            break
        else:
            print("輸入無效，請輸入 1、2 或 exit。")

if __name__ == "__main__":
    user_selected()