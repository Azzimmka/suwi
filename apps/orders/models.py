"""
Order models for Suwi - orders and order items.
"""

from django.db import models
from django.conf import settings
from django.urls import reverse
from decimal import Decimal


class Order(models.Model):
    """
    Customer order with delivery information.
    """

    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтверждён'),
        ('cooking', 'Готовится'),
        ('delivering', 'В доставке'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]

    # Customer info
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Клиент'
    )

    # Order status
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )

    # Delivery address (required geolocation)
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

    address = models.TextField(
        'Адрес доставки',
        help_text='Полный адрес с ориентирами'
    )

    # Contact info (may differ from customer's phone)
    phone = models.CharField(
        'Телефон для связи',
        max_length=20
    )

    # Additional info
    comment = models.TextField(
        'Комментарий к заказу',
        blank=True,
        help_text='Пожелания по доставке, аллергии и т.д.'
    )

    # Totals
    subtotal = models.DecimalField(
        'Сумма товаров',
        max_digits=12,
        decimal_places=0,
        default=0
    )

    delivery_fee = models.DecimalField(
        'Стоимость доставки',
        max_digits=10,
        decimal_places=0,
        default=0
    )

    bonus_used = models.DecimalField(
        'Использовано бонусов',
        max_digits=10,
        decimal_places=0,
        default=0
    )

    total = models.DecimalField(
        'Итого к оплате',
        max_digits=12,
        decimal_places=0,
        default=0
    )

    # Telegram message ID (for updating status in chat)
    telegram_message_id = models.CharField(
        'ID сообщения в Telegram',
        max_length=50,
        blank=True,
        help_text='ID сообщения для обновления статуса'
    )

    # Timestamps
    created_at = models.DateTimeField(
        'Создан',
        auto_now_add=True,
        db_index=True
    )

    updated_at = models.DateTimeField(
        'Обновлён',
        auto_now=True
    )

    confirmed_at = models.DateTimeField(
        'Подтверждён',
        blank=True,
        null=True
    )

    delivered_at = models.DateTimeField(
        'Доставлен',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.pk} - {self.get_status_display()}'

    def get_absolute_url(self):
        return reverse('orders:detail', kwargs={'pk': self.pk})

    def get_google_maps_url(self):
        """Return Google Maps URL for the delivery location."""
        return f'https://www.google.com/maps?q={self.latitude},{self.longitude}'

    def get_yandex_maps_url(self):
        """Return Yandex Maps URL for the delivery location."""
        return f'https://yandex.ru/maps/?pt={self.longitude},{self.latitude}&z=17'

    def get_yandex_go_url(self):
        """
        Return Yandex Go deep link for delivery.
        Pre-fills route from restaurant to customer.
        """
        restaurant_lat = settings.RESTAURANT_LATITUDE
        restaurant_lon = settings.RESTAURANT_LONGITUDE

        return (
            f'https://3.redirect.appmetrica.yandex.com/route?'
            f'start-lat={restaurant_lat}&start-lon={restaurant_lon}'
            f'&end-lat={self.latitude}&end-lon={self.longitude}'
            f'&tariffClass=express'
            f'&comment=Заказ #{self.pk}, тел: {self.phone}'
        )

    def calculate_total(self):
        """Calculate and update order totals."""
        self.subtotal = sum(
            item.get_total() for item in self.items.all()
        )
        self.total = self.subtotal + self.delivery_fee - self.bonus_used
        return self.total

    @property
    def items_count(self):
        """Return total number of items in order."""
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    """
    Individual item in an order.
    Stores product info at the time of order (price may change later).
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )

    product = models.ForeignKey(
        'menu.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items',
        verbose_name='Продукт'
    )

    # Store product info at time of order (prices may change)
    product_name = models.CharField(
        'Название продукта',
        max_length=200
    )

    price = models.DecimalField(
        'Цена за единицу',
        max_digits=10,
        decimal_places=0,
        help_text='Цена на момент заказа'
    )

    quantity = models.PositiveIntegerField(
        'Количество',
        default=1
    )

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f'{self.product_name} x{self.quantity}'

    def get_total(self):
        """Return total price for this item."""
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        # Auto-fill product name and price from product if not set
        if self.product and not self.product_name:
            self.product_name = self.product.name
        if self.product and not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)
