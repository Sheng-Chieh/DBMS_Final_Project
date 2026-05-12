# finalproject/coffeechat_alumni/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpRequest
from .models import CoffeeChatDatabase  
from django.http import JsonResponse
from datetime import datetime, timedelta

def create_coffee_chat(request):
    fake_alumni_name = "測試校友_陳大頭"
    if request.method == "POST":
        try:
            location_type = request.POST.get('location_type')
            if not location_type:
                messages.error(request, "請選擇線上或實體")
                return render(request, 'coffeechat_alumni/create_coffeechat.html')
            if location_type == 'online':
                location_detail = request.POST.get('online_tool', '').strip()
            elif location_type == 'offline':
                location_detail = request.POST.get('offline_location', '').strip()
            else: location_detail = ""
            duration_str = request.POST.get('duration')
            duration = int(duration_str) if duration_str and duration_str.isdigit() else 30
            target_departments = request.POST.get('target_departments', '').strip()
            resume_match_rate_str = request.POST.get('resume_match_rate')
            resume_match_rate = int(resume_match_rate_str) if resume_match_rate_str and resume_match_rate_str.isdigit() else 0
            action = request.POST.get('action', 'publish')
            is_published = 1 if action == 'publish' else 0
            date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            if not location_type or not location_detail:
                messages.error(request, "請完整填寫地點資訊！")
                return render(request, 'coffeechat_alumni/create_coffeechat.html') 
            if not date or not start_time or not end_time:
                messages.error(request, "請填寫完整時間")
                return render(request, 'coffeechat_alumni/create_coffeechat.html')
            success = CoffeeChatDatabase.create_chat(
                alumni_name=fake_alumni_name,
                loc_type=location_type,
                loc_detail=location_detail,
                duration=duration,
                target_departments=target_departments,
                resume_match_rate=resume_match_rate,
                is_published=is_published,
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            if success:
                if is_published == 1: messages.success(request, "Coffee Chat 已成功發布！")
                else: messages.success(request, "Coffee Chat 草稿已儲存！")
                return redirect('create_coffee_chat')
        except Exception as e:
            messages.error(request, f"發生錯誤：{str(e)}")
            return render(request, 'coffeechat_alumni/create_coffeechat.html')
    return render(request, 'coffeechat_alumni/create_coffeechat.html')

def edit_coffee_chat(request, chat_id):
    chat = CoffeeChatDatabase.get_chat_by_id(chat_id)
    if not chat:
        messages.error(request, "找不到這個 Coffee Chat，無法編輯。")
        return redirect('list_manage_reservation')
    if request.method == "POST":
        try:
            location_type = request.POST.get('location_type')
            if location_type == 'online':
                location_detail = request.POST.get('online_tool', '')
            else: location_detail = request.POST.get('offline_location', '')
            duration = int(request.POST.get('duration', 30))
            target_departments = request.POST.get('target_departments', '')
            resume_match_rate = int(request.POST.get('resume_match_rate', 0))
            date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            CoffeeChatDatabase.update_chat(
                chat_id, location_type, location_detail, date, start_time, end_time,
                duration, target_departments, resume_match_rate
            )
            messages.success(request, "更新成功")
            return redirect('edit_coffee_chat', chat_id=chat_id)
        except Exception as e:
            messages.error(request, f"更新失敗：{str(e)}")
    return render(request, 'coffeechat_alumni/edit_coffee_chat.html', {'chat': chat})

def ca_homepage(request):
    return render(request, 'coffeechat_alumni/ca_homepage.html')

def list_manage_reservation(request):
    chats = CoffeeChatDatabase.get_all_chats() 
    return render(request, 'coffeechat_alumni/list_manage_reservation.html', {'chats': chats})

def accept_applicant(request, applicant_id):
    if request.method == "POST":
        CoffeeChatDatabase.accept_applicant(applicant_id)
        messages.success(request, "已接受申請")
        # 取得申請所在的 chat_id 以便重新導向
        conn = CoffeeChatDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT coffee_chat_id FROM coffee_chat_application WHERE id = %s", (applicant_id,))
        res = cursor.fetchone()
        cursor.close()
        conn.close()
        if res:
            return redirect('manage_reservation', chat_id=res[0])
    return redirect('list_manage_reservation')

# ====== 新增：婉拒申請者 View ======
def reject_applicant(request, applicant_id):
    if request.method == "POST":
        CoffeeChatDatabase.reject_applicant(applicant_id)
        messages.success(request, "已婉拒申請")
        # 取得申請所在的 chat_id 以便重新導向
        conn = CoffeeChatDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT coffee_chat_id FROM coffee_chat_application WHERE id = %s", (applicant_id,))
        res = cursor.fetchone()
        cursor.close()
        conn.close()
        if res:
            return redirect('manage_reservation', chat_id=res[0])
    return redirect('list_manage_reservation')

def manage_reservation(request, chat_id):
    chat_info = CoffeeChatDatabase.get_chat_by_id(chat_id)
    applicants = CoffeeChatDatabase.get_applicants(chat_id)
    if not chat_info:
        messages.error(request, "找不到這個 Coffee Chat，可能已經被刪除囉！")
        return redirect('list_manage_reservation')
        
    # 修正：整理 applicants 時間格式 (timedelta string for template)
    for app in applicants:
        # 如果資料庫存在 created_at (TIMESTAMP)，通常會自動轉換為 Python datetime。
        # 如果是 timedelta，則轉換。這裡假設 models._execute 已經做了初步處理，我們補強格式化。
        if 'scheduled_time' in app and isinstance(app['scheduled_time'], timedelta):
             # 處理可能有 datetime 或 timedelta 的情況，依據需求顯示時間段或單一時間點。
             # 你給的 wireframe 和需求中，manage_reservation.html 沒有顯示申請時間，
             # 但其他代碼有用到。這裡確保不會因為格式出錯。
             pass 

    return render(request, 'coffeechat_alumni/manage_reservation.html', {
        'chat_info': chat_info,
        'applicants': applicants
    })

def toggle_coffee_chat_status(request, chat_id):
    if request.method == "POST":
        conn = CoffeeChatDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_published FROM coffee_chat_config WHERE id = %s", (chat_id,))
        result = cursor.fetchone()
        current_status = result[0] if result else 0
        new_status = 0 if current_status == 1 else 1
        cursor.execute("""
            UPDATE coffee_chat_config SET is_published = %s WHERE id = %s
        """, (new_status, chat_id))
        conn.commit()
        cursor.close()
        conn.close()
        return JsonResponse({"success": True, "new_status": new_status})
    return JsonResponse({"success": False})

def delete_coffee_chat(request, chat_id):
    if request.method == "POST":
        conn = CoffeeChatDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM coffee_chat_config WHERE id = %s", (chat_id,))
        conn.commit()
        cursor.close()
        conn.close()
        messages.success(request, "已刪除 Coffee Chat")
        return redirect('list_manage_reservation')

def student_coffee_chat_list(request):
    published_chats = CoffeeChatDatabase.get_published_chats()
    return render(request, 'coffeechat_alumni/student_list.html', {'chats': published_chats})