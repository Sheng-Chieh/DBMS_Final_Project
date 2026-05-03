from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import CoffeeChatApplication
from accounts.models import Account
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def apply_chat(request):
    # 學生是自己登入的狀態(id=1), 想預約的校友(id=2)
    fake_student_id = 1
    fake_alumni_id = 2
    fake_reserved_time = "2026/05/20 14:00-15:00"

    if request.method == 'POST':
        # ====== 1. 從請求(Request)中抓出前端輸入的資料 ======
        experience_summary = request.POST.get('experience_summary', '未填寫')
        questions_outline = request.POST.get('questions_outline', '未填寫')
        
        try:
            student = Account.objects.get(id=fake_student_id)
        except Account.DoesNotExist:
            return HttpResponse(f"請先確保你在資料庫 `users` 有 id={fake_student_id} 的假帳號資料！")
            
        try:
            alumni = Account.objects.get(id=fake_alumni_id)
        except Account.DoesNotExist:
            return HttpResponse(f"請先確保你在資料庫 `users` 有 id={fake_alumni_id} 的假帳號資料！")

        # ====== 3. 將資料存進資料庫 (相當於 INSERT INTO) ======
        CoffeeChatApplication.objects.create(
            student_name=getattr(student, 'name', f'學生_{fake_student_id}'),
            alumni_name=getattr(alumni, 'name', f'校友_{fake_alumni_id}'),
            scheduled_time=fake_reserved_time,
            experience_summary=experience_summary,
            question_outline=questions_outline,
            status='pending' # 預設是待確認
        )
        
        # ====== 4. 送出後返回原頁面並帶上成功訊息 ======
        context = {
            'alumni_name': getattr(alumni, 'name', '測試校友'),
            'reserved_time': fake_reserved_time,
            'message': '✅ 預約申請已成功送出！請去 TablePlus 檢查！'
        }
        return render(request, 'coffeechat/apply.html', context)
    
    # ====== GET 請求：只負責把裝有 Modal 的畫面渲染出來 ======
    context = {
        'alumni_name': '測試校友 (王大明)',
        'reserved_time': fake_reserved_time,
    }
    return render(request, 'coffeechat/apply.html', context)