from django.urls import path
from . import views

urlpatterns = [
    path('', views.organize_test, name='organize_test'),
    path('add_question/', views.add_question, name='add_question'),
    path('manage_test/', views.manage_test, name='manage_test'),
]