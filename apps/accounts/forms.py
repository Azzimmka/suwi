"""
Authentication forms for Suwi.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator

from .models import Customer


class PhoneInput(forms.TextInput):
    """Custom phone input widget with formatting."""
    input_type = 'tel'

    def __init__(self, attrs=None):
        default_attrs = {
            'placeholder': '+998 XX XXX XX XX',
            'autocomplete': 'tel',
            'inputmode': 'tel',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class CustomerRegistrationForm(UserCreationForm):
    """
    Registration form for new customers.
    Uses phone number instead of username.
    """

    phone = forms.CharField(
        label='Номер телефона',
        max_length=20,
        widget=PhoneInput(attrs={
            'class': 'form-input',
            'autofocus': True,
        }),
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9\s\-]{10,20}$',
                message='Введите корректный номер телефона'
            )
        ],
        help_text='Формат: +998901234567'
    )

    first_name = forms.CharField(
        label='Имя',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ваше имя',
            'autocomplete': 'given-name',
        })
    )

    password1 = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'autocomplete': 'new-password',
            'placeholder': 'Минимум 6 символов',
        }),
    )

    password2 = forms.CharField(
        label='Подтверждение пароля',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'autocomplete': 'new-password',
            'placeholder': 'Повторите пароль',
        }),
    )

    class Meta:
        model = Customer
        fields = ('phone', 'first_name', 'password1', 'password2')

    def clean_phone(self):
        """Normalize and validate phone number."""
        phone = self.cleaned_data.get('phone')
        # Remove spaces and dashes
        phone = ''.join(filter(lambda x: x.isdigit() or x == '+', phone))

        # Check if phone already exists
        if Customer.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                'Пользователь с таким номером телефона уже зарегистрирован'
            )

        return phone

    def save(self, commit=True):
        """Save the user with normalized phone number."""
        user = super().save(commit=False)
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user


class CustomerLoginForm(forms.Form):
    """
    Login form using phone number and password.
    """

    phone = forms.CharField(
        label='Номер телефона',
        max_length=20,
        widget=PhoneInput(attrs={
            'class': 'form-input',
            'autofocus': True,
        })
    )

    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'autocomplete': 'current-password',
        })
    )

    remember_me = forms.BooleanField(
        label='Запомнить меня',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox',
        })
    )

    error_messages = {
        'invalid_login': 'Неверный номер телефона или пароль.',
        'inactive': 'Этот аккаунт деактивирован.',
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validate credentials and authenticate user."""
        phone = self.cleaned_data.get('phone')
        password = self.cleaned_data.get('password')

        if phone and password:
            # Normalize phone
            phone = ''.join(filter(lambda x: x.isdigit() or x == '+', phone))

            self.user_cache = authenticate(
                self.request,
                phone=phone,
                password=password
            )

            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                )

            if not self.user_cache.is_active:
                raise forms.ValidationError(
                    self.error_messages['inactive'],
                    code='inactive',
                )

        return self.cleaned_data

    def get_user(self):
        """Return the authenticated user."""
        return self.user_cache


class CustomerProfileForm(forms.ModelForm):
    """
    Form for updating customer profile.
    """

    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Имя',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Фамилия',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'email@example.com',
            }),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }
