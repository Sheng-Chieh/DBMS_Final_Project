import pymysql
from pymysql import MySQLError as Error
from django.conf import settings

class CoffeeChatDatabase:
    @staticmethod
    def get_connection():
        try:
            return pymysql.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=int(settings.DATABASES['default'].get('PORT', 3306))
            )
        except Error as e:
            print(f"資料庫連線失敗: {e}")
            return None

    @staticmethod
    def _execute(query, params=None, fetch=False, fetchone=False, commit=False):
        conn = CoffeeChatDatabase.get_connection()
        if not conn: return None
        cursor = conn.cursor(pymysql.cursors.DictCursor)
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

    #建立時段 (寫入 alumni_id)
    @classmethod
    def create_chat(cls, alumni_id, loc_type, loc_detail, date, start_time, end_time, duration, target_departments, resume_match_rate, is_published):
        query = """
            INSERT INTO coffee_chat_config
            (alumni_id, location_type, location_detail, date, start_time, end_time, 
             duration, target_departments, resume_match_rate, is_published)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return cls._execute(query, (
            alumni_id, loc_type, loc_detail, date, start_time, end_time,
            duration, target_departments, resume_match_rate, is_published
        ), commit=True)
    
    #撈取時 JOIN 校友名字
    @classmethod
    def get_chat_by_id(cls, chat_id):
        query = """
            SELECT c.*, u.name as alumni_name 
            FROM coffee_chat_config c
            JOIN users u ON c.alumni_id = u.user_id
            WHERE c.id = %s
        """
        return cls._execute(query, (chat_id,), fetchone=True)
    
    @classmethod
    def get_all_chats(cls):
        query = """
            SELECT c.*, u.name as alumni_name 
            FROM coffee_chat_config c
            JOIN users u ON c.alumni_id = u.user_id
            ORDER BY c.created_at DESC
        """
        return cls._execute(query, fetch=True) or []
    
    @classmethod
    def get_published_chats(cls):
        query = """
            SELECT c.*, u.name as alumni_name 
            FROM coffee_chat_config c
            JOIN users u ON c.alumni_id = u.user_id
            WHERE c.is_published = 1 
            ORDER BY c.created_at DESC
        """
        return cls._execute(query, fetch=True) or []

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

    @classmethod
    def accept_applicant(cls, applicant_id):
        cls._execute("UPDATE coffee_chat_application SET status='accepted' WHERE id=%s", (applicant_id,), commit=True)

    @classmethod
    def reject_applicant(cls, applicant_id):
        cls._execute("UPDATE coffee_chat_application SET status='rejected' WHERE id=%s", (applicant_id,), commit=True)

    #審核介面：JOIN 學生名字
    @classmethod
    def get_applicants(cls, chat_id):
        query = """
            SELECT a.*, u.name as student_name 
            FROM coffee_chat_application a
            JOIN users u ON a.student_id = u.user_id
            WHERE a.coffee_chat_id = %s 
            ORDER BY a.created_at DESC
        """
        return cls._execute(query, (chat_id,), fetch=True) or []
    
    #只撈取「特定校友」發布的時段
    @classmethod
    def get_chats_by_alumni(cls, alumni_id):
        query = """
            SELECT c.*, u.name as alumni_name 
            FROM coffee_chat_config c
            JOIN users u ON c.alumni_id = u.user_id
            WHERE c.alumni_id = %s
            ORDER BY c.created_at DESC
        """
        return cls._execute(query, (alumni_id,), fetch=True) or []