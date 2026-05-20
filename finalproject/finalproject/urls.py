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
from microprojects.views import project_list, project_create
from accounts import views as account_views
from coffeechat import views as coffeechat_student_views
from coffeechat_alumni import views as coffeechat_alumni_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('search/', views.search_companies, name='search_companies'),
    path('company/<int:company_id>/', views.company_detail, name='company_detail'),

    path('projects/', micro_views.project_list, name='project_list'),
    path('projects/create/', project_create, name='project_create'), 

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
    
    path('resume/', account_views.resume, name='resume'),
    path('add-activity/', account_views.add_activity, name='add_activity'),
    path('add-work/', account_views.add_work, name='add_work'),
    path('add-course/', account_views.add_course, name='add_course'),
    path('onboarding/', account_views.onboarding, name='onboarding'),
    path('activity/delete/<int:activity_id>/', account_views.delete_activity, name='delete_activity'),
    path('work/delete/<int:work_id>/', account_views.delete_work, name='delete_work'),
    path('course/delete/<int:course_record_id>/', account_views.delete_course, name='delete_course'),
    path('activity/update/<int:activity_id>/', account_views.update_activity, name='update_activity'),
    path('work/update/<int:work_id>/', account_views.update_work, name='update_work'),
    path('course/update/<int:course_record_id>/', account_views.update_course, name='update_course'),
    path('logout/', account_views.logout, name='logout'),
    path('profile/update/', account_views.update_profile, name='update_profile'),

]
