
from django.urls import path
from . import views

urlpatterns = [

    path('create-employee/', views.create_employees, name='create-employee'),
    path('view-employee/', views.view_employees, name='view-employee'),
]