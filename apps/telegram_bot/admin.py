"""
Admin configuration for telegram_bot app.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import TelegramSettings
from .services import TelegramBot


@admin.register(TelegramSettings)
class TelegramSettingsAdmin(admin.ModelAdmin):
    """Admin for TelegramSettings model (singleton)."""

    list_display = ('__str__', 'is_active', 'notify_customer', 'updated_at', 'test_connection')
    readonly_fields = ('updated_at', 'test_connection')

    fieldsets = (
        ('Основные настройки', {
            'fields': ('bot_token', 'chat_id', 'is_active')
        }),
        ('Уведомления клиентам', {
            'fields': ('notify_customer', 'welcome_message'),
            'classes': ('collapse',),
        }),
        ('Информация', {
            'fields': ('updated_at', 'test_connection'),
        }),
    )

    def has_add_permission(self, request):
        # Only one instance allowed (singleton)
        return not TelegramSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of singleton
        return False

    def test_connection(self, obj):
        """Test Telegram bot connection."""
        if not obj or not obj.bot_token:
            return format_html(
                '<span style="color: #999;">Токен не настроен</span>'
            )

        bot = TelegramBot()
        result = bot._make_request('getMe')

        if result:
            bot_name = result.get('username', 'Unknown')
            return format_html(
                '<span style="color: green;">✅ Подключён: @{}</span>',
                bot_name
            )
        else:
            return format_html(
                '<span style="color: red;">❌ Ошибка подключения</span>'
            )

    test_connection.short_description = 'Статус подключения'

    def save_model(self, request, obj, form, change):
        """Clear cache when saving."""
        super().save_model(request, obj, form, change)
        from django.core.cache import cache
        cache.delete('telegram_settings')
