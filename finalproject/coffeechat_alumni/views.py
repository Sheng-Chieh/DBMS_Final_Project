# finalproject/coffeechat_alumni/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpRequest
from .models import CoffeeChatDatabase  
from django.http import JsonResponse
from datetime import datetime, timedelta

def create_coffee_chat(request):

    # 測試階段固定校友名稱
    fake_alumni_name = "測試校友_陳大頭"

    if request.method == "POST":
        try:
            # 1. 接收地點相關資料
            location_type = request.POST.get('location_type')
            if not location_type:
                messages.error(request, "請選擇線上或實體")
                return render(request, 'coffeechat_alumni/create_coffeechat.html')
    
            # 根據線上或實體，抓取對應的輸入內容
            if location_type == 'online':
                location_detail = request.POST.get('online_tool', '').strip()
            elif location_type == 'offline':
                location_detail = request.POST.get('offline_location', '').strip()
            else:
                location_detail = ""

            # 2. 接收時長與門檻條件
            duration_str = request.POST.get('duration')
            duration = int(duration_str) if duration_str and duration_str.isdigit() else 30
            
            target_departments = request.POST.get('target_departments', '').strip()
            
            resume_match_rate_str = request.POST.get('resume_match_rate')
            resume_match_rate = int(resume_match_rate_str) if resume_match_rate_str and resume_match_rate_str.isdigit() else 0

            # 3. 判斷是「儲存草稿」還是「發布」
            # 注意：你在前端的「發布」按鈕目前是 type="button"，請確保前端有加上 name="action" 屬性來區分。
            # 若沒有特別設定，我們先假設送出表單預設為發布 (is_published = True)
            action = request.POST.get('action', 'publish')
            is_published = 1 if action == 'publish' else 0

            # 4. 接收並整理時段資料 (動態新增的部分)
            date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')

            # --- 防呆檢查 ---
            if not location_type or not location_detail:
                messages.error(request, "請完整填寫地點資訊！")
                # 如果有錯，就重新渲染表單頁面
                return render(request, 'coffeechat_alumni/create_coffeechat.html') # 請替換成你實際的 template 路徑
            
            if not date or not start_time or not end_time:
                messages.error(request, "請填寫完整時間")
                return render(request, 'coffeechat_alumni/create_coffeechat.html')
            # 5. 呼叫 models.py 寫入資料庫
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

            # 6. 處理成功後的結果
            if success:
                if is_published == 1:
                    messages.success(request, "Coffee Chat 已成功發布！")
                else:
                    messages.success(request, "Coffee Chat 草稿已儲存！")

                return redirect('create_coffee_chat')
            
        except Exception as e:
            # 捕捉來自 models.py 的錯誤 (例如資料庫連線失敗)
            messages.error(request, f"發生錯誤：{str(e)}")
            return render(request, 'coffeechat_alumni/create_coffeechat.html')

    # 如果不是 POST 請求 (例如使用者剛點進這個網址)，就顯示空白的表單網頁
    return render(request, 'coffeechat_alumni/create_coffeechat.html')

# edit_coffee_chat 的 view
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
            else:
                location_detail = request.POST.get('offline_location', '')

            duration = int(request.POST.get('duration', 30))
            target_departments = request.POST.get('target_departments', '')
            resume_match_rate = int(request.POST.get('resume_match_rate', 0))

            date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')

            CoffeeChatDatabase.update_chat(
                chat_id,
                location_type,
                location_detail,
                date,
                start_time,
                end_time,
                duration,
                target_departments,
                resume_match_rate
            )

            messages.success(request, "更新成功")
            return redirect('edit_coffee_chat', chat_id=chat_id)

        except Exception as e:
            messages.error(request, f"更新失敗：{str(e)}")

    return render(request, 'coffeechat_alumni/edit_coffee_chat.html', {
        'chat': chat
    })

def homepage(request):
    return render(request, 'coffeechat_alumni/homepage.html')

def list_manage_reservation(request):
    chats = CoffeeChatDatabase.get_all_chats()  # 你可能還沒寫
    return render(request, 'coffeechat_alumni/list_manage_reservation.html', {
        'chats': chats
    })

def accept_applicant(request, applicant_id):
    if request.method == "POST":
        CoffeeChatDatabase.accept_applicant(applicant_id)
        messages.success(request, "已接受申請")
        return redirect('list_manage_reservation')
    
def manage_reservation(request, chat_id):
    chat_info = CoffeeChatDatabase.get_chat_by_id(chat_id)
    applicants = CoffeeChatDatabase.get_applicants(chat_id)
    if not chat_info:
        messages.error(request, "找不到這個 Coffee Chat，可能已經被刪除囉！")
        return redirect('list_manage_reservation')
    return render(request, 'coffeechat_alumni/manage_reservation.html', {
        'chat_info': chat_info,
        'applicants': applicants
    })

def toggle_coffee_chat_status(request, chat_id):
    if request.method == "POST":
        conn = CoffeeChatDatabase.get_connection()
        cursor = conn.cursor()

        # 1. 先查目前狀態
        cursor.execute("""
            SELECT is_published FROM coffee_chat_config WHERE id = %s
        """, (chat_id,))
        result = cursor.fetchone()

        current_status = result[0] if result else 0
        new_status = 0 if current_status == 1 else 1

        # 2. 更新
        cursor.execute("""
            UPDATE coffee_chat_config
            SET is_published = %s
            WHERE id = %s
        """, (new_status, chat_id))

        conn.commit()
        cursor.close()
        conn.close()

        return JsonResponse({
            "success": True,
            "new_status": new_status
        })

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
    # 只把 is_published=1 的資料撈出來給學生看
    published_chats = CoffeeChatDatabase.get_published_chats()
    return render(request, 'coffeechat_alumni/student_list.html', {'chats': published_chats})
