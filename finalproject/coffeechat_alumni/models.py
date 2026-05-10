import mysql.connector
from mysql.connector import Error


class CoffeeChatDatabase:

    @staticmethod
    def get_connection():
        try:
            return mysql.connector.connect(
                host='127.0.0.1',
                database='coffee_chat_db',
                user='root',
                password='ericaLEE941028++'
            )
        except Error as e:
            print(f"資料庫連線失敗: {e}")
            return None


    # 共用 SQL 執行方法
    @staticmethod
    def _execute(query, params=None, fetch=False, fetchone=False, commit=False):

        conn = CoffeeChatDatabase.get_connection()
        if not conn:
            return None

        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(query, params or ())

            if commit:
                conn.commit()
                return True

            if fetch:
                return cursor.fetchall()

            if fetchone:
                return cursor.fetchone()

        except Error as e:
            conn.rollback()
            print(f"SQL Error: {e}")
            raise

        finally:
            cursor.close()
            conn.close()


    # 建立 Coffee Chat
    @classmethod
    def create_chat(
        cls, loc_type, loc_detail,
        date, start_time, end_time,
        duration, target_departments,
        resume_match_rate, is_published
    ):

        return cls._execute("""
            INSERT INTO coffee_chat_config
            (location_type, location_detail, date, start_time, end_time,
             duration, target_departments, resume_match_rate, is_published)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            loc_type,
            loc_detail,
            date,
            start_time,
            end_time,
            duration,
            target_departments,
            resume_match_rate,
            is_published
        ), commit=True)


    # 取得單一 chat
    @classmethod
    def get_chat_by_id(cls, chat_id):
        data = cls._execute("""
            SELECT * FROM coffee_chat_config
            WHERE id = %s
        """, (chat_id,), fetchone=True)
        if data:
            if data.get("start_time"):
                data["start_time"] = str(data["start_time"])[:5]

            if data.get("end_time"):
                data["end_time"] = str(data["end_time"])[:5]

        return data


    # 取得全部 chat
    @classmethod
    def get_all_chats(cls):
        return cls._execute("""
            SELECT * FROM coffee_chat_config
            ORDER BY created_at DESC
        """, fetch=True) or []


    # 取得已發布 chat
    @classmethod
    def get_published_chats(cls):
        return cls._execute("""
            SELECT * FROM coffee_chat_config
            WHERE is_published = 1
            ORDER BY created_at DESC
        """, fetch=True) or []


    # 更新 chat
    @staticmethod
    def update_chat(
        chat_id, loc_type, loc_detail,
        date, start_time, end_time,
        duration, target_departments,
        resume_match_rate
    ):

        return CoffeeChatDatabase._execute("""
            UPDATE coffee_chat_config
            SET location_type=%s,
                location_detail=%s,
                date=%s,
                start_time=%s,
                end_time=%s,
                duration=%s,
                target_departments=%s,
                resume_match_rate=%s
            WHERE id=%s
        """, (
            loc_type,
            loc_detail,
            date,
            start_time,
            end_time,
            duration,
            target_departments,
            resume_match_rate,
            chat_id
        ), commit=True)


    # 接受申請者
    @classmethod
    def accept_applicant(cls, applicant_id):
        cls._execute("""
            UPDATE applicant
            SET status='accepted'
            WHERE id=%s
        """, (applicant_id,), commit=True)


    # 取得申請者
    @classmethod
    def get_applicants(cls, chat_id):
        return cls._execute("""
            SELECT * FROM applicant
            WHERE coffee_chat_id = %s
            ORDER BY created_at DESC
        """, (chat_id,), fetch=True) or []
    