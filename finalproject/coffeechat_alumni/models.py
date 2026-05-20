import mysql.connector # 到時候讀取資料庫設定要改
from mysql.connector import Error
from django.conf import settings

class CoffeeChatDatabase:
    @staticmethod
    def get_connection():
        try:
            return mysql.connector.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default'].get('PORT', 3306)
            )
        except Error as e:
            print(f"資料庫連線失敗: {e}")
            return None

    @staticmethod
    def _execute(query, params=None, fetch=False, fetchone=False, commit=False):
        conn = CoffeeChatDatabase.get_connection()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            if commit:
                conn.commit()
                return True
            if fetch: return cursor.fetchall()
            if fetchone: return cursor.fetchone()
        except Error as e:
            conn.rollback()
            print(f"SQL Error: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    # 建立時段
    @classmethod
    def create_chat(cls, alumni_name, loc_type, loc_detail, date, start_time, end_time, duration, target_departments, resume_match_rate, is_published):
        query = """
            INSERT INTO coffee_chat_config
            (alumni_name, location_type, location_detail, date, start_time, end_time, 
             duration, target_departments, resume_match_rate, is_published)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return cls._execute(query, (
            alumni_name, loc_type, loc_detail, date, start_time, end_time,
            duration, target_departments, resume_match_rate, is_published
        ), commit=True)

    @classmethod
    def get_chat_by_id(cls, chat_id):
        return cls._execute("SELECT * FROM coffee_chat_config WHERE id = %s", (chat_id,), fetchone=True)

    @classmethod
    def get_all_chats(cls):
        return cls._execute("SELECT * FROM coffee_chat_config ORDER BY created_at DESC", fetch=True) or []

    @classmethod
    def get_published_chats(cls):
        return cls._execute("SELECT * FROM coffee_chat_config WHERE is_published = 1 ORDER BY created_at DESC", fetch=True) or []

    # 更新時段
    @staticmethod
    def update_chat(chat_id, loc_type, loc_detail, date, start_time, end_time, duration, target_departments, resume_match_rate):
        query = """
            UPDATE coffee_chat_config
            SET location_type=%s, location_detail=%s, date=%s, start_time=%s, 
                end_time=%s, duration=%s, target_departments=%s, resume_match_rate=%s
            WHERE id=%s
        """
        return CoffeeChatDatabase._execute(query, (
            loc_type, loc_detail, date, start_time, end_time,
            duration, target_departments, resume_match_rate, chat_id
        ), commit=True)

    # 接受申請者 (修正資料表名稱為 coffee_chat_application)
    @classmethod
    def accept_applicant(cls, applicant_id):
        cls._execute("UPDATE coffee_chat_application SET status='accepted' WHERE id=%s", (applicant_id,), commit=True)

    # ====== 新增：婉拒申請者 ======
    @classmethod
    def reject_applicant(cls, applicant_id):
        cls._execute("UPDATE coffee_chat_application SET status='rejected' WHERE id=%s", (applicant_id,), commit=True)

    # 取得申請者 (修正資料表名稱為 coffee_chat_application)
    @classmethod
    def get_applicants(cls, chat_id):
        return cls._execute("SELECT * FROM coffee_chat_application WHERE coffee_chat_id = %s ORDER BY created_at DESC", (chat_id,), fetch=True) or []