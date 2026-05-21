# finalproject/coffeechat_alumni/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import CoffeeChatDatabase 
from datetime import timedelta

def ca_homepage(request):
    return render(request, 'coffeechat_alumni/ca_homepage.html')

def student_coffee_chat_list(request):
    published_chats = CoffeeChatDatabase.get_published_chats()
    return render(request, 'coffeechat_alumni/student_list.html', {'chats': published_chats})

def manage_chats_controller(request):
    action = request.GET.get('action', 'list')
    chat_id = request.GET.get('id') or request.POST.get('id')

    if action == 'create':
        fake_alumni_name = "測試校友_陳大頭"
        if request.method == "POST":
            try:
                location_type = request.POST.get('location_type')
                location_detail = request.POST.get('online_tool', '').strip() if location_type == 'online' else request.POST.get('offline_location', '').strip()
                duration = int(request.POST.get('duration', 30))
                target_departments = request.POST.get('target_departments', '').strip()
                resume_match_rate = int(request.POST.get('resume_match_rate', 0))
                is_published = 1 if request.POST.get('submit_action', 'publish') == 'publish' else 0
                date = request.POST.get('date')
                start_time = request.POST.get('start_time')
                end_time = request.POST.get('end_time')

                if not location_type or not location_detail or not date or not start_time or not end_time:
                    messages.error(request, "請完整填寫資訊！")
                    return render(request, 'coffeechat_alumni/create_coffeechat.html')

                CoffeeChatDatabase.create_chat(
                    alumni_name=fake_alumni_name, loc_type=location_type, loc_detail=location_detail,
                    duration=duration, target_departments=target_departments, resume_match_rate=resume_match_rate,
                    is_published=is_published, date=date, start_time=start_time, end_time=end_time
                )
                messages.success(request, "Coffee Chat 已儲存！")
                return redirect('manage_chats') # 成功後導回列表
            except Exception as e:
                messages.error(request, f"發生錯誤：{str(e)}")
        
        return render(request, 'coffeechat_alumni/create_coffeechat.html')

    elif action == 'edit':
        if request.method == "POST":
            try:
                location_type = request.POST.get('location_type')
                location_detail = request.POST.get('online_tool', '') if location_type == 'online' else request.POST.get('offline_location', '')
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
                return redirect(f"{request.path}?action=edit&id={chat_id}")
            except Exception as e:
                messages.error(request, f"更新失敗：{str(e)}")
        
        chat = CoffeeChatDatabase.get_chat_by_id(chat_id)
        if not chat:
            messages.error(request, "找不到該筆資料")
            return redirect('manage_chats')
        return render(request, 'coffeechat_alumni/edit_coffee_chat.html', {'chat': chat})

    elif action == 'delete' and request.method == "POST":
        conn = CoffeeChatDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM coffee_chat_config WHERE id = %s", (chat_id,))
        conn.commit()
        cursor.close()
        conn.close()
        messages.success(request, "已刪除 Coffee Chat")
        return redirect('manage_chats')

    elif action == 'toggle' and request.method == "POST":
        conn = CoffeeChatDatabase.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_published FROM coffee_chat_config WHERE id = %s", (chat_id,))
        result = cursor.fetchone()
        new_status = 0 if (result and result[0] == 1) else 1
        cursor.execute("UPDATE coffee_chat_config SET is_published = %s WHERE id = %s", (new_status, chat_id))
        conn.commit()
        cursor.close()
        conn.close()
        return JsonResponse({"success": True, "new_status": new_status})

    chats = CoffeeChatDatabase.get_all_chats()
    for chat in chats:
        chat["start_time"] = str(chat["start_time"])[:5]
        chat["end_time"] = str(chat["end_time"])[:5]
    return render(request, 'coffeechat_alumni/list_manage_reservation.html', {'chats': chats})

def manage_applicants_controller(request):
    action = request.GET.get('action', 'view')
    chat_id = request.GET.get('chat_id') or request.POST.get('chat_id')

    if action == 'update_status' and request.method == "POST":
        applicant_id = request.POST.get('applicant_id')
        status_action = request.POST.get('status_action') # 'accept' 或 'reject'
        
        if status_action == 'accept':
            CoffeeChatDatabase.accept_applicant(applicant_id)
            messages.success(request, "已接受申請")
        elif status_action == 'reject':
            CoffeeChatDatabase.reject_applicant(applicant_id)
            messages.success(request, "已婉拒申請")
            
        return redirect(f"{request.path}?action=view&chat_id={chat_id}")

    chat_info = CoffeeChatDatabase.get_chat_by_id(chat_id)
    if not chat_info:
        messages.error(request, "找不到這個 Coffee Chat！")
        return redirect('manage_chats')
        
    applicants = CoffeeChatDatabase.get_applicants(chat_id)
    return render(request, 'coffeechat_alumni/manage_reservation.html', {
        'chat_info': chat_info,
        'applicants': applicants
    })