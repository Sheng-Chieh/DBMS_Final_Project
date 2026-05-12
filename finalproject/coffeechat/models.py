from django.shortcuts import render, redirect
from django.http import HttpResponse
# 抓coffeechat_alumni 的class
from coffeechat_alumni.models import CoffeeChatDatabase
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def apply_chat(request):
    fake_student_name = "測試學生_王小明" # 測試用的學生名字

    if request.method == 'POST':
        # 1. 抓取前端傳來的資料 (包含隱藏的 coffee_chat_id)
        coffee_chat_id = request.POST.get('coffee_chat_id')
        experience_summary = request.POST.get('experience_summary', '')
        questions_outline = request.POST.get('questions_outline', '')

        # 2. 🌟 純 SQL 寫入資料 (INSERT)
        insert_query = """
            INSERT INTO coffee_chat_application 
            (coffee_chat_id, student_name, experience_summary, question_outline, status)
            VALUES (%s, %s, %s, %s, 'pending')
        """
        CoffeeChatDatabase._execute(
            insert_query, 
            (coffee_chat_id, fake_student_name, experience_summary, questions_outline), 
            commit=True
        )
        
        # 3. 重新撈取時段，並帶上成功訊息
        context = {
            'timeslots': get_all_published_chats(),
            'message': '✅ 已成功送出預約申請！'
        }
        return render(request, 'coffeechat/apply.html', context)
    
    # GET 請求：顯示大廳
    context = {
        'timeslots': get_all_published_chats(),
    }
    return render(request, 'coffeechat/apply.html', context)


def my_applications(request):
    fake_student_name = "測試學生_王小明"

    query = """
        SELECT a.*, c.alumni_name, c.date as chat_date, c.start_time, c.end_time 
        FROM coffee_chat_application a
        JOIN coffee_chat_config c ON a.coffee_chat_id = c.id
        WHERE a.student_name = %s
        ORDER BY a.created_at DESC
    """
    applications = CoffeeChatDatabase._execute(query, (fake_student_name,), fetch=True) or []

    # 整理時間格式給前端
    for app in applications:
        start_str = str(app['start_time'])[:5]
        end_str = str(app['end_time'])[:5]
        date_str = app['chat_date'].strftime("%Y/%m/%d")
        app['scheduled_time'] = f"{date_str} {start_str}-{end_str}"

    context = {
        'applications': applications
    }
    return render(request, 'coffeechat/my_applications.html', context)


# --- 輔助小函式：撈取所有發布的時段 ---
def get_all_published_chats():
    # 🌟 純 SQL 撈取設定檔 (SELECT)
    query = """
        SELECT id, alumni_name, location_type, location_detail, duration, 
               target_departments, date as chat_date, start_time, end_time
        FROM coffee_chat_config
        WHERE is_published = 1
        ORDER BY chat_date ASC, start_time ASC
    """
    raw_timeslots = CoffeeChatDatabase._execute(query, fetch=True) or []

    # 整理時間格式，讓前端不會報錯
    for ts in raw_timeslots:
        ts['start_time_str'] = str(ts['start_time'])[:5] # 把 14:00:00 變成 14:00
        ts['end_time_str'] = str(ts['end_time'])[:5]
        ts['chat_date_str'] = ts['chat_date'].strftime("%Y/%m/%d")
    return raw_timeslots