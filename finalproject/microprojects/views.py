from django.shortcuts import render
from django.db import connection

def project_list(request):
    with connection.cursor() as cursor:
        sql = "SELECT project_id, title, description, industry, status FROM micro_project WHERE status = 'Active'"
        cursor.execute(sql)
        projects = cursor.fetchall()

    # 把原本的 'project_list.html' 改成帶有路徑的正確檔名
    return render(request, 'microproject/microproject_list.html', {'projects': projects})

# Create your views here.
