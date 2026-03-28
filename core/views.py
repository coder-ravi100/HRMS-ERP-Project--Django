from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from .forms import * #RegistrationForm

from .models import Department, EmployeeProfile, Task, Leave, Attendance
from core.models import User
from django.utils import timezone
from datetime  import timedelta,date
import random

from .utils import *
from django.utils.timezone import localtime,now
from django.db.models  import Count
from .utils import sendmailForOtp
import json
from django.core.paginator import Paginator

# Create your views here.
#---------------------------------------------------------
#           ******ADMIN DASHBOARD SECTION******
#---------------------------------------------------------
@never_cache
@login_required
def admin_dashboard(request):
     if request.user.role != "ADMIN":
        return redirect('employee-dashboard')
     today = date.today()
     week_ago = today - timedelta(days=7)

    # CARDS DATA
     total_employees = User.objects.filter(role="EMPLOYEE").count()
     total_departments = Department.objects.count()
     present_today = Attendance.objects.filter(date=today, status="Present").count()
     pending_tasks = Task.objects.filter(status="Pending").count()

    # LINE CHART (Attendance Trend - last 7 days)
     attendance_data = []
     for i in range(7):
        day = today - timedelta(days=i)
        
        count = Attendance.objects.filter(date=day, status="Present").count() or 0
        
        attendance_data.append({
            "y": day.strftime("%a"),
            "present": count
        })
     attendance_data = attendance_data[::-1]

    # DONUT (Department Distribution)
     dept_data = Department.objects.annotate(total=Count('employeeprofile')).values('name', 'total')
     donut_data = [{"label": d["name"], "value": d["total"]} for d in dept_data]

    # STACKED (Tasks)
     task_data = []
     for i in range(7):
        day = today - timedelta(days=i)
        completed = Task.objects.filter(created_at__date=day, status="Completed").count()
        pending = Task.objects.filter(created_at__date=day, status="Pending").count()

        task_data.append({
            "y": day.strftime("%a"),
            "completed": completed,
            "pending": pending
        })
     task_data = task_data[::-1]

     context = {
        "total_employees": total_employees,
        "total_departments": total_departments,
        "present_today": present_today,
        "pending_tasks": pending_tasks,
        "attendance_data": attendance_data,
        "donut_data": donut_data,
        "task_data": task_data,
        "attendance_data": json.dumps(attendance_data),
        "donut_data": json.dumps(donut_data),
        "task_data": json.dumps(task_data),
        "activity_level" : 85
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

    employee = request.user
    today = date.today()

    # Attendance Chart 
    attendance_data = []
    for i in range(7):
        day = today - timedelta(days=i)

        count = Attendance.objects.filter(
            employee=employee,
            date=day,
            status="Present"
        ).count()

        attendance_data.append({
            "y": day.strftime("%a"),
            "Present": count
        })

    attendance_data = attendance_data[::-1]  

    # Task Data (Donut)
    completed_tasks = Task.objects.filter(
        assigned_to=employee, status="Completed"
    ).count()

    pending_tasks = Task.objects.filter(
        assigned_to=employee, status="Pending"
    ).count()

    task_data = [
        {'label': 'Completed', 'value': completed_tasks},
        {'label': 'Pending', 'value': pending_tasks},
    ]

    # Cards
    present_count = Attendance.objects.filter(employee=employee, status='Present').count()
    absent_count = Attendance.objects.filter(employee=employee, status='Absent').count()

 
    total_tasks = Task.objects.filter(assigned_to=employee).count()
    completed_tasks = Task.objects.filter(assigned_to=employee, status='Completed').count()
    pending_tasks = Task.objects.filter(assigned_to=employee, status='Pending').count()

    total_leaves = Leave.objects.filter(employee=employee).count()
    approved_leaves = Leave.objects.filter(employee=employee, status='Approved').count()
    pending_leaves = Leave.objects.filter(employee=employee, status='Pending').count()

    context = {
        'present_count': present_count,
        'absent_count': absent_count,

        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,

        'total_leaves': total_leaves,
        'approved_leaves': approved_leaves,
        'pending_leaves': pending_leaves,

       
        'attendance_data': json.dumps(attendance_data),
        'task_data': json.dumps(task_data),
    }

    return render(request, 'dashboard/Employee_Dashboard.html',context)


#---------------------------------------------------------
#           ******LOGIN SECTION******
#---------------------------------------------------------
def user_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        #empty validation
        if not email or not password:
            messages.error(request, "All fields are required")
            return redirect('user-login')

        try:
           
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            messages.error(request, "User not found")
            return redirect('user-login')

        #password check
        if not user.check_password(password):
            messages.error(request, "Wrong password")
            return redirect('user-login')

        
        login(request, user)

        next_url = request.GET.get('next')

        if user.role == "ADMIN":
            return redirect(next_url or 'admin-dashboard')
        else:
            return redirect(next_url or 'employee-dashboard')

    return render(request, 'authentication/Login.html')



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

        Department.objects.create(
            name = dep_name,
            description = dep_description
        )
        
        messages.success(request, "Department Added Successfully")
        return redirect('list_department')
    
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
    try:
        d_id = Department.objects.get(id = pk)
    except Department.DoesNotExist:
        messages.error(request,"Department Not Found")
    
    if request.method == "POST":
        d_id.name = request.POST['name']
        d_id.description = request.POST['description']
        d_id.save()

        messages.success(request,"Department Updated Successfully")
       
        return redirect('list_department')
    context = {
        'd_id' : d_id
    }
    return render(request,'department/Department_edit.html',context)

#Delete Department Bussiness Logic Code
def delete_department(request,pk):
   try:
       d_id = Department.objects.get(id = pk)
       d_id.delete()
       messages.success(request,'Department  Depeted Successfully')
    
   except Department.DoesNotExist:
       messages.error(request,'Department Not Found')
    
   return redirect('list_department')
   

#---------------------------------------------------------
#           ******EMPLOYEE SECTION******
#---------------------------------------------------------

#Create Employee Bussiness Logic Code
def add_employee(request):
    departments = Department.objects.all()

    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        role = request.POST['role']
        phone = request.POST['phone']
        address = request.POST['address']
        profile_pic = request.FILES.get('profile_pic')

        username = first_name.lower() + last_name.lower()
        password = first_name[:2] + email[:3] + "123"

        department = Department.objects.get(id=request.POST['department'])

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

        EmployeeProfile.objects.create(
            user=user,
            department=department,
            designation=request.POST['designation'],
            salary=request.POST['salary'],
            join_date=request.POST['join_date'],
            experience=request.POST['experience']
        )

        print("Employee Password:", password)
        messages.success(request, "Employee added successfully")
        return redirect('list-employee')

    #Paginator Logic Code  
    employees = EmployeeProfile.objects.all()
    paginator = Paginator(employees, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'departments': departments,
        'page_obj': page_obj
    }
    return render(request, 'employee/Employee_add.html', context)

#List Employee Bussiness Logic  Code
def list_employee(request):
    # employees = EmployeeProfile.objects.select_related('user','department')
    
    #Paginator Logic Code  
    employees = EmployeeProfile.objects.all().order_by('id')
    paginator = Paginator(employees, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

        
    context = {
        'employees' : employees,
        'page_obj': page_obj
    }
    
    return render(request,'employee/Employee_list.html',context)



#Update Employee Bussiness Logic  Code
def edit_employee(request, pk):
    emp = EmployeeProfile.objects.get(id=pk)
    departments = Department.objects.all()

    if request.method == "POST":
        emp.user.first_name = request.POST['first_name']
        emp.user.last_name = request.POST['last_name']
        emp.user.email = request.POST['email']
        emp.user.phone = request.POST['phone']
        emp.user.address = request.POST['address']

        profile_pic = request.FILES.get('profile_pic')
        if profile_pic:
            emp.user.profile_pic = profile_pic

        emp.user.save()

        emp.department = Department.objects.get(id=request.POST['department'])
        emp.designation = request.POST['designation']
        emp.salary = request.POST['salary']
        emp.experience = request.POST['experience']

        if request.POST.get('join_date'):
            emp.join_date = request.POST['join_date']

        emp.save()

        messages.success(request, "Employee updated successfully")
        return redirect('list-employee')

    context = {
        'emp' : emp,
        'dep_id' : departments
    }
    return render(request, 'employee/Employee_edit.html',context)


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

    messages.success(request,"Employee Deleted Successfully")
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
        messages.success(request,"Task Added Successfully")
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
        
        messages.success(request,"Task Updated Successfully")
        return redirect('list-task')
    
    context = {
        'tasks' : tasks,
        'employees' : employees
    }
    
    return render(request,'tasks/Task_edit.html',context)
    

#Delete Task Bussiness Logic  Code  
def task_delete(request,pk):
    tasks = Task.objects.get(id=pk)
    tasks.delete()

    messages.error(request,"Task  Deleted Successfully")
    return redirect('list-task')



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
    
    messages.success(request,"Task Marked As Completed")
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
        messages.success(request,"Leave Applied Successfully")
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

        if status in ["Pending","Approved", "Rejected"]:
            leave.status = status
            leave.save()
            
            messages.success(request,f"Leave {status.lower()} Successfully")
        else:
            messages.error(request,"Invalid Status")

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

#---------------------------------------------------------
#           ******ADMIN PROFILE SECTION******
#---------------------------------------------------------
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
        messages.success(request,"Profile Added Successfully")
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


#---------------------------------------------------------
#           ******EMPLOYEE PROFILE SECTION******
#---------------------------------------------------------
@login_required
def employee_profile(request):
    user = request.user

    if user.role != "EMPLOYEE":
        messages.success(request,"Profile Added Successfully")
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