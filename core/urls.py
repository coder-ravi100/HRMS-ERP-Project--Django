from django.urls import path
from .import views

urlpatterns = [
      path('admin_dashboard/', views.admin_dashboard, name='admin-dashboard'),


      path('add_department/', views.add_department, name='add-department'),
      path('list_department/', views.list_department, name='list_department'),
      path('edit_department/<int:pk>', views.edit_department, name='edit-department'),
      path('delete_department/<int:pk>', views.delete_department, name='delete-department'),



      path('add_employee/', views.add_employee, name='add-employee'),
      path('list_employee/', views.list_employee, name='list-employee'),
      path('show_employee/<int:pk>', views.show_employee, name='show-employee'),
      path('edit_employee/<int:pk>', views.edit_employee, name='edit-employee'),
      path('delete_employee/<int:pk>', views.delete_employee, name='delete-employee'),



      path('add_task/', views.add_task, name='add-task'),
      path('list_task/', views.list_task, name='list-task'),
      path('task_edit/<int:pk>', views.task_edit, name='task-edit'),
      path('task_delete/<int:pk>', views.task_delete, name='task-delete'),

]
