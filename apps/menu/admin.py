"""
Admin configuration for menu app.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, Favorite


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""

    list_display = ('name', 'slug', 'order', 'is_active', 'products_count', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    list_editable = ('order', 'is_active')

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Товаров'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model."""

    list_display = (
        'name', 'category', 'price_display', 'is_available',
        'is_popular', 'is_new', 'order', 'image_preview'
    )
    list_filter = ('category', 'is_available', 'is_popular', 'is_new')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('category', 'order', 'name')
    list_editable = ('is_available', 'is_popular', 'is_new', 'order')
    readonly_fields = ('created_at', 'updated_at', 'image_preview_large')

    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'description')
        }),
        ('Цена и характеристики', {
            'fields': ('price', 'weight', 'pieces')
        }),
        ('Изображение', {
            'fields': ('image', 'image_preview_large')
        }),
        ('Настройки отображения', {
            'fields': ('is_available', 'is_popular', 'is_new', 'order')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        return f'{obj.price:,.0f} сум'
    price_display.short_description = 'Цена'
    price_display.admin_order_field = 'price'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 80px; object-fit: cover;">',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Фото'

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 300px;">',
                obj.image.url
            )
        return 'Нет изображения'
    image_preview_large.short_description = 'Превью'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin for Favorite model."""

    list_display = ('customer', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('customer__phone', 'customer__first_name', 'product__name')
    raw_id_fields = ('customer', 'product')
    date_hierarchy = 'created_at'
