"""
Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Customer, SavedAddress


class SavedAddressInline(admin.TabularInline):
    """Inline for saved addresses in customer admin."""
    model = SavedAddress
    extra = 0
    fields = ('name', 'custom_name', 'address', 'is_default')
    readonly_fields = ('created_at',)


@admin.register(Customer)
class CustomerAdmin(UserAdmin):
    """Admin for Customer model."""

    # List display
    list_display = ('phone', 'first_name', 'last_name', 'bonus_balance', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('phone', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)

    # Fieldsets for edit page
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        (_('Личные данные'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Telegram'), {'fields': ('telegram_chat_id',)}),
        (_('Бонусы'), {'fields': ('bonus_balance',)}),
        (_('Права доступа'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('Важные даты'), {'fields': ('last_login', 'date_joined')}),
    )

    # Fieldsets for add page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'first_name', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login')
    inlines = [SavedAddressInline]


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    """Admin for SavedAddress model."""

    list_display = ('customer', 'name', 'address', 'is_default', 'created_at')
    list_filter = ('name', 'is_default')
    search_fields = ('customer__phone', 'customer__first_name', 'address')
    raw_id_fields = ('customer',)
