from functools import wraps
from datetime import datetime

from django.shortcuts import render, redirect

from .models import Account, Activity, WorkExperience, CourseRecord, Company, Department


# ===================== Helper =====================

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_year_options():
    current_year = datetime.now().year

    return {
        'enrollment_years': range(current_year - 10, current_year + 1),
        'graduation_years': range(current_year - 10, current_year + 8)
    }


def get_user_id(request):
    return request.session.get('user_id')


# ===================== Auth =====================

def register(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', '').strip()

        try:
            user_id = Account.objects.create_user_with_raw_sql(
                name, email, password, role
            )

            request.session['user_id'] = user_id
            request.session['name'] = name
            request.session['email'] = email
            request.session['role'] = role
            request.session['is_profile_completed'] = 0

            return redirect('onboarding')

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
            request.session['is_profile_completed'] = user['is_profile_completed']

            if user['is_profile_completed'] == 0:
                return redirect('onboarding')

            return redirect('resume')

        return render(request, 'accounts/login.html', {
            'error': 'Email 或密碼錯誤'
        })

    return render(request, 'accounts/login.html')


def logout(request):
    request.session.flush()
    return redirect('login')


# ===================== Resume =====================

@login_required
def resume(request):
    user_id = get_user_id(request)

    user = Account.objects.get_user_by_id(user_id)
    activities = Activity.objects.get_user_activities(user_id)
    works = WorkExperience.objects.get_user_work_experiences(user_id)
    courses = CourseRecord.objects.get_user_courses(user_id)

    companies = Company.objects.get_all_companies()
    departments = Department.objects.get_all_departments()

    return render(request, 'accounts/resume.html', {
        'user': user,
        'activities': activities,
        'works': works,
        'courses': courses,
        'companies': companies,
        'departments': departments,
        'year_options': get_year_options(),
    })


@login_required
def update_profile(request):
    if request.method == 'POST':
        user_id = get_user_id(request)
        role = request.session.get('role')

        department_id = request.POST.get('department_id') or None
        enrollment_year = request.POST.get('enrollment_year') or None
        graduation_year = request.POST.get('graduation_year') or None
        company_id = request.POST.get('company_id') or None
        current_job_title = request.POST.get('current_job_title') or None

        if role == 'student':
            company_id = None
            current_job_title = None

        Account.objects.update_profile(
            user_id,
            department_id,
            enrollment_year,
            graduation_year,
            company_id,
            current_job_title
        )

    return redirect('resume')


# ===================== Activity CRUD =====================

@login_required
def add_activity(request):
    if request.method == 'POST':
        Activity.objects.add_activity(
            get_user_id(request),
            request.POST.get('category'),
            request.POST.get('title'),
            request.POST.get('role'),
            request.POST.get('start_date') or None,
            request.POST.get('end_date') or None,
            request.POST.get('description')
        )

        return redirect('resume')

    return render(request, 'accounts/add_activity.html', {
    'today': datetime.now().date().isoformat()
})


@login_required
def update_activity(request, activity_id):
    if request.method == 'POST':
        Activity.objects.update_activity(
            activity_id,
            get_user_id(request),
            request.POST.get('category'),
            request.POST.get('title'),
            request.POST.get('role'),
            request.POST.get('start_date') or None,
            request.POST.get('end_date') or None,
            request.POST.get('description')
        )

    return redirect('resume')


@login_required
def delete_activity(request, activity_id):
    Activity.objects.delete_activity(
        activity_id,
        get_user_id(request)
    )

    return redirect('resume')


# ===================== Work Experience CRUD =====================

@login_required
def add_work(request):
    companies = Company.objects.get_all_companies()

    if request.method == 'POST':
        WorkExperience.objects.add_work(
            get_user_id(request),
            request.POST.get('company_id') or None,
            request.POST.get('job_type'),
            request.POST.get('job_title'),
            request.POST.get('start_date') or None,
            request.POST.get('end_date') or None,
            request.POST.get('description')
        )

        return redirect('resume')

    return render(request, 'accounts/add_work.html', {
        'companies': companies,
        'today': datetime.now().date().isoformat()
    })


@login_required
def update_work(request, work_id):
    if request.method == 'POST':
        WorkExperience.objects.update_work(
            work_id,
            get_user_id(request),
            request.POST.get('company_id') or None,
            request.POST.get('job_type'),
            request.POST.get('job_title'),
            request.POST.get('start_date') or None,
            request.POST.get('end_date') or None,
            request.POST.get('description')
        )

    return redirect('resume')


@login_required
def delete_work(request, work_id):
    WorkExperience.objects.delete_work(
        work_id,
        get_user_id(request)
    )

    return redirect('resume')


# ===================== Course CRUD =====================

@login_required
def add_course(request):
    if request.method == 'POST':
        CourseRecord.objects.add_course(
            get_user_id(request),
            request.POST.get('course_name'),
            request.POST.get('semester'),
            request.POST.get('grade')
        )

        return redirect('resume')

    return render(request, 'accounts/add_course.html')


@login_required
def update_course(request, course_record_id):
    if request.method == 'POST':
        CourseRecord.objects.update_course(
            course_record_id,
            get_user_id(request),
            request.POST.get('course_name'),
            request.POST.get('semester'),
            request.POST.get('grade')
        )

    return redirect('resume')


@login_required
def delete_course(request, course_record_id):
    CourseRecord.objects.delete_course(
        course_record_id,
        get_user_id(request)
    )

    return redirect('resume')


# ===================== Onboarding =====================

@login_required
def onboarding(request):
    user_id = get_user_id(request)
    role = request.session.get('role')

    departments = Department.objects.get_all_departments()
    companies = Company.objects.get_all_companies()

    if request.method == 'POST':
        department_id = request.POST.get('department_id') or None
        enrollment_year = request.POST.get('enrollment_year') or None
        graduation_year = request.POST.get('graduation_year') or None
        company_id = request.POST.get('company_id') or None
        current_job_title = request.POST.get('current_job_title') or None

        if role == 'student':
            company_id = None
            current_job_title = None

        Account.objects.update_onboarding(
            user_id,
            department_id,
            enrollment_year,
            graduation_year,
            company_id,
            current_job_title
        )

        course_name = request.POST.get('course_name')
        if course_name:
            CourseRecord.objects.add_course(
                user_id,
                course_name,
                '',
                ''
            )

        activity_title = request.POST.get('activity_title')
        activity_category = request.POST.get('activity_category')
        if activity_title:
            Activity.objects.add_activity(
                user_id,
                activity_category,
                activity_title,
                '',
                None,
                None,
                ''
            )

        request.session['is_profile_completed'] = 1
        return redirect('resume')

    return render(request, 'accounts/onboarding.html', {
        'role': role,
        'departments': departments,
        'companies': companies,
        'year_options': get_year_options(),
    })