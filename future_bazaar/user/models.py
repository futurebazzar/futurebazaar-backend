from django.contrib.auth.models import AbstractUser
from django.db import models


from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and returns a user with an email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and returns a superuser with an email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class UserModel(AbstractUser):
    class Meta:
        db_table = 'user'
    USER_TYPES = [
        ('admin', 'Admin'),
        ('seller', 'Seller'),
        ('end_user', 'End User'),
    ]
    username = None  # Removing the username field
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)
    contact_number = models.CharField(unique=True, max_length=15, blank=False)
    password = models.CharField(max_length=50, blank=False)
    is_active = models.BooleanField(default=True)
    profile_photo = models.BinaryField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='end_user')

    # Avoid conflicts with Django's built-in User model
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',
        blank=True,
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.'
    )

    USERNAME_FIELD = 'email'  # Email is now the unique identifier for authentication
    REQUIRED_FIELDS = ['first_name', 'last_name', 'contact_number']

        # Set the custom manager
    objects = CustomUserManager()


    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"

    
class Seller(models.Model):
    class Meta:
        db_table = 'seller'
    CATEGORY = [
        ('electronic', 'electronic'),
        ('furniture', 'furniture'),
    ]
    seller_id = models.AutoField(primary_key=True)
    user_id = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name='seller_profile')
    business_name = models.CharField(max_length=100)
    business_address = models.TextField(blank=False)
    business_contact_number = models.CharField(max_length=15, blank=False)
    bussiness_email = models.EmailField(null=True, blank=True)
    seller_category = models.CharField(max_length=100, choices=CATEGORY, default='furniture')
    seller_exclusives = models.TextField(blank=True)
    is_seller_exclusives = models.BooleanField(blank=False)
    shop_description = models.TextField(null=True, blank=True)
    shop_timing_open = models.TimeField(blank=False)
    shop_timing_close = models.TimeField(blank=False)
    shop_location = models.TextField(blank=False)
    geo_location = models.CharField(max_length=255)
    shop_photo = models.BinaryField(blank=False)
    is_approved = models.BooleanField(default=False)
    days_closed = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now_add=True)    
    

    def __str__(self):
        return self.business_name