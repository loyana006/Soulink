from datetime import date

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    dob = models.DateField(blank=False, default=date(1111, 1, 1))
    address = models.TextField(blank=True, null=True, max_length=50, default="")
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

    def full_name(self):
        return f"{self.first_name} {self.last_name}"
