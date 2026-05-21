from coffeechat_alumni.models import CoffeeChatDatabase

class CoffeeChatStudentDatabase:
    # 建立預約申請單
    @classmethod
    def create_application(cls, coffee_chat_id, student_id, experience_summary, question_outline):
        query = """
            INSERT INTO coffee_chat_application 
            (coffee_chat_id, student_id, experience_summary, question_outline, status)
            VALUES (%s, %s, %s, %s, 'pending')
        """
        return CoffeeChatDatabase._execute(
            query, 
            (coffee_chat_id, student_id, experience_summary, question_outline), 
            commit=True
        )

    # 撈取該學生的所有申請紀錄 (JOIN 校友名字)
    @classmethod
    def get_student_applications(cls, student_id):
        query = """
            SELECT a.*, c.date as chat_date, c.start_time, c.end_time, u.name as alumni_name
            FROM coffee_chat_application a
            JOIN coffee_chat_config c ON a.coffee_chat_id = c.id
            JOIN users u ON c.alumni_id = u.user_id
            WHERE a.student_id = %s
            ORDER BY a.created_at DESC
        """
        return CoffeeChatDatabase._execute(query, (student_id,), fetch=True) or []