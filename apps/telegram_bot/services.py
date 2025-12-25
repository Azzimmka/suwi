"""
Telegram bot services for Suwi.
Handles sending notifications and processing callbacks.
"""

import requests
import logging
from django.conf import settings

from .models import TelegramSettings

logger = logging.getLogger(__name__)


class TelegramBot:
    """
    Telegram bot service for sending notifications.
    """

    API_URL = 'https://api.telegram.org/bot{token}/{method}'

    def __init__(self):
        self.settings = TelegramSettings.load()

    @property
    def token(self):
        return self.settings.bot_token

    @property
    def chat_id(self):
        return self.settings.chat_id

    def is_enabled(self):
        """Check if bot is properly configured and enabled."""
        return (
            self.settings.is_active and
            self.token and
            self.chat_id
        )

    def _make_request(self, method, data=None):
        """Make a request to Telegram Bot API."""
        if not self.token:
            logger.warning('Telegram bot token not configured')
            return None

        url = self.API_URL.format(token=self.token, method=method)

        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if not result.get('ok'):
                logger.error(f'Telegram API error: {result.get("description")}')
                return None

            return result.get('result')

        except requests.RequestException as e:
            logger.error(f'Telegram request failed: {e}')
            return None

    def send_message(self, chat_id, text, parse_mode='HTML', reply_markup=None):
        """Send a message to a chat."""
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
        }

        if reply_markup:
            data['reply_markup'] = reply_markup

        return self._make_request('sendMessage', data)

    def edit_message(self, chat_id, message_id, text, parse_mode='HTML', reply_markup=None):
        """Edit an existing message."""
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': parse_mode,
        }

        if reply_markup:
            data['reply_markup'] = reply_markup

        return self._make_request('editMessageText', data)

    def answer_callback(self, callback_query_id, text=None, show_alert=False):
        """Answer a callback query."""
        data = {
            'callback_query_id': callback_query_id,
        }

        if text:
            data['text'] = text
            data['show_alert'] = show_alert

        return self._make_request('answerCallbackQuery', data)


def get_order_message(order):
    """
    Generate formatted order message for Telegram.
    """
    status_emoji = {
        'new': '🆕',
        'confirmed': '✅',
        'cooking': '👨‍🍳',
        'delivering': '🚗',
        'delivered': '✔️',
        'cancelled': '❌',
    }

    emoji = status_emoji.get(order.status, '📋')
    status_text = order.get_status_display()

    # Order items
    items_text = '\n'.join([
        f"🍣 {item.product_name} x{item.quantity} — {item.get_total():,.0f} сум"
        for item in order.items.all()
    ])

    # Build message
    message = f"""
{emoji} <b>Заказ #{order.pk}</b> — {status_text}

📍 <b>Адрес:</b> {order.address}
📱 <b>Телефон:</b> {order.phone}

{items_text}

💰 <b>Итого:</b> {order.total:,.0f} сум
"""

    if order.comment:
        message += f"\n💬 <b>Комментарий:</b> {order.comment}"

    message += f"\n\n🕐 {order.created_at.strftime('%d.%m.%Y %H:%M')}"

    return message.strip()


def get_order_keyboard(order):
    """
    Generate inline keyboard for order status management.
    """
    buttons = []

    if order.status == 'new':
        buttons = [
            [
                {'text': '✅ Подтвердить', 'callback_data': f'order_{order.pk}_confirmed'},
                {'text': '❌ Отклонить', 'callback_data': f'order_{order.pk}_cancelled'},
            ]
        ]
    elif order.status == 'confirmed':
        buttons = [
            [{'text': '👨‍🍳 Готовится', 'callback_data': f'order_{order.pk}_cooking'}]
        ]
    elif order.status == 'cooking':
        buttons = [
            [{'text': '🚗 В доставке', 'callback_data': f'order_{order.pk}_delivering'}]
        ]
    elif order.status == 'delivering':
        buttons = [
            [{'text': '✔️ Доставлен', 'callback_data': f'order_{order.pk}_delivered'}]
        ]

    # Add maps buttons for active orders
    if order.status in ['new', 'confirmed', 'cooking', 'delivering']:
        buttons.append([
            {'text': '📍 Карта', 'url': order.get_yandex_maps_url()},
            {'text': '📦 Яндекс Go', 'url': order.get_yandex_go_url()},
        ])

    return {'inline_keyboard': buttons} if buttons else None


def send_order_notification(order):
    """
    Send order notification to restaurant chat.
    Returns message_id if successful.
    """
    bot = TelegramBot()

    if not bot.is_enabled():
        logger.info('Telegram notifications disabled')
        return None

    message = get_order_message(order)
    keyboard = get_order_keyboard(order)

    result = bot.send_message(
        chat_id=bot.chat_id,
        text=message,
        reply_markup=keyboard
    )

    if result:
        # Save message_id for later updates
        order.telegram_message_id = str(result.get('message_id', ''))
        order.save(update_fields=['telegram_message_id'])
        return result.get('message_id')

    return None


def update_order_notification(order):
    """
    Update existing order notification in Telegram.
    """
    bot = TelegramBot()

    if not bot.is_enabled():
        return None

    if not order.telegram_message_id:
        # No existing message, send new one
        return send_order_notification(order)

    message = get_order_message(order)
    keyboard = get_order_keyboard(order)

    result = bot.edit_message(
        chat_id=bot.chat_id,
        message_id=order.telegram_message_id,
        text=message,
        reply_markup=keyboard
    )

    return result


def send_customer_notification(order, message_text):
    """
    Send notification to customer via Telegram.
    Customer must have telegram_chat_id set.
    """
    bot = TelegramBot()

    if not bot.is_enabled():
        return None

    if not bot.settings.notify_customer:
        return None

    customer = order.customer
    if not customer.telegram_chat_id:
        return None

    return bot.send_message(
        chat_id=customer.telegram_chat_id,
        text=message_text
    )


def get_customer_status_message(order):
    """
    Generate status update message for customer.
    """
    status_messages = {
        'confirmed': f'✅ Ваш заказ #{order.pk} подтверждён! Начинаем готовить.',
        'cooking': f'👨‍🍳 Ваш заказ #{order.pk} готовится!',
        'delivering': f'🚗 Ваш заказ #{order.pk} в пути! Курьер скоро будет.',
        'delivered': f'✔️ Заказ #{order.pk} доставлен! Спасибо за заказ! Приятного аппетита!',
        'cancelled': f'❌ К сожалению, заказ #{order.pk} был отменён. Свяжитесь с нами для уточнения.',
    }

    return status_messages.get(order.status)
