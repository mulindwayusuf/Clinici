from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import os

def user_profile_pic_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/profile_pics/user_<id>/<filename>
    return f'profile_pics/user_{instance.user.id}/{filename}'

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'Admin')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        from .models import Employee
        employee = Employee.objects.create(
            name=username + " Employee",
            job_title="Administrator",
            salary=0,  # Now interpreted as USh (was $0.00)
            hire_date=timezone.now().date()
        )
        extra_fields['employee'] = employee
        return self.create_user(username, password, **extra_fields)

class Medicine(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in USh")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in USh")
    expiration_date = models.DateField()
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class StockTransaction(models.Model):
    TRANSACTION_TYPES = (('Intake', 'Intake'), ('Sale', 'Sale'), ('Discard', 'Discard'))
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    transaction_date = models.DateTimeField(default=timezone.now)
    employee = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True)
    sale_item = models.ForeignKey('SaleItem', on_delete=models.SET_NULL, null=True, blank=True)
 
    def __str__(self):
        return f"{self.transaction_type} - {self.medicine.name}"

class Sale(models.Model):
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total in USh")
    sale_date = models.DateTimeField(default=timezone.now)
    receipt_generated = models.BooleanField(default=False)

    def __str__(self):
        return f"Sale {self.id} - USh {self.total_amount}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, help_text="Subtotal in USh")

    def __str__(self):
        return f"{self.medicine.name} x{self.quantity}"

class Employee(models.Model):
    name = models.CharField(max_length=100)
    job_title = models.CharField(max_length=50)
    salary = models.DecimalField(max_digits=10, decimal_places=2, help_text="Salary in USh")
    contact_info = models.CharField(max_length=100, null=True, blank=True)
    hire_date = models.DateField()
    profile_picture = models.ImageField(upload_to=user_profile_pic_path, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Delete old profile picture if it exists and new one is uploaded
        try:
            old = Employee.objects.get(pk=self.pk)
            if old.profile_picture and old.profile_picture != self.profile_picture:
                if os.path.isfile(old.profile_picture.path):
                    os.remove(old.profile_picture.path)
        except Employee.DoesNotExist:
            pass
        super().save(*args, **kwargs)

class Attendance(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.employee.name} - {self.date}"

    class Meta:
        unique_together = ('employee', 'date')

class User(AbstractBaseUser, PermissionsMixin):
    ROLES = (('Admin', 'Admin'), ('Employee', 'Employee'))
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    username = models.CharField(max_length=50, unique=True)
    role = models.CharField(max_length=10, choices=ROLES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['role']

    def __str__(self):
        return self.username

class Notification(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    message = models.TextField()
    date_sent = models.DateTimeField(default=timezone.now)
    acknowledged = models.BooleanField(default=False)

    def __str__(self):
        return self.message