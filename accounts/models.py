from django.db import models
from django.contrib.auth.models import User

# ================= Student List =================
class Student_list(models.Model):
    registration_number = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100)
    is_registered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.registration_number} - {self.full_name}"


# ================= Voter Profile =================
class Voter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student = models.OneToOneField(Student_list, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.student.full_name
