from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("EMPLOYEE", "Employee"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    phone = models.CharField(max_length=15, blank=True)

    address = models.TextField(blank=True)

    email = models.EmailField(unique = True)
    
    profile_pic = models.ImageField(
        upload_to="profile_pics/",
        default="profile_pics/default.png",
        blank=True
    )

    def __str__(self):
        return self.username


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
        null=True,
        blank=True
    )

    designation = models.CharField(max_length=100)


    salary = models.DecimalField(max_digits=10, decimal_places=2)

    join_date = models.DateField(auto_now_add=True)

    experience = models.PositiveIntegerField(
        help_text="Years of experience",
        null=True,
        blank=True
    )

    def __str__(self):
        return self.user.username


class Task(models.Model):

    STATUS = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
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
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tasks"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="Pending"
    )

    due_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.assigned_to.username}"


class Leave(models.Model):

    STATUS = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE)

    start_date = models.DateField()

    end_date = models.DateField()

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="Pending"
    )

    def __str__(self):
        return self.employee.username
    


class Attendance(models.Model):

    STATUS = [
        ("Present", "Present"),
        ("Absent", "Absent"),
        ("Half Day", "Half Day"),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE)

    date = models.DateField(auto_now_add=True)

    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS)

    def __str__(self):
        return f"{self.employee.username} - {self.date}"