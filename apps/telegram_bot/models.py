"""
Telegram bot settings model for Suwi.
Uses singleton pattern - only one settings instance allowed.
"""

from django.db import models
from django.core.cache import cache


class TelegramSettings(models.Model):
    """
    Singleton model for Telegram bot settings.
    Only one instance of this model should exist.
    """

    bot_token = models.CharField(
        'Bot Token',
        max_length=100,
        help_text='Токен бота от @BotFather'
    )

    chat_id = models.CharField(
        'Chat ID ресторана',
        max_length=50,
        help_text='ID группы/чата для уведомлений о заказах'
    )

    is_active = models.BooleanField(
        'Активен',
        default=True,
        help_text='Отправлять уведомления в Telegram'
    )

    # Optional: notify customer via Telegram
    notify_customer = models.BooleanField(
        'Уведомлять клиента',
        default=False,
        help_text='Отправлять уведомления клиентам о статусе заказа'
    )

    # Welcome message for customers
    welcome_message = models.TextField(
        'Приветственное сообщение',
        blank=True,
        default='Добро пожаловать в Suwi! Здесь вы будете получать уведомления о статусе ваших заказов.',
        help_text='Сообщение при подключении клиента к уведомлениям'
    )

    updated_at = models.DateTimeField(
        'Обновлено',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Настройки Telegram'
        verbose_name_plural = 'Настройки Telegram'

    def __str__(self):
        status = 'активен' if self.is_active else 'неактивен'
        return f'Telegram бот ({status})'

    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton)
        self.pk = 1
        super().save(*args, **kwargs)
        # Clear cache when settings are updated
        cache.delete('telegram_settings')

    def delete(self, *args, **kwargs):
        # Prevent deletion of singleton
        pass

    @classmethod
    def load(cls):
        """
        Load settings from database or cache.
        Creates default instance if none exists.
        """
        # Try to get from cache first
        settings = cache.get('telegram_settings')
        if settings is None:
            settings, created = cls.objects.get_or_create(
                pk=1,
                defaults={
                    'bot_token': '',
                    'chat_id': '',
                    'is_active': False,
                }
            )
            # Cache for 5 minutes
            cache.set('telegram_settings', settings, 300)
        return settings

    @classmethod
    def get_bot_token(cls):
        """Get bot token from settings."""
        return cls.load().bot_token

    @classmethod
    def get_chat_id(cls):
        """Get restaurant chat ID from settings."""
        return cls.load().chat_id

    @classmethod
    def is_enabled(cls):
        """Check if Telegram notifications are enabled."""
        settings = cls.load()
        return settings.is_active and settings.bot_token and settings.chat_id
