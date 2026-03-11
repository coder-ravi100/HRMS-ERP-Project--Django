from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

# Create your views here.
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request,username = username , password = password)

        if user is not None:
            
            login(request, user)

            role = user.role
            print(type(user.role))
            print(user.role)

            if role == "ADMIN":
                return redirect("admin_dashboard")
            
            elif role == "HR":
                return redirect("hr_dashboard")
            
            elif role == "MANAGER":
                return redirect("manager_dashboard")
            
            elif role == "EMPLOYEE":
                return redirect("employee_dashboard")
        
        else:
            messages.error(request, "Invalid Username or password")


    return render(request,'accounts/login.html')


def admin_dashboard(request):
    return render(request,"dashboard/admin_dashboard.html")


def hr_dashboard(request):
    return render(request, "dashboard/hr_dashboard.html")


def manager_dashboard(request):
    return render(request, "dashboard/manager_dashboard.html")


def employee_dashboard(request):
    return render(request, "dashboard/employee_dashboard.html")
