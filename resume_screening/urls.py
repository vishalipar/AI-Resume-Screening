from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('candidates/', views.candidates, name='candidates'),
    path('delete/<int:user_id>/', views.delete_user, name='delete_user'),
]