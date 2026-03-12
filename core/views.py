from django.shortcuts import render

# Create your views here.
def create_employees(request):
    return render(request, 'employee/employee_create.html')


def view_employees(request):
    return render(request,'employee/employee_list.html')