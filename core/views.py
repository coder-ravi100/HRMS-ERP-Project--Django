from django.shortcuts import render
from .models  import *

# Create your views here.
def admin_dashboard(request):
    return render(request,'dashboard/Admin_Dashboard.html')



def add_department(request):
    if request.POST:
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



def list_department(request):
     d_all = Department.objects.all()
     contaxt = {
         'd_all' : d_all
     }
     return render(request,'department/Department_list.html',contaxt)



def edit_department(request, pk):
    if request.POST:
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