"""
Menu models for Suwi - categories, products, and favorites.
"""

from django.db import models
from django.urls import reverse
from django.conf import settings


class Category(models.Model):
    """
    Product category (e.g., Rolls, Sushi, Sets, Drinks).
    """

    name = models.CharField(
        'Название',
        max_length=100
    )

    slug = models.SlugField(
        'URL',
        max_length=100,
        unique=True,
        help_text='URL категории (латиница, без пробелов)'
    )

    description = models.TextField(
        'Описание',
        blank=True
    )

    image = models.ImageField(
        'Изображение',
        upload_to='categories/',
        blank=True,
        null=True
    )

    order = models.PositiveIntegerField(
        'Порядок',
        default=0,
        help_text='Порядок отображения (меньше = выше)'
    )

    is_active = models.BooleanField(
        'Активна',
        default=True,
        help_text='Отображать категорию на сайте'
    )

    created_at = models.DateTimeField(
        'Создана',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('menu:category', kwargs={'slug': self.slug})

    def get_products_count(self):
        """Return count of available products in this category."""
        return self.products.filter(is_available=True).count()


class Product(models.Model):
    """
    Product model (sushi, rolls, drinks, etc.).
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Категория'
    )

    name = models.CharField(
        'Название',
        max_length=200
    )

    slug = models.SlugField(
        'URL',
        max_length=200,
        unique=True,
        help_text='URL продукта (латиница, без пробелов)'
    )

    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Состав, особенности'
    )

    price = models.DecimalField(
        'Цена',
        max_digits=10,
        decimal_places=0,  # No decimal places for UZS
        help_text='Цена в сумах'
    )

    image = models.ImageField(
        'Изображение',
        upload_to='products/',
        blank=True,
        null=True
    )

    weight = models.CharField(
        'Вес/Объём',
        max_length=50,
        blank=True,
        help_text='Например: 250г или 330мл'
    )

    pieces = models.PositiveSmallIntegerField(
        'Количество штук',
        blank=True,
        null=True,
        help_text='Количество штук в порции (для роллов)'
    )

    is_available = models.BooleanField(
        'В наличии',
        default=True,
        help_text='Доступен для заказа'
    )

    is_popular = models.BooleanField(
        'Популярное',
        default=False,
        help_text='Показывать в блоке популярных'
    )

    is_new = models.BooleanField(
        'Новинка',
        default=False,
        help_text='Показывать метку "Новинка"'
    )

    order = models.PositiveIntegerField(
        'Порядок',
        default=0,
        help_text='Порядок в категории (меньше = выше)'
    )

    created_at = models.DateTimeField(
        'Создан',
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        'Обновлён',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['category', 'order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('menu:product', kwargs={'slug': self.slug})


class Favorite(models.Model):
    """
    Customer's favorite products.
    """

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Клиент'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Продукт'
    )

    created_at = models.DateTimeField(
        'Добавлен',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ['customer', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.customer} - {self.product}'
