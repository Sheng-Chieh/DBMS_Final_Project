from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='homepage'),
    path('home/', views.index_logged_in, name='homepage_logged_in'),
]
