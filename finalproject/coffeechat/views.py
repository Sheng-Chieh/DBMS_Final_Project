from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from accounts.views import login_required
from coffeechat_alumni.models import CoffeeChatDatabase
from .models import CoffeeChatStudentDatabase

@login_required
@csrf_exempt
def apply_chat(request):
    #權限控管：如果不是學生，直接踢回首頁
    if request.session.get('role') != 'student':
        return redirect('homepage_logged_in')

    student_id = request.session.get('user_id') 

    if request.method == 'POST':
        coffee_chat_id = request.POST.get('coffee_chat_id')
        experience_summary = request.POST.get('experience_summary', '未填寫')
        questions_outline = request.POST.get('questions_outline', '未填寫')
        
        try:
            #呼叫學生端 Model，不碰 SQL
            CoffeeChatStudentDatabase.create_application(
                coffee_chat_id, student_id, experience_summary, questions_outline
            )
            message = '已成功送出預約申請！追蹤進度請按【我的申請】！'
        except Exception as e:
            message = f'申請失敗，請稍後再試。錯誤訊息：{str(e)}'

        context = {
            'timeslots': get_all_published_chats(),
            'message': message
        }
        return render(request, 'coffeechat/apply.html', context)
    
    context = {'timeslots': get_all_published_chats()}
    return render(request, 'coffeechat/apply.html', context)

@login_required
def my_applications(request):
    #權限控管：如果不是學生，直接踢回首頁
    if request.session.get('role') != 'student':
        return redirect('homepage_logged_in')

    student_id = request.session.get('user_id')
    
    #呼叫學生端 Model，撈出該學生專屬的申請
    applications = CoffeeChatStudentDatabase.get_student_applications(student_id)
    
    for app in applications:
        start_str = str(app['start_time'])[:5] if app['start_time'] else ''
        end_str = str(app['end_time'])[:5] if app['end_time'] else ''
        date_str = app['chat_date'].strftime("%Y/%m/%d") if app['chat_date'] else ''
        app['scheduled_time'] = f"{date_str} {start_str}-{end_str}"
        
    return render(request, 'coffeechat/my_applications.html', {'applications': applications})

def get_all_published_chats():
    # 呼叫校友端 Model 拿取大廳資料 (已自動 JOIN 校友名字)
    raw_timeslots = CoffeeChatDatabase.get_published_chats()
    
    for ts in raw_timeslots:
        ts['start_time_str'] = str(ts['start_time'])[:5] if ts['start_time'] else ''
        ts['end_time_str'] = str(ts['end_time'])[:5] if ts['end_time'] else ''
        
        ts['chat_date_str'] = ts['date'].strftime("%Y/%m/%d") if ts.get('date') else ''
        
    return raw_timeslots