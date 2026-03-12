from django.shortcuts import render

# Create your views here.
def create_employees(request):
    return render(request, 'employee/employee_create.html')


def view_employees(request):
    return render(request,'employee/employee_list.html')

def update_employee(request):
    return render(request,'employee/employee_update.html')



def create_department(request):
    return render(request,'department/department_create.html')

def list_department(request):
    return render(request,'department/department_list.html')