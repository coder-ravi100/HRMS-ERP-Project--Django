from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

# Create your views here.
def login(request):
    return render(request,'accounts/login,html')



def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request,username=username,password=password)

        if user:

            login(request,user)

            if user.role == "ADMIN":
                return redirect("admin_dashboard")

            if user.role == "HR":
                return redirect("hr_dashboard")

            if user.role == "MANAGER":
                return redirect("manager_dashboard")

            if user.role == "EMPLOYEE":
                return redirect("employee_dashboard")

    return render(request,"login.html")