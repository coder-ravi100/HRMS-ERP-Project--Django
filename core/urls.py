
from django.urls import path
from . import views

urlpatterns = [

    path('create-employee/', views.create_employees, name='create-employee'),
    path('view-employee/', views.view_employees, name='view-employee'),
    path('update_employee/',  views.update_employee , name='update-employee'),



    path('create_department/', views.create_department, name='create-department'),
    path('list_department/', views.list_department, name='list-department'),
]