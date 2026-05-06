from django.shortcuts import render
from django.http import HttpResponse
from .models import CoffeeChatApplication, CoffeeChatConfiguration, CoffeeChatTime
from accounts.models import Account
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def apply_chat(request):
    # 學生依然是自己登入的狀態(id=1)
    fake_student_id = 1 

    if request.method == 'POST':
        # ====== 1. 從前端 Modal 表單抓出資料 ======
        # 這裡我們改成抓取隱藏欄位傳過來的真實校友和時段字串
        alumni_name = request.POST.get('alumni_name', '未知校友')
        scheduled_time = request.POST.get('scheduled_time', '未知時段')
        experience_summary = request.POST.get('experience_summary', '未填寫')
        questions_outline = request.POST.get('questions_outline', '未填寫')
        
        try:
            student = Account.objects.get(id=fake_student_id)
        except Account.DoesNotExist:
            return HttpResponse(f"請先確保你在資料庫 `users` 有 id={fake_student_id} 的假帳號資料！")

        # ====== 2. 將資料存進 Application 資料表 ======
        CoffeeChatApplication.objects.create(
            student_name=getattr(student, 'name', f'學生_{fake_student_id}'),
            alumni_name=alumni_name,        # 直接存入前端傳來的校友名字
            scheduled_time=scheduled_time,  # 直接存入前端傳來的預約時段
            experience_summary=experience_summary,
            question_outline=questions_outline,
            status='待確認'
        )
        
        # ====== 3. 送出後返回原頁面並帶上成功訊息 ======
        # 重新撈取所有時段供畫面渲染
        all_timeslots = CoffeeChatTime.objects.select_related('coffee_chat').all()
        context = {
            'timeslots': all_timeslots,
            'message': f'✅ 已成功向【{alumni_name}】送出預約申請！追蹤進度請按【我的申請】！'
        }
        return render(request, 'coffeechat/apply.html', context)
    
    # ====== GET 請求：撈出所有可預約時段並渲染畫面 ======
    # 使用 select_related('coffee_chat') 可以把 Time 表和 Configuration 表關聯起來一起撈出
    all_timeslots = CoffeeChatTime.objects.select_related('coffee_chat').all()
    
    context = {
        'timeslots': all_timeslots,
    }
    return render(request, 'coffeechat/apply.html', context)

def my_applications(request):
    # 測試階段：我們先把資料庫裡所有的申請單都撈出來
    # order_by('-created_at') 代表依照建立時間「反向(最新)」排序
    applications = CoffeeChatApplication.objects.all().order_by('-created_at')
    
    context = {
        'applications': applications
    }
    return render(request, 'coffeechat/my_applications.html', context)