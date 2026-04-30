from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:token>/', views.assessment_test, name='assessment_test'),
]