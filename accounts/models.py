from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


ROLES = [
    ('Student', 'Student'),
    ('Counsellor', 'Counsellor'),
    ('Admin', 'Admin'),
]


class UserManager(BaseUserManager):
    def create_user(self, email, name, role, password=None):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            role=role,
        )

        user.set_password(password)
        # Keep Django admin access aligned with app-level Admin role.
        if role == 'Admin':
            user.is_staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, role, password=None):
        user = self.create_user(
            email=email,
            name=name,
            role=role,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLES)
    anonymous_flag = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Risk engine fields (do not remove; used by risk_engine.py)
    risk_score = models.IntegerField(default=0)
    current_stress_level = models.CharField(max_length=10, default='Low')
    is_flagged_high = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'role']

    def __str__(self):
        return self.email
