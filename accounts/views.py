from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import User  # sirf User model, extra role models nahi

# ---------- LOGIN VIEW ----------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            role = user.role.upper() if user.role else ""

            if role == "ADMIN" or user.is_superuser:
                return redirect('admin_dashboard')
            elif role == "HR":
                return redirect('hr_dashboard')
            elif role == "MANAGER":
                return redirect('manager_dashboard')
            elif role == "EMPLOYEE":
                return redirect('employee_dashboard')
            else:
                messages.error(request, "Your role is not assigned properly")
                logout(request)
                return redirect('login')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'accounts/login.html')


# ---------- DASHBOARD VIEWS ----------
@login_required(login_url='login')
def admin_dashboard(request):
    if not (request.user.role.upper() == "ADMIN" or request.user.is_superuser):
        return redirect('login')
    return render(request, "dashboard/admin_dashboard.html", {'user': request.user})


@login_required(login_url='login')
def hr_dashboard(request):
    if request.user.role.upper() != "HR":
        return redirect('login')
    return render(request, "dashboard/hr_dashboard.html", {'user': request.user})


@login_required(login_url='login')
def manager_dashboard(request):
    if request.user.role.upper() != "MANAGER":
        return redirect('login')
    return render(request, "dashboard/manager_dashboard.html", {'user': request.user})


@login_required(login_url='login')
def employee_dashboard(request):
    if request.user.role.upper() != "EMPLOYEE":
        return redirect('login')
    return render(request, "dashboard/employee_dashboard.html", {'user': request.user})


# ---------- LOGOUT VIEW ----------
@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')