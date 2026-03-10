from django.db import models
from accounts.models import User

# Create your models here.
class Department(models.Model):

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name



class EmployeeProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True
    )

    designation = models.CharField(max_length=100)

    phone = models.CharField(max_length=15)

    salary = models.DecimalField(max_digits=10, decimal_places=2)

    join_date = models.DateField()

    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="team_members"
    )

    def __str__(self):
        return str(self.user)
    


class Leave(models.Model):

    STATUS = [
        ("Pending","Pending"),
        ("Approved","Approved"),
        ("Rejected","Rejected")
    ]

    employee = models.ForeignKey(User,on_delete=models.CASCADE)

    leave_type = models.CharField(max_length=50)

    start_date = models.DateField()

    end_date = models.DateField()

    reason = models.TextField()

    status = models.CharField(max_length=20,choices=STATUS,default="Pending")

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leave"
    )

    def __str__(self):
        return f"{self.employee} - {self.status}"
    


class Task(models.Model):

    STATUS = [
        ("Pending","Pending"),
        ("In Progress","In Progress"),
        ("Completed","Completed")
    ]

    PRIORITY = [
        ("Low","Low"),
        ("Medium","Medium"),
        ("High","High")
    ]

    title = models.CharField(max_length=200)

    description = models.TextField()

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    assigned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_tasks"
    )

    priority = models.CharField(max_length=20,choices=PRIORITY)

    status = models.CharField(max_length=20,choices=STATUS,default="Pending")

    due_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title