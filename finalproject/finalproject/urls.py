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
from accounts import views as account_views
from coffeechat import views as coffeechat_student_views
from coffeechat_alumni import views as coffeechat_alumni_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('search/', views.search_companies, name='search_companies'),
    path('company/<int:company_id>/', views.company_detail, name='company_detail'),

    path('projects/', micro_views.project_list, name='project_list'), 

    path('login/', account_views.login, name='login'),
    path('register/', account_views.register, name='register'),

    path('company/chat_lc/', views.chat_recommend_companies_lc, name='chat_recommend_companies_lc'),
    path('company/chat/', views.company_chat_page, name='company_chat_page'),

    # 學生端 (coffeechat_student_views)
    path('coffeechat/apply/', coffeechat_student_views.apply_chat, name='apply_chat'),
    path('coffeechat/my-applications/', coffeechat_student_views.my_applications, name='my_applications'),

    # 校友端 (coffeechat_alumni_views)
    path('', coffeechat_alumni_views.homepage, name='homepage'),
    path('homepage/', coffeechat_alumni_views.homepage, name='homepage_alt'),
    
    path('create-coffee-chat/', coffeechat_alumni_views.create_coffee_chat, name='create_coffee_chat'),
    path('edit-coffee-chat/<int:chat_id>/', coffeechat_alumni_views.edit_coffee_chat, name='edit_coffee_chat'),
    path('manage-reservations/', coffeechat_alumni_views.list_manage_reservation, name='list_manage_reservation'),
    
    path('applicant/<int:applicant_id>/accept/', coffeechat_alumni_views.accept_applicant, name='accept_applicant'),
    path('manage-reservation/<int:chat_id>/', coffeechat_alumni_views.manage_reservation, name='manage_reservation'),
    path('toggle-coffee-chat-status/<int:chat_id>/', coffeechat_alumni_views.toggle_coffee_chat_status, name='toggle_coffee_chat_status'),
    path('delete_chat/<int:chat_id>/', coffeechat_alumni_views.delete_coffee_chat, name='delete_coffee_chat'),
]
