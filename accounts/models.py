from django.db import models
from django.contrib.auth.models import AbstractUser


class MyUsers(AbstractUser):
    """
    Custom user model with additional fields.
    Inherits from the Django AbstractUser model.
    """
    bio = models.TextField(max_length=300, null=True, blank=True)
    picture = models.ImageField(
        upload_to="profile/%Y/%m/%d", null=True, blank=True)

