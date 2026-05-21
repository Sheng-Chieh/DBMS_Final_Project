from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from coffeechat_alumni.models import CoffeeChatDatabase
from accounts.views import login_required

@login_required
@csrf_exempt
def apply_chat(request):
    # 測試階段：直接給定一個學生名字 (不使用 ORM 撈 Account)
    fake_student_name = "測試學生_小明" 

    if request.method == 'POST':
        # ====== 1. 從前端 Modal 表單抓出資料 ======
        # 改為抓取時段的 ID，以及學生填寫的內容
        coffee_chat_id = request.POST.get('coffee_chat_id')
        experience_summary = request.POST.get('experience_summary', '未填寫')
        questions_outline = request.POST.get('questions_outline', '未填寫')
        
        # ====== 2. 純 SQL 將資料存進 Application 資料表 ======
        insert_query = """
            INSERT INTO coffee_chat_application 
            (coffee_chat_id, student_name, experience_summary, question_outline, status)
            VALUES (%s, %s, %s, %s, 'pending')
        """
        try:
            CoffeeChatDatabase._execute(
                insert_query, 
                (coffee_chat_id, fake_student_name, experience_summary, questions_outline), 
                commit=True
            )
            # 成功送出後的訊息
            message = '✅ 已成功送出預約申請！追蹤進度請按【我的申請】！'
        except Exception as e:
            message = f'❌ 申請失敗，請稍後再試。錯誤訊息：{str(e)}'

        # ====== 3. 重新撈取所有時段並返回畫面 ======
        context = {
            'timeslots': get_all_published_chats(),
            'message': message
        }
        return render(request, 'coffeechat/apply.html', context)
    
    # ====== GET 請求：撈出所有可預約時段並渲染畫面 ======
    context = {
        'timeslots': get_all_published_chats(),
    }
    return render(request, 'coffeechat/apply.html', context)


@login_required
def my_applications(request):
    fake_student_name = "測試學生_小明"
    
    #撈取該學生的所有申請，並 JOIN 設定表來取得校友名稱與時間
    query = """
        SELECT a.*, c.alumni_name, c.date as chat_date, c.start_time, c.end_time 
        FROM coffee_chat_application a
        JOIN coffee_chat_config c ON a.coffee_chat_id = c.id
        WHERE a.student_name = %s
        ORDER BY a.created_at DESC
    """
    applications = CoffeeChatDatabase._execute(query, (fake_student_name,), fetch=True) or []
    
    # 整理時間格式給前端顯示
    for app in applications:
        start_str = str(app['start_time'])[:5] if app['start_time'] else ''
        end_str = str(app['end_time'])[:5] if app['end_time'] else ''
        date_str = app['chat_date'].strftime("%Y/%m/%d") if app['chat_date'] else ''
        app['scheduled_time'] = f"{date_str} {start_str}-{end_str}"
        
    context = {
        'applications': applications
    }
    return render(request, 'coffeechat/my_applications.html', context)


# --- 輔助函式：撈取所有發布的時段 ---
def get_all_published_chats():
    query = """
        SELECT id, alumni_name, location_type, location_detail, duration, 
               target_departments, date as chat_date, start_time, end_time
        FROM coffee_chat_config
        WHERE is_published = 1
        ORDER BY chat_date ASC, start_time ASC
    """
    raw_timeslots = CoffeeChatDatabase._execute(query, fetch=True) or []
    
    # 整理時間格式，讓前端可以直接印出字串，避免 template 語法錯誤
    for ts in raw_timeslots:
        ts['start_time_str'] = str(ts['start_time'])[:5] if ts['start_time'] else ''
        ts['end_time_str'] = str(ts['end_time'])[:5] if ts['end_time'] else ''
        ts['chat_date_str'] = ts['chat_date'].strftime("%Y/%m/%d") if ts['chat_date'] else ''
        
    return raw_timeslots