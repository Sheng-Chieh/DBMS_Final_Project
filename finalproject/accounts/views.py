from django.shortcuts import render, redirect
from .models import Account


def register(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', '').strip()

        try:
            Account.objects.create_user_with_raw_sql(name, email, password, role)
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

        user = Account.objects.login_with_raw_sql(email, password)

        if user:
            request.session['user_id'] = user['user_id']
            request.session['name'] = user['name']
            request.session['email'] = user['email']
            request.session['role'] = user['role']

            return redirect('search_companies')

        return render(request, 'accounts/login.html', {
            'error': 'Email 或密碼錯誤'
        })

    return render(request, 'accounts/login.html')