from django.urls import path
from . import views

urlpatterns = [
    path('', views.organize_test, name='organize_test')
]