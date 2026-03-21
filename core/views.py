from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from .forms import * #RegistrationForm

from .models import Department, EmployeeProfile, Task, Leave
from core.models import User
from django.utils import timezone
from datetime  import timedelta
import random
from .utils import *

# Create your views here.
#---------------------------------------------------------
#           ******ADMIN DASHBOARD SECTION******
#---------------------------------------------------------
@never_cache
@login_required
def admin_dashboard(request):
    if request.user.role != "ADMIN":
        return redirect('employee-dashboard')
    return render(request,'dashboard/Admin_Dashboard.html')


#---------------------------------------------------------
#           ******EMPLOYEE DASHBOARD SECTION******
#---------------------------------------------------------
@never_cache
@login_required
def employee_dashboard(request):
    if request.user.role != "EMPLOYEE":
        return redirect('admin-dashboard')
    return render(request,'dashboard/Employee_Dashboard.html')


#---------------------------------------------------------
#           ******LOGIN SECTION******
#---------------------------------------------------------
def user_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid Credentials")
            return redirect('user-login')

        user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)

           
            next_url = request.GET.get('next')

            if user.role == "ADMIN":
                return redirect(next_url or 'admin-dashboard')
            else:
                return redirect(next_url or 'employee-dashboard')

        else:
            messages.error(request, "Invalid Credentials")
    return render(request,'authentication/Login.html')



def user_logout(request):
    logout(request)
    request.session.flush()
    messages.success(request, "You Have Been Logged out")
    return redirect('user-login')



def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            #cooldown (60 sec)
            if user.otp_created_at and user.otp_created_at > timezone.now() - timedelta(seconds=60):
                messages.error(request, "Wait before requesting new OTP")
                return redirect('forgot-password')

            #generate 6-digit OTP
            otp = str(random.randint(100000, 999999))

            user.otp = otp
            user.otp_created_at = timezone.now()
            user.otp_attempts = 0
            user.save()

            sendmailForOtp(
                "Password Reset OTP",
                "otp_template",
                user.email,
                {'otp': otp}
            )

            request.session['reset_email'] = email

            messages.success(request, "OTP sent")
            return redirect('reset-password')

        except User.DoesNotExist:
            messages.error(request, "Email not registered")

    return render(request, 'authentication/forgot_password.html')


def reset_password(request):
    email = request.session.get('reset_email')

    if not email:
        messages.error(request, "Session expired")
        return redirect('forgot-password')

    if request.method == "POST":
        otp = request.POST.get('otp')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        try:
            user = User.objects.get(email=email)

            #OTP expiry (5 min)
            if not user.otp_created_at or user.otp_created_at < timezone.now() - timedelta(minutes=5):
                messages.error(request, "OTP expired")
                return redirect('forgot-password')

            #OTP check
            if str(user.otp) != otp:
                messages.error(request, "Invalid OTP")
                return redirect('reset-password')

            #password match
            if password != confirm_password:
                messages.error(request, "Passwords do not match")
                return redirect('reset-password')

            #update password
            user.set_password(password)
            user.otp = None
            user.otp_created_at = None
            user.save()

            #clear session
            request.session.pop('reset_email', None)

            messages.success(request, "Password reset successful")
            return redirect('user-login')

        except User.DoesNotExist:
            messages.error(request, "User not found")
            return redirect('forgot-password')

    return render(request,'authentication/Reset_password.html',{'email' : email})



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
        print("PASSWORD:", password)

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


def task_edit(request,pk):
    tasks = Task.objects.get(id=pk)
    employees = User.objects.filter(role="EMPLOYEE")

    if request.method == "POST":

        tasks.title = request.POST['title']
        tasks.description = request.POST['description']
        tasks.assigned_to = User.objects.get(id=request.POST['assigned_to'])
        tasks.assigned_by = request.user
        tasks.due_date = request.POST['due_date']
        tasks.status = request.POST['status']

        tasks.save()

        tasks = Task.objects.all()
        context = {
            'tasks' : tasks,
            'employees' : employees
        }
        return render(request,'tasks/Task_list.html',context)
    context = {
        'tasks' : tasks,
        'employees' : employees
    }
    return render(request,'tasks/Task_edit.html',context)
    

    
def task_delete(request,pk):
    tasks = Task.objects.get(id=pk)
    tasks.delete()

    tasks = Task.objects.all()

    context = {
        'tasks' : tasks
    }
    return render(request,'tasks/Task_list.html',context)




#---------------------------------------------------------
#           ******LEAVE SECTION******
#---------------------------------------------------------
def apply_leave(request):

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')

        Leave.objects.create(
            employee = request.user,
            start_date = start_date,
            end_date = end_date,
            reason = reason
        )
        #Fetch The Data
        leaves = Leave.objects.filter(employee=request.user)
        context = {
            'leaves': leaves
        }
        return render(request,'leave/My_leave.html',context)
    
    return render(request,'leave/Leave_apply.html')



def leave_list(request):
    leaves = Leave.objects.select_related('employee')

    context = {
        'leaves' : leaves
    }
    return render(request,'leave/Leave_list.html',context)



def my_leave(request):
    leaves = Leave.objects.filter(employee=request.user)
    
    context = {
        'leaves' : leaves
    }
    return render(request,'leave/My_leave.html',context)

def update_leave_status(request,pk):
    leave = Leave.objects.get(id=pk)
    if leave.status == "POST":
        leave.status = request.POST.get('status')
        leave.save()
    context = {
        'leave' : leave
    }
    return render(request,'leave/Leave_list.html',context)



