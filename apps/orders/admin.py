"""
Admin configuration for orders app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline for order items."""
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'get_total')
    can_delete = False

    def get_total(self, obj):
        return f'{obj.get_total():,.0f} сум'
    get_total.short_description = 'Сумма'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for Order model."""

    list_display = (
        'id', 'customer_link', 'status_badge', 'address_short',
        'total_display', 'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'customer__phone', 'customer__first_name', 'address', 'phone')
    readonly_fields = (
        'customer', 'latitude', 'longitude', 'subtotal', 'delivery_fee',
        'bonus_used', 'total', 'created_at', 'updated_at', 'map_link'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]

    fieldsets = (
        ('Заказ', {
            'fields': ('customer', 'status')
        }),
        ('Доставка', {
            'fields': ('address', 'latitude', 'longitude', 'map_link', 'phone', 'comment')
        }),
        ('Суммы', {
            'fields': ('subtotal', 'delivery_fee', 'bonus_used', 'total')
        }),
        ('Telegram', {
            'fields': ('telegram_message_id',),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_confirmed', 'mark_cooking', 'mark_delivering', 'mark_delivered']

    def customer_link(self, obj):
        url = reverse('admin:accounts_customer_change', args=[obj.customer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.customer.phone)
    customer_link.short_description = 'Клиент'

    def status_badge(self, obj):
        colors = {
            'new': '#1565c0',
            'confirmed': '#2e7d32',
            'cooking': '#ef6c00',
            'delivering': '#7b1fa2',
            'delivered': '#2e7d32',
            'cancelled': '#c62828',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-size: 0.85em;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Статус'

    def address_short(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_short.short_description = 'Адрес'

    def total_display(self, obj):
        return f'{obj.total:,.0f} сум'
    total_display.short_description = 'Итого'
    total_display.admin_order_field = 'total'

    def map_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">Google Maps</a> | '
            '<a href="{}" target="_blank">Yandex Maps</a> | '
            '<a href="{}" target="_blank">Yandex Go</a>',
            obj.get_google_maps_url(),
            obj.get_yandex_maps_url(),
            obj.get_yandex_go_url()
        )
    map_link.short_description = 'Карты'

    @admin.action(description='Пометить как "Подтверждён"')
    def mark_confirmed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='confirmed', confirmed_at=timezone.now())

    @admin.action(description='Пометить как "Готовится"')
    def mark_cooking(self, request, queryset):
        queryset.update(status='cooking')

    @admin.action(description='Пометить как "В доставке"')
    def mark_delivering(self, request, queryset):
        queryset.update(status='delivering')

    @admin.action(description='Пометить как "Доставлен"')
    def mark_delivered(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='delivered', delivered_at=timezone.now())


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin for OrderItem model."""

    list_display = ('id', 'order_link', 'product_name', 'quantity', 'price', 'total_display')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'product_name')
    raw_id_fields = ('order', 'product')

    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.pk])
        return format_html('<a href="#">#{}</a>', obj.order.pk)
    order_link.short_description = 'Заказ'

    def total_display(self, obj):
        return f'{obj.get_total():,.0f} сум'
    total_display.short_description = 'Сумма'
