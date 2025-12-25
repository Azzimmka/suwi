"""
Custom user model and related models for Suwi.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator


class CustomerManager(BaseUserManager):
    """
    Custom manager for Customer model.
    Uses phone number as the unique identifier.
    """

    def create_user(self, phone, password=None, **extra_fields):
        """
        Create and return a regular user with phone and password.
        """
        if not phone:
            raise ValueError('Номер телефона обязателен')

        # Normalize phone number (remove spaces, dashes)
        phone = self.normalize_phone(phone)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        """
        Create and return a superuser with phone and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone, password, **extra_fields)

    @staticmethod
    def normalize_phone(phone):
        """
        Normalize phone number by removing spaces and dashes.
        """
        return ''.join(filter(lambda x: x.isdigit() or x == '+', phone))


class Customer(AbstractUser):
    """
    Custom user model that uses phone number instead of username.
    """

    # Phone number validator
    phone_validator = RegexValidator(
        regex=r'^\+?[0-9]{10,15}$',
        message='Введите корректный номер телефона (10-15 цифр)'
    )

    # Remove username field, use phone as identifier
    username = None
    phone = models.CharField(
        'Номер телефона',
        max_length=20,
        unique=True,
        validators=[phone_validator],
        help_text='Формат: +998901234567'
    )

    # Additional fields
    telegram_chat_id = models.CharField(
        'Telegram Chat ID',
        max_length=50,
        blank=True,
        help_text='ID чата для уведомлений клиенту'
    )

    bonus_balance = models.PositiveIntegerField(
        'Бонусный баланс',
        default=0,
        help_text='Бонусные баллы клиента'
    )

    # Override email to make it optional
    email = models.EmailField('Email', blank=True)

    # Use phone as the username field
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []  # No additional required fields for createsuperuser

    objects = CustomerManager()

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-date_joined']

    def __str__(self):
        if self.first_name:
            return f'{self.first_name} ({self.phone})'
        return self.phone

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name if full_name else self.phone

    def get_short_name(self):
        """
        Return the short name for the user.
        """
        return self.first_name if self.first_name else self.phone


class SavedAddress(models.Model):
    """
    Saved delivery addresses for customers.
    """

    NAME_CHOICES = [
        ('home', 'Дом'),
        ('work', 'Работа'),
        ('other', 'Другое'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='saved_addresses',
        verbose_name='Клиент'
    )

    name = models.CharField(
        'Название',
        max_length=50,
        choices=NAME_CHOICES,
        default='home'
    )

    custom_name = models.CharField(
        'Своё название',
        max_length=100,
        blank=True,
        help_text='Если выбрано "Другое"'
    )

    address = models.TextField(
        'Адрес',
        help_text='Полный адрес доставки'
    )

    latitude = models.DecimalField(
        'Широта',
        max_digits=9,
        decimal_places=6
    )

    longitude = models.DecimalField(
        'Долгота',
        max_digits=9,
        decimal_places=6
    )

    is_default = models.BooleanField(
        'По умолчанию',
        default=False,
        help_text='Использовать этот адрес по умолчанию'
    )

    created_at = models.DateTimeField(
        'Создан',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Сохранённый адрес'
        verbose_name_plural = 'Сохранённые адреса'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        display_name = self.custom_name if self.name == 'other' else self.get_name_display()
        return f'{display_name}: {self.address[:50]}'

    def save(self, *args, **kwargs):
        # If this address is set as default, remove default from other addresses
        if self.is_default:
            SavedAddress.objects.filter(
                customer=self.customer,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
