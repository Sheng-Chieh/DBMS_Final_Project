from django.shortcuts import render, redirect
from .models import Account, Activity, WorkExperience, CourseRecord, Company, Department

def register(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', '').strip()

        try:
            user_id = Account.objects.create_user_with_raw_sql(name, email, password, role)

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
            else:
                return redirect('resume')
        
        return render(request, 'accounts/login.html', {
            'error': 'Email 或密碼錯誤'
        })

    return render(request, 'accounts/login.html')

def logout(request):
    request.session.flush()
    return redirect('login')

def resume(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session.get('user_id')

    user = Account.objects.get_user_by_id(user_id)

    activities = Activity.objects.get_user_activities(user_id)
    works = WorkExperience.objects.get_user_work_experiences(user_id)
    courses = CourseRecord.objects.get_user_courses(user_id)
    companies = Company.objects.get_all_companies()

    timeline_items = []

    for course in courses:
        timeline_items.append({
        'type': 'course',
        'type_label': '課程',
        'title': course['course_name'],
        'subtitle': course.get('course_category', ''),
        'time': course.get('semester', '未填寫'),
        'description': f"課程類別：{course.get('course_category', '')}"
    })

    for activity in activities:
        timeline_items.append({
        'type': 'activity',
        'type_label': '活動',
        'title': activity['title'],
        'subtitle': activity.get('role', ''),
        'time': activity.get('start_date', ''),
        'description': activity.get('description', '')
    })

    for work in works:
        timeline_items.append({
        'type': 'work',
        'type_label': '工作',
        'title': work['job_title'],
        'subtitle': work['company_name'],
        'time': work.get('start_date', ''),
        'description': work.get('description', '')
    })
    return render(request, 'accounts/resume.html', {
        'user': user,
        'activities': activities,
        'works': works,
        'courses': courses,
        'companies': companies,
        'timeline_items': timeline_items
    })

def add_activity(request):
    if 'user_id' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        user_id = request.session.get('user_id')

        category = request.POST.get('category')
        title = request.POST.get('title')
        role = request.POST.get('role')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        description = request.POST.get('description')

        Activity.objects.add_activity(
            user_id, category, title, role, start_date, end_date, description
        )

        return redirect('resume')

    return render(request, 'accounts/add_activity.html')

def delete_activity(request, activity_id):
    if 'user_id' not in request.session:
        return redirect('login')

    Activity.objects.delete_activity(activity_id, request.session.get('user_id'))
    return redirect('resume')

def update_activity(request, activity_id):
    if 'user_id' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        user_id = request.session.get('user_id')

        category = request.POST.get('category')
        title = request.POST.get('title')
        role = request.POST.get('role')
        start_date = request.POST.get('start_date') or None
        end_date = request.POST.get('end_date') or None
        description = request.POST.get('description')

        Activity.objects.update_activity(
            activity_id, user_id, category, title, role, start_date, end_date, description
        )

    return redirect('resume')


def add_work(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session.get('user_id')
    companies = Company.objects.get_all_companies()

    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        job_type = request.POST.get('job_type')
        job_title = request.POST.get('job_title')
        start_date = request.POST.get('start_date') or None
        end_date = request.POST.get('end_date') or None
        description = request.POST.get('description')

        WorkExperience.objects.add_work(
            user_id,
            company_id,
            job_type,
            job_title,
            start_date,
            end_date,
            description
        )

        return redirect('resume')

    return render(request, 'accounts/add_work.html', {
        'companies': companies
    })

def delete_work(request, work_id):
    if 'user_id' not in request.session:
        return redirect('login')

    WorkExperience.objects.delete_work(work_id, request.session.get('user_id'))
    return redirect('resume')

def update_work(request, work_id):
    if 'user_id' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        user_id = request.session.get('user_id')

        company_id = request.POST.get('company_id')
        job_type = request.POST.get('job_type')
        job_title = request.POST.get('job_title')
        start_date = request.POST.get('start_date') or None
        end_date = request.POST.get('end_date') or None
        description = request.POST.get('description')

        WorkExperience.objects.update_work(
            work_id, user_id, company_id, job_type, job_title, start_date, end_date, description
        )

    return redirect('resume')

def add_course(request):
    if 'user_id' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        user_id = request.session.get('user_id')
        course_name = request.POST.get('course_name')
        course_category = request.POST.get('course_category')
        semester = request.POST.get('semester')
        grade = request.POST.get('grade')

        CourseRecord.objects.add_course(
            user_id, course_name, course_category, semester, grade
        )

        return redirect('resume')

    return render(request, 'accounts/add_course.html')

def delete_course(request, course_record_id):
    if 'user_id' not in request.session:
        return redirect('login')

    CourseRecord.objects.delete_course(course_record_id, request.session.get('user_id'))
    return redirect('resume')

def update_course(request, course_record_id):
    if 'user_id' not in request.session:
        return redirect('login')

    if request.method == 'POST':
        user_id = request.session.get('user_id')

        course_name = request.POST.get('course_name')
        course_category = request.POST.get('course_category')
        semester = request.POST.get('semester')
        grade = request.POST.get('grade')

        CourseRecord.objects.update_course(
            course_record_id, user_id, course_name, course_category, semester, grade
        )

    return redirect('resume')

def onboarding(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session.get('user_id')
    role = request.session.get('role')

    departments = Department.objects.get_all_departments()
    companies = Company.objects.get_all_companies()

    if request.method == 'POST':
        department_id = request.POST.get('department_id') or None
        enrollment_year = request.POST.get('enrollment_year') or None
        graduation_year = request.POST.get('graduation_year') or None
        current_company = request.POST.get('current_company') or None
        current_job_title = request.POST.get('current_job_title') or None

        Account.objects.update_onboarding(
            user_id,
            department_id,
            enrollment_year,
            graduation_year,
            current_company,
            current_job_title
        )

        # 選填：快速新增第一筆課程
        course_name = request.POST.get('course_name')
        course_category = request.POST.get('course_category')

        if course_name:
            CourseRecord.objects.add_course(
                user_id,
                course_name,
                course_category,
                '',
                ''
            )

        # 選填：快速新增第一筆活動
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

        # 選填：快速新增第一筆工作
        company_id = request.POST.get('company_id')
        job_title = request.POST.get('job_title')
        job_type = request.POST.get('job_type')

        if company_id and job_title:
            WorkExperience.objects.add_work(
                user_id,
                company_id,
                job_type,
                job_title,
                None,
                None,
                ''
            )

        request.session['is_profile_completed'] = 1
        return redirect('resume')

    return render(request, 'accounts/onboarding.html', {
        'role': role,
        'departments': departments,
        'companies': companies
    })