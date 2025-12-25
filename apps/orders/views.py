"""
Order views for Suwi - checkout, order status, and history.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction

from apps.cart.cart import Cart
from apps.accounts.models import SavedAddress
from .models import Order, OrderItem


class CheckoutView(LoginRequiredMixin, View):
    """
    Checkout page - form with address, phone, and map for geolocation.
    """
    template_name = 'orders/checkout.html'

    def get(self, request):
        cart = Cart(request)

        # Redirect if cart is empty
        if cart.is_empty():
            messages.warning(request, 'Ваша корзина пуста')
            return redirect('cart:detail')

        # Get user's saved addresses
        saved_addresses = SavedAddress.objects.filter(
            customer=request.user
        ).order_by('-is_default', 'name')

        context = {
            'title': 'Оформление заказа',
            'cart': cart,
            'saved_addresses': saved_addresses,
            'user_phone': request.user.phone,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        cart = Cart(request)

        # Redirect if cart is empty
        if cart.is_empty():
            messages.warning(request, 'Ваша корзина пуста')
            return redirect('cart:detail')

        # Get form data
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        comment = request.POST.get('comment', '').strip()
        save_address = request.POST.get('save_address') == 'on'
        address_name = request.POST.get('address_name', '').strip()

        # Validate required fields
        errors = []
        if not latitude or not longitude:
            errors.append('Пожалуйста, укажите точку доставки на карте')
        if not address:
            errors.append('Укажите адрес доставки')
        if not phone:
            errors.append('Укажите номер телефона')

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('orders:checkout')

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (ValueError, TypeError):
            messages.error(request, 'Неверные координаты')
            return redirect('orders:checkout')

        # Create order
        with transaction.atomic():
            order = Order.objects.create(
                customer=request.user,
                latitude=latitude,
                longitude=longitude,
                address=address,
                phone=phone,
                comment=comment,
                status='new',
            )

            # Create order items from cart
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_name=item['product'].name,
                    price=item['price'],
                    quantity=item['quantity'],
                )

            # Calculate totals
            order.calculate_total()
            order.save()

            # Save address if requested
            if save_address and address_name:
                SavedAddress.objects.create(
                    customer=request.user,
                    name=address_name,
                    address=address,
                    latitude=latitude,
                    longitude=longitude,
                )

            # Clear cart
            cart.clear()

        messages.success(request, f'Заказ #{order.pk} успешно создан!')
        return redirect('orders:detail', pk=order.pk)


class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    Order detail page with status tracking.
    """
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        # Users can only see their own orders
        return Order.objects.filter(customer=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Заказ #{self.object.pk}'
        return context


class OrderStatusView(LoginRequiredMixin, View):
    """
    API endpoint for polling order status.
    Returns JSON with current status.
    """

    def get(self, request, pk):
        order = get_object_or_404(
            Order,
            pk=pk,
            customer=request.user
        )

        return JsonResponse({
            'status': order.status,
            'status_display': order.get_status_display(),
            'updated_at': order.updated_at.isoformat(),
        })


class OrderHistoryView(LoginRequiredMixin, ListView):
    """
    List of user's orders.
    """
    model = Order
    template_name = 'orders/history.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(
            customer=self.request.user
        ).prefetch_related('items')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'История заказов'
        return context


class RepeatOrderView(LoginRequiredMixin, View):
    """
    Repeat a previous order - adds all items to cart.
    """

    def post(self, request, pk):
        order = get_object_or_404(
            Order,
            pk=pk,
            customer=request.user
        )

        cart = Cart(request)

        # Add all items from order to cart
        items_added = 0
        for item in order.items.all():
            if item.product and item.product.is_available:
                cart.add(
                    product=item.product,
                    quantity=item.quantity,
                    override_quantity=False
                )
                items_added += 1

        if items_added > 0:
            messages.success(
                request,
                f'Добавлено {items_added} товаров из заказа #{order.pk}'
            )
        else:
            messages.warning(
                request,
                'Товары из этого заказа больше недоступны'
            )

        return redirect('cart:detail')
