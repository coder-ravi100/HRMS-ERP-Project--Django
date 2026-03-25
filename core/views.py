from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from .forms import * #RegistrationForm

from .models import Department, EmployeeProfile, Task, Leave, Attendance
from core.models import User
from django.utils import timezone
from datetime  import timedelta
import random

from .utils import *
from django.utils.timezone import localtime,now
from django.db.models  import Count
from .utils import sendmailForOtp

# Create your views here.
#---------------------------------------------------------
#           ******ADMIN DASHBOARD SECTION******
#---------------------------------------------------------
@never_cache
@login_required
def admin_dashboard(request):
    if request.user.role != "ADMIN":
        return redirect('employee-dashboard')
    
    today = now().date()

    # ================= KPI =================
    total_employees = User.objects.filter(role="EMPLOYEE").count()

    present_today = Attendance.objects.filter(
        date=today,
        status="Present"
    ).count()

    on_leave = Leave.objects.filter(
        status="Approved",
        start_date__lte=today,
        end_date__gte=today
    ).count()

    pending_leaves = Leave.objects.filter(status="Pending").count()


    # ================= ATTENDANCE TREND =================
    last_7_days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Attendance.objects.filter(
            date=day,
            status="Present"
        ).count()

        last_7_days.append({
            "day": day.strftime("%a"),
            "present": count
        })


    # ================= TASK DONUT =================
    task_data = [
        {"label": "Pending", "value": Task.objects.filter(status="Pending").count()},
        {"label": "In Progress", "value": Task.objects.filter(status="In Progress").count()},
        {"label": "Completed", "value": Task.objects.filter(status="Completed").count()},
    ]


    # ================= DEPARTMENT PERFORMANCE =================
    departments = Department.objects.all()
    dept_data = []

    for dept in departments:
        employees = User.objects.filter(employeeprofile__department=dept)

        total_tasks = Task.objects.filter(assigned_to__in=employees).count()
        completed_tasks = Task.objects.filter(
            assigned_to__in=employees,
            status="Completed"
        ).count()

        percentage = 0
        if total_tasks > 0:
            percentage = int((completed_tasks / total_tasks) * 100)

        dept_data.append({
            "dept": dept.name,
            "completed": percentage
        })


    context = {
        "total_employees": total_employees,
        "present_today": present_today,
        "on_leave": on_leave,
        "pending_leaves": pending_leaves,

        "attendance_data": last_7_days,
        "task_data": task_data,
        "dept_data": dept_data,
    }

    return render(request,'dashboard/Admin_Dashboard.html',context)


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
            print("INPUT EMAIL:", email)
            print("USER FOUND:", user.username, user.email)
            
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

            # OTP expiry (5 min)
            if not user.otp_created_at or user.otp_created_at < timezone.now() - timedelta(minutes=5):
                messages.error(request, "OTP expired")
                return redirect('forgot-password')

            # attempts limit
            user.otp_attempts += 1
            if user.otp_attempts > 5:
                messages.error(request, "Too many attempts")
                return redirect('forgot-password')

            # OTP match
            if str(user.otp) != otp:
                user.save()
                messages.error(request, "Invalid OTP")
                return redirect('reset-password')

            # password match
            if password != confirm_password:
                messages.error(request, "Passwords do not match")
                return redirect('reset-password')

            # update password
            user.set_password(password)
            user.otp = None
            user.otp_created_at = None
            user.otp_attempts = 0
            user.save()

            request.session.pop('reset_email', None)

            messages.success(request, "Password reset successful")
            return redirect('user-login')

        except User.DoesNotExist:
            messages.error(request, "User not found")
            return redirect('forgot-password')
    context = {
        'email' : email
    }
    return render(request, 'authentication/Reset_password.html',context)


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

#Create Employee Bussiness Logic Code
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
#add Task Bussiness Logic  Code
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
        return redirect('list-task')
    context = {
        'employees' : employees
    }
    
    return render(request,'tasks/Task_add.html',context)


#List Task Bussiness Logic  Code
def list_task(request):
    tasks = Task.objects.select_related("assigned_to", "assigned_by").order_by('-id')
    
    context = {
        'tasks' : tasks
    }
    return render(request,'tasks/task_list.html',context)


#Edit Task Bussiness Logic  Code
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
    

#Delete Task Bussiness Logic  Code  
def task_delete(request,pk):
    tasks = Task.objects.get(id=pk)
    tasks.delete()

    tasks = Task.objects.all()

    context = {
        'tasks' : tasks
    }
    return render(request,'tasks/Task_list.html',context)



#Employee Tasks Businees Logic 
def my_task(request):
    tasks = Task.objects.filter(assigned_to=request.user).select_related('assigned_to','assigned_by')
    context = {
        'tasks' : tasks
    }
    return render(request,'tasks/My_task.html',context)



#Employee Task Mark Business Logic
def update_task_status(request,pk):
    task = Task.objects.get(id=pk,assigned_to=request.user)

    task.status = 'Completed'
    task.save()
    return redirect('my-task')


#---------------------------------------------------------
#           ******LEAVE SECTION******
#---------------------------------------------------------
#Apply Employee Leave Bussiness Logic  Code
def apply_leave(request):
    if request.user.role != "EMPLOYEE":
        return redirect('employee-dashboard')

    if request.method == "POST":
        Leave.objects.create(
            employee=request.user,
            start_date=request.POST.get("start_date"),
            end_date=request.POST.get("end_date"),
            reason=request.POST.get("reason"),
            status="Pending"
        )
        return redirect('my-leave')

    return render(request, 'leave/Leave_apply.html')


#Admin Show Leave List Bussiness Logic  Code
def leave_list(request):
    leaves = Leave.objects.select_related('employee').order_by('-id')

    context = {
        'leaves' : leaves
    }
    return render(request,'leave/Leave_list.html',context)


