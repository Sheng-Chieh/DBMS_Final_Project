"""
URL configuration for finalproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from company import views
from microprojects import views as micro_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('search/', views.search_companies, name='search_companies'),
    path('company/<int:company_id>/', views.company_detail, name='company_detail'),
    path('projects/', micro_views.project_list, name='project_list'), 
    path('company/chat_lc/', views.chat_recommend_companies_lc, name='chat_recommend_companies_lc'),
    path('company/chat/', views.company_chat_page, name='company_chat_page'),
]
