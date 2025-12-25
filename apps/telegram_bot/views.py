"""
Telegram webhook views for Suwi.
"""

import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone

from apps.orders.models import Order
from .models import TelegramSettings
from .services import (
    TelegramBot,
    update_order_notification,
    send_customer_notification,
    get_customer_status_message,
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    """
    Telegram webhook endpoint.
    Receives updates from Telegram and processes them.
    """

    def post(self, request):
        """Process incoming webhook update."""
        try:
            data = json.loads(request.body)
            logger.debug(f'Telegram webhook data: {data}')

            # Process callback query (button clicks)
            if 'callback_query' in data:
                self.process_callback(data['callback_query'])

            # Process regular messages (optional: for customer linking)
            elif 'message' in data:
                self.process_message(data['message'])

            return HttpResponse('OK')

        except json.JSONDecodeError:
            logger.error('Invalid JSON in webhook')
            return HttpResponse('Invalid JSON', status=400)

        except Exception as e:
            logger.error(f'Webhook error: {e}')
            return HttpResponse('Error', status=500)

    def process_callback(self, callback_query):
        """
        Process callback query from inline button.
        Format: order_{order_id}_{new_status}
        """
        bot = TelegramBot()
        callback_id = callback_query['id']
        data = callback_query.get('data', '')

        # Parse callback data
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

        # Get order
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
            'confirmed': 'подтверждён',
            'cooking': 'готовится',
            'delivering': 'в доставке',
            'delivered': 'доставлен',
            'cancelled': 'отменён',
        }

        bot.answer_callback(
            callback_id,
            f'Заказ #{order.pk} {status_names.get(new_status, new_status)}!'
        )

    def process_message(self, message):
        """
        Process regular message.
        Used for customer linking via /start command.
        """
        text = message.get('text', '')
        chat_id = message['chat']['id']

        if text.startswith('/start'):
            # Check for deep link parameter
            parts = text.split()
            if len(parts) > 1:
                # Deep link: /start link_<customer_id>
                param = parts[1]
                if param.startswith('link_'):
                    self.link_customer(chat_id, param[5:], message)
                    return

            # Regular /start - send welcome message
            self.send_welcome(chat_id)

    def link_customer(self, chat_id, customer_id, message):
        """Link customer's Telegram account for notifications."""
        from apps.accounts.models import Customer

        bot = TelegramBot()

        try:
            customer = Customer.objects.get(pk=int(customer_id))
            customer.telegram_chat_id = str(chat_id)
            customer.save(update_fields=['telegram_chat_id'])

            bot.send_message(
                chat_id,
                f'✅ Telegram успешно привязан!\n\n'
                f'Теперь вы будете получать уведомления о статусе заказов, '
                f'{customer.first_name or "уважаемый клиент"}.'
            )

        except (Customer.DoesNotExist, ValueError):
            bot.send_message(
                chat_id,
                '❌ Не удалось привязать аккаунт. Попробуйте ещё раз.'
            )

    def send_welcome(self, chat_id):
        """Send welcome message to new user."""
        bot = TelegramBot()
        settings = TelegramSettings.load()

        welcome_text = settings.welcome_message or (
            '🍣 Добро пожаловать в Suwi!\n\n'
            'Здесь вы будете получать уведомления о статусе ваших заказов.'
        )

        bot.send_message(chat_id, welcome_text)


class SetWebhookView(View):
    """
    Utility view to set up Telegram webhook.
    Should be called once after deployment.
    """

    def get(self, request):
        """Set up webhook URL."""
        settings = TelegramSettings.load()

        if not settings.bot_token:
            return JsonResponse({
                'success': False,
                'error': 'Bot token not configured'
            })

        # Build webhook URL
        webhook_url = request.build_absolute_uri('/telegram/webhook/')

        # Set webhook via Telegram API
        api_url = f'https://api.telegram.org/bot{settings.bot_token}/setWebhook'

        import requests
        try:
            response = requests.post(api_url, json={
                'url': webhook_url,
                'allowed_updates': ['message', 'callback_query']
            }, timeout=10)

            result = response.json()

            return JsonResponse({
                'success': result.get('ok', False),
                'webhook_url': webhook_url,
                'result': result
            })

        except requests.RequestException as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
