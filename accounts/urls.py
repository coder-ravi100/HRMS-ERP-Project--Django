
from django.urls import path
from . import views

urlpatterns = [
   path("", views.login_view, name="login_view"),
   path("admin/dashboard/", views.admin_dashboard, name = "admin_dashboard"),
   path("hr/dashboard/", views.hr_dashboard, name = "hr_dashboard"),
   path("manager/dashboard/", views.manager_dashboard, name = "manager_dashboard"),
   path("employee/dashboard/", views.employee_dashboard, name = "employee_dashboard"),
   
]
