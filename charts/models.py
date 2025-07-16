from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Meta:
        db_table = 'USERS'  # table name
    
    # Custom fields
    firstname = models.CharField(_('first name'), max_length=100)
    lastname = models.CharField(_('last name'), max_length=100)
    age = models.IntegerField(
        _('age'),
        help_text=_('User age must be 18 or older.'),
    )
    is_admin = models.BooleanField(
        _('admin status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )

    
    # Required fields for createsuperuser command
    REQUIRED_FIELDS = ['email', 'firstname', 'lastname', 'age']
    
    @property
    def is_staff(self):
        """Is the user a staff member (admin)?"""
        return self.is_admin
    
    @property
    def is_superuser(self):
        """For simplicity, we'll treat admins as superusers"""
        return self.is_admin
    
    def __str__(self):
        return self.username
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        return f"{self.firstname} {self.lastname}".strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.firstname

from django.db import models

class Ticker(models.Model):
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=10, choices=[
        ('STOCK', 'Stock'),
        ('ETF', 'ETF'),
        ('CRYPTO', 'Cryptocurrency')
    ])
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"