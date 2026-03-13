from django.shortcuts import render, redirect,get_object_or_404
from .models  import *

# Create your views here.
def admin_dashboard(request):
    return render(request,'dashboard/Admin_Dashboard.html')



def add_department(request):
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get("description")

        Department.objects.create(name=name,description=description)
        
        deparment = Department.objects.all()
        contaxt = {'department' : deparment}
        return render(request,'department/Department_list.html',contaxt)
    
    return render(request,'department/Department_add.html')



def list_department(request):
     department = Department.objects.all()
     
     contaxt = {'department' : department}
     return render(request,'department/Department_list.html',contaxt)



def edit_department(request, pk):
    department = get_object_or_404(Department, id=pk)

    if request.method == "POST":
        department.name = request.POST["name"]
        department.description = request.POST["description"]
        department.save()

        return redirect('list_department')

    context = {'department': department}
    return render(request,'department/Department_edit.html',context)


def delete_department(request,pk):
    department = get_object_or_404(Department,id=pk)
    
    department.delete()

    return redirect('list_Department')