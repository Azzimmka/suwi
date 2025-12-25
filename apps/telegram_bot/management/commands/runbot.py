"""
Management command to run Telegram bot in polling mode.
Use this for local development when webhook is not available.
"""

import time
import logging
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import Order
from apps.telegram_bot.models import TelegramSettings
from apps.telegram_bot.services import (
    TelegramBot,
    update_order_notification,
    send_customer_notification,
    get_customer_status_message,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run Telegram bot in polling mode (for local development)'

    def __init__(self):
        super().__init__()
        self.last_update_id = 0

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🤖 Запуск Telegram бота в режиме polling...'))

        settings = TelegramSettings.load()
        if not settings.bot_token:
            self.stdout.write(self.style.ERROR('❌ Токен бота не настроен!'))
            return

        # Delete webhook to use polling
        self.delete_webhook(settings.bot_token)

        self.stdout.write(self.style.SUCCESS('✅ Бот запущен! Нажмите Ctrl+C для остановки.'))

        while True:
            try:
                self.poll_updates(settings.bot_token)
                time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\n👋 Бот остановлен.'))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
                time.sleep(5)

    def delete_webhook(self, token):
        """Delete webhook to enable polling."""
        url = f'https://api.telegram.org/bot{token}/deleteWebhook'
        try:
            requests.post(url, timeout=10)
        except:
            pass

    def poll_updates(self, token):
        """Poll for new updates."""
        url = f'https://api.telegram.org/bot{token}/getUpdates'
        params = {
            'offset': self.last_update_id + 1,
            'timeout': 30,
            'allowed_updates': ['message', 'callback_query']
        }

        try:
            response = requests.get(url, params=params, timeout=35)
            data = response.json()

            if not data.get('ok'):
                return

            for update in data.get('result', []):
                self.last_update_id = update['update_id']
                self.process_update(update)

        except requests.Timeout:
            pass
        except requests.RequestException as e:
            logger.error(f'Polling error: {e}')

    def process_update(self, update):
        """Process a single update."""
        if 'callback_query' in update:
            self.process_callback(update['callback_query'])
        elif 'message' in update:
            self.process_message(update['message'])

    def process_callback(self, callback_query):
        """Process callback query from inline button."""
        bot = TelegramBot()
        callback_id = callback_query['id']
        data = callback_query.get('data', '')

        self.stdout.write(f'📲 Callback: {data}')

        if not data.startswith('order_'):
            bot.answer_callback(callback_id, 'Неизвестная команда')
            return

        try:
            parts = data.split('_')
            order_id = int(parts[1])
            new_status = parts[2]
        except (IndexError, ValueError):
            bot.answer_callback(callback_id, 'Неверный формат данных')
            return

        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            bot.answer_callback(callback_id, 'Заказ не найден')
            return

        # Validate status transition
        valid_transitions = {
            'new': ['confirmed', 'cancelled'],
            'confirmed': ['cooking', 'cancelled'],
            'cooking': ['delivering', 'cancelled'],
            'delivering': ['delivered', 'cancelled'],
        }

        if new_status not in valid_transitions.get(order.status, []):
            bot.answer_callback(
                callback_id,
                f'Невозможно изменить статус с "{order.get_status_display()}"',
                show_alert=True
            )
            return

        # Update order status
        old_status = order.get_status_display()
        order.status = new_status

        if new_status == 'confirmed':
            order.confirmed_at = timezone.now()
        elif new_status == 'delivered':
            order.delivered_at = timezone.now()

        order.save()

        # Update Telegram message
        update_order_notification(order)

        # Send notification to customer
        customer_message = get_customer_status_message(order)
        if customer_message:
            send_customer_notification(order, customer_message)

        # Answer callback
        status_names = {
            'confirmed': 'подтверждён ✅',
            'cooking': 'готовится 👨‍🍳',
            'delivering': 'в доставке 🚗',
            'delivered': 'доставлен ✔️',
            'cancelled': 'отменён ❌',
        }

        status_text = status_names.get(new_status, new_status)
        bot.answer_callback(callback_id, f'Заказ #{order.pk} {status_text}')

        self.stdout.write(
            self.style.SUCCESS(f'✅ Заказ #{order.pk}: {old_status} → {order.get_status_display()}')
        )

    def process_message(self, message):
        """Process regular message."""
        text = message.get('text', '')
        chat_id = message['chat']['id']
        username = message['from'].get('username', 'unknown')

        self.stdout.write(f'💬 Сообщение от @{username}: {text}')

        if text.startswith('/start'):
            bot = TelegramBot()
            settings = TelegramSettings.load()

            welcome_text = settings.welcome_message or (
                '🍣 Добро пожаловать в Суши love! ❤️\n\n'
                'Здесь вы будете получать уведомления о статусе ваших заказов.'
            )

            bot.send_message(chat_id, welcome_text)
