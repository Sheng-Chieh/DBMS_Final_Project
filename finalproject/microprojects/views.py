from django.shortcuts import render, redirect
from .models import MicroProject 

def project_list(request):
    search_industry = request.GET.get('industry', '')
    search_company = request.GET.get('company', '')
    search_tag = request.GET.get('tag', '')

    # 呼叫 MicroProject 拿資料
    filter_industries, filter_companies, filter_tags = MicroProject.objects.get_filter_options()
    projects = MicroProject.objects.search_projects(search_industry, search_company, search_tag)

    return render(request, 'microproject/microproject_list.html', {
        'projects': projects,
        'filter_industries': filter_industries,
        'filter_companies': filter_companies,
        'filter_tags': filter_tags,
        'current_industry': search_industry,
        'current_company': search_company,
        'current_tag': search_tag,
    })

def project_create(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')

    if not user_id:
        return redirect('/login/') 
    if user_role != 'alumni':
        return redirect('/projects/')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        company_id = request.POST.get('company_id') 
        selected_tags = request.POST.getlist('tags') 
        
        # 呼叫 MicroProject 一次搞定寫入邏輯
        MicroProject.objects.create_project_with_tags(
            alumni_id=user_id, 
            company_id=company_id, 
            title=title, 
            description=description, 
            selected_tags=selected_tags
        )
        return redirect('/projects/') 

    # 呼叫 MicroProject 拿下拉選單資料
    filter_industries, filter_companies, filter_tags = MicroProject.objects.get_filter_options()
        
    return render(request, 'microproject/microproject_create.html', {
        'tags': filter_tags,
        'industries': filter_industries,  
        'companies': filter_companies
    })