from django.shortcuts import render, redirect
from django.db import connection


def register(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', '').strip()

        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO users (name, email, password, role)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, [name, email, password, role])

            return redirect('login')

        except Exception:
            return render(request, 'accounts/register.html', {
                'error': '註冊失敗，這個 Email 可能已經被使用'
            })

    return render(request, 'accounts/register.html')


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        with connection.cursor() as cursor:
            sql = """
                SELECT user_id, name, email, role
                FROM users
                WHERE email = %s AND password = %s
            """
            cursor.execute(sql, [email, password])
            row = cursor.fetchone()

        if row:
            request.session['user_id'] = row[0]
            request.session['name'] = row[1]
            request.session['email'] = row[2]
            request.session['role'] = row[3]

            return redirect('search_companies')

        return render(request, 'accounts/login.html', {
            'error': 'Email 或密碼錯誤'
        })

    return render(request, 'accounts/login.html')