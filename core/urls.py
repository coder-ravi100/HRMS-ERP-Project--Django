from django.urls import path
from .import views

urlpatterns = [
      
      path('',views.user_login, name='user-login'),
      path('logout/', views.user_logout, name='user-logout'),
      path('forgot/', views.forgot_password, name='forgot-password'),
      path('reset_password/', views.reset_password, name='reset-password'),

      

      path('admin_dashboard/', views.admin_dashboard, name='admin-dashboard'),
      path('employee_dashboard/', views.employee_dashboard,  name='employee-dashboard'),


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
      
      path('my_task/', views.my_task, name='my-task'),
      path('task_update/<int:pk>', views.update_task_status, name='update-task-status'),



      path('leave_apply/', views.apply_leave, name='apply-leave'),
      path('leave_list/', views.leave_list, name='leave-list'),
      path('my_leave/', views.my_leave, name='my-leave'),
      path('leave_status/<int:pk>',views.update_leave_status, name='update-leave-status'),


      
      path('add_attendance/', views.add_attendance, name = 'add-attendance'),
      path('list_attendance/',  views.list_attendance, name='list-attendance'),
      path('edit_attendance/<int:pk>', views.edit_attendance, name='edit-attendance'),
      path('delete_attendance/<int:pk>',views.delete_attendance, name='delete-attendance'),
      
      path('my_attendance/', views.my_attendance, name='my-attendance'),

]
