from django.shortcuts import render
from .models  import Department, EmployeeProfile ,Task
from core.models import User
from django.contrib import messages
import random ,string

# Create your views here.
def admin_dashboard(request):
    return render(request,'dashboard/Admin_Dashboard.html')

#---------------------------------------------------------
#           ******DEPARTMENT SECTION******
#---------------------------------------------------------
#Add Department Bussiness Logic Code
def add_department(request):
    if request.method == "POST":
        dep_name = request.POST["name"]
        dep_description = request.POST["description"]
        d_id = Department.objects.create(
            name = dep_name,
            description = dep_description,
        )
        if d_id:
            d_all = Department.objects.all()
            contaxt = {
                'd_all' : d_all,
            }
        
        return render(request,'department/Department_list.html',contaxt)
    
    return render(request,'department/Department_add.html')


#View Department Bussiness Logic  Code
def list_department(request):
     d_all = Department.objects.all()
     contaxt = {
         'd_all' : d_all
     }
     return render(request,'department/Department_list.html',contaxt)


#Edit Department Bussiness Logic Code
def edit_department(request, pk):
    if request.method == "POST":
        d_id = Department.objects.get(id = pk)
        d_id.name = request.POST['name']
        d_id.description = request.POST['description']

        d_id.save()
        d_all = Department.objects.all()

        contaxt = {
            'd_all' : d_all
        }
        return render(request,'department/Department_list.html',contaxt)
    else:
        d_id = Department.objects.get(id = pk)
        contaxt = {
            'd_id' : d_id
        }
        return render(request,'department/Department_edit.html',contaxt)


#Delete Department Bussiness Logic Code
def delete_department(request,pk):
   try:
       d_id = Department.objects.get(id = pk)
       d_id.delete()

       d_all = Department.objects.all()
       contaxt = {
           'd_all' : d_all
       }
       return render(request,'department/Department_list.html',contaxt)
   except:
       d_all = Department.objects.all()
       contaxt = {
           'd_all' : d_all
       }
       return render(request,'department/Department_list.html',contaxt)
   



#---------------------------------------------------------
#           ******EMPLOYEE SECTION******
#---------------------------------------------------------

#Create Employee Bussiness Logic  Code
def add_employee(request):

    departments = Department.objects.all()

    if request.method == "POST":
        # USER DATA
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        role = request.POST['role']
        phone = request.POST['phone']
        address = request.POST['address']
        profile_pic = request.FILES.get('profile_pic')

        # USERNAME
        username = first_name.lower() + last_name.lower()

        # RANDOM PASSWORD
        l1 = ['34xx','35xx','36xx','37xx','38xx','39xx']
        password = first_name[0:2] + email[0:3] + random.choice(l1)

        # EMPLOYEE PROFILE DATA
        dep_id = request.POST['department']
        designation = request.POST['designation']
        salary = request.POST['salary']
        join_date = request.POST['join_date']
        experience = request.POST['experience']

        department = Department.objects.get(id=dep_id)

        # CREATE USER
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            phone=phone,
            address=address,
            profile_pic=profile_pic
        )

        # CREATE EMPLOYEE PROFILE
        EmployeeProfile.objects.create(
            user=user,
            department=department,
            designation=designation,
            salary=salary,
            join_date=join_date,
            experience=experience
        )

        employees = EmployeeProfile.objects.all()

        context = {
            "employees": employees
        }

        return render(request,'employee/Employee_list.html',context)

    context = {
        "departments": departments
    }

    return render(request,'employee/Employee_add.html',context)


#Edit Employee Bussiness Logic  Code
def list_employee(request):
    employees = EmployeeProfile.objects.select_related('user','department')
    context = {
        'employees' : employees
    }
    return render(request,'employee/Employee_list.html',context)




#Update Employee Bussiness Logic  Code
def edit_employee(request,pk):
    
    emp_id = EmployeeProfile.objects.get(id=pk)
    dep_id = Department.objects.all()

    if request.method == "POST":
        #USER UPDATE
        emp_id.user.first_name = request.POST['first_name']
        emp_id.user.last_name = request.POST['last_name']
        emp_id.user.email = request.POST['email']
        emp_id.user.phone = request.POST['phone']
        emp_id.user.address = request.POST['address']

        profile_pic = request.FILES.get('profile_pic')
        if profile_pic:
            emp_id.user.profile_pic = profile_pic
        emp_id.user.save()

        #EMPLOYEE PROFILE UPDATE
        dep_id = request.POST['department']
        emp_id.department = Department.objects.get(id=dep_id)

        emp_id.designation = request.POST['designation']
        emp_id.salary = request.POST['salary']
        join_date = request.POST.get('join_date')

        if join_date:
            emp_id.join_date = join_date        

        emp_id.experience = request.POST['experience']

        emp_id.save()

        employees = EmployeeProfile.objects.all()
        context = {
            'employees' : employees
        }
        return render(request,'employee/Employee_list.html',context)
    context = {
        'emp_id' : emp_id,
        'dep_id' : dep_id
    }
    return render(request,'employee/Employee_edit.html',context)

#Show Employee Bussiness Logic code
def show_employee(request,pk):
    emp = EmployeeProfile.objects.get(id=pk)
    dep = Department.objects.all()

    context = {
        'emp' : emp,
        'dep' :dep
    }
    return render(request,'employee/Employee_show.html',context)


#Delete Employee Bussiness Logic  Code
def delete_employee(request,pk):
    emp = EmployeeProfile.objects.get(id = pk)
    emp.user.delete()

    employees = EmployeeProfile.objects.all()

    context = {
        "employees" : employees
    }
    return render(request,'employee/Employee_list.html',context)


#---------------------------------------------------------
#           ******TASKS SECTION******
#---------------------------------------------------------

def add_task(request):
    employees = User.objects.filter(role="EMPLOYEE")

    if request.method == "POST":

        title = request.POST.get('title')
        description = request.POST.get('description')
        assigned_to = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')
        status = request.POST.get('status')

        employee = User.objects.get(id = assigned_to)

        Task.objects.create(
            title = title,
            description = description,
            assigned_to = employee,
            assigned_by = request.user,
            due_date = due_date,
            status = status
        )
        return render(request,'tasks/Task_list.html')
    context = {
        'employees' : employees
    }
    return render(request,'tasks/Task_add.html',context)


def list_task(request):
    tasks = Task.objects.select_related("assigned_to", "assigned_by")
    
    context = {
        'tasks' : tasks
    }
    return render(request,'tasks/task_list.html',context)


def task_view(request):
    return render(request,'tasks/Task_view.html')