#Employee Leave Show Bussiness Logic  Code
def my_leave(request):
    leaves = Leave.objects.filter(employee=request.user).order_by('-id')
    
    context = {
        'leaves' : leaves
    }
    return render(request,'leave/My_leave.html',context)



#Update Leave For Admin Bussiness Logic  Code
def update_leave_status(request,pk):
    
    if request.method == "POST":
        try:
            leave = Leave.objects.get(id=pk)
        except Leave.DoesNotExist:
            return redirect('leave-list')  

        status = request.POST.get('status')

        if status in ["Approved", "Rejected"]:
            leave.status = status
            leave.save()

    return redirect('leave-list')



#---------------------------------------------------------
#           ******ATTENDANCE SECTION******
#---------------------------------------------------------

#Employee Attendance Logic code
def my_attendance(request):
    if request.user.role != "EMPLOYEE":
        messages.error(request, "Only Employees Can Mark Attendance")
        return redirect('employee-dashboard')
   
    user = request.user
    today = localtime().date()
    
    #get today Records
    attendance = Attendance.objects.filter(employee=user, date=today).first()

    if request.method == "POST":
        action = request.POST.get('action')

        #check-in (only once per day)
        if action == "checkin":
            if attendance:
                messages.warning(request, "You Can Mark Attendance  Only Once Per Day")
            else:
                Attendance.objects.create(
                    employee=user,
                    date=today,
                    check_in = localtime().time(),
                    status="Present"
                )
                messages.success(request, "Check-in Successful")
        #Check-Out
        elif  action == "checkout":
            if not attendance:
                messages.error(request, "You Must Check In First")
            elif attendance.check_out:
                messages.warning(request, "Already Checked Out")
            else:
                attendance.check_out = localtime().time()
                attendance.save()
                messages.success(request, "Check-Out Successful")
        return redirect('my-attendance')
    

    context = {
        'today_attendance' : attendance,
        'today_date' : today
    }
    return render(request,'attendance/My_attendance.html',context)

#--Curd For Employee By Admin 

#Add Attendance Logic Code
# @login_required
# def add_attendance(request):
#     return render(request,'attendance/Attendance_add.html')


#List Attendance Logic Code
@login_required
def list_attendance(request):
    if request.user.role != "ADMIN":
        return redirect('admin-dashboard')
    attendance = Attendance.objects.all().order_by('-date')
    context =  {
        'attendance' : attendance
    }
    return render(request, 'attendance/Attendance_list.html',context)



#Edit Attendance Logic code
@login_required
def edit_attendance(request,pk):
    if request.user.role != "ADMIN":
        return redirect('admin-dashboard')
    
    try:
        attendace = Attendance.objects.get(id = pk)
    except Attendance.DoesNotExist:
        messages.error(request, "Record Not Found")
        return redirect('list-attendance')
    
    if request.method == "POST":
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        status = request.POST.get('status')
        
        attendace.check_in = check_in or None
        attendace.check_out = check_out or None
        attendace.status = status

        attendace.save()
        messages.success(request, "Update Successfully")

        return redirect('list-attendance')
    employees = User.objects.filter(role="EMPLOYEE")
    context = {
        'attendance' : attendace,
        'employees' : employees
    }
    return render(request,'attendance/Attendance_edit.html',context)


#Delete Attendance Logic code
@login_required
def delete_attendance(request,pk):
    if request.user.role != "ADMIN":
        return redirect('admin-dashboard')
    
    try:
        attendance = Attendance.objects.get(id = pk)
    except Attendance.DoesNotExist:
        messages.error(request, "Record Not Found")
        return redirect('list-attendance')
    
    attendance.delete()
    messages.success(request, "Deleted Successfully")

    return redirect('list-attendance')


@login_required
def admin_profile(request):
    user = request.user

    if request.method == "POST":
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.address = request.POST.get('address')

        if request.FILES.get('profile_pic'):
            user.profile_pic = request.FILES.get('profile_pic')

        user.save()
        return redirect('admin-profile')
    context = {
        'user' : user
    }
    return render(request, 'profile/Admin_profile.html',context)


@login_required
def admin_profile_edit(request):
    user = request.user
    if user.role != "ADMIN":
        return redirect('user-login')
    
    if request.method == "POST":
       
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        #Validation
        if not first_name or not email:
            messages.error(request,'First Name Email Required')
            return redirect('admin-profile')
        
        #update Field
        
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        user.address = address

        #image Update
        if request.FILES.get('profile_pic'):
            user.profile_pic = request.FILES.get('profile_pic')

            user.save()

            messages.success(request, "Profile Updated Successfully")
            return redirect('admin-profile')
    context = {
            'user' : user
        }
    return render(request,'profile/Admin_profile_edit.html',context)



@login_required
def employee_profile(request):
    user = request.user

    if user.role != "EMPLOYEE":
        return redirect('admin-dashboard')
    
    profile = EmployeeProfile.objects.filter(user=user).first()
    
    
    context = {
        'user' : user,
        'profile' : profile
    }
    return render(request,'profile/Employee_profile.html',context)



@login_required
def employee_profile_edit(request):
    user = request.user

    if user.role != "EMPLOYEE":
        return redirect('admin-dashboard')
    
    profile, created = EmployeeProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.address = request.POST.get('address')

        profile.experience = request.POST.get('experience')

       
        if request.FILES.get('profile_pic'):
            user.profile_pic = request.FILES.get('profile_pic')

        user.save()
        profile.save()

        messages.success(request, 'Profile Updated Successfully')
        return redirect('employee-profile')

    context = {
        'user' : user,
        'profile' : profile
    }
    return render(request, 'profile/Employee_profile_edit.html',context)