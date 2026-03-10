from django.contrib import admin
from .models import Department ,EmployeeProfile ,Leave ,Task

# Register your models here.
admin.site.register(Department)
admin.site.register(EmployeeProfile)
admin.site.register(Leave)
admin.site.register(Task)