"""
Cart views for Suwi - shopping cart functionality.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator

from apps.menu.models import Product
from .cart import Cart


class CartDetailView(TemplateView):
    """
    Shopping cart detail page.
    """
    template_name = 'cart/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Корзина'
        return context


class CartAddView(View):
    """
    Add product to cart (AJAX).
    """

    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, pk=product_id, is_available=True)

        # Get quantity from request
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                quantity = 1
            if quantity > 99:
                quantity = 99
        except (ValueError, TypeError):
            quantity = 1

        # Check if override (replace) or add
        override = request.POST.get('override') == 'true'

        cart.add(product=product, quantity=quantity, override_quantity=override)

        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': len(cart),
                'cart_total': float(cart.get_total_price()),
                'message': f'{product.name} добавлен в корзину',
            })

        return redirect('cart:detail')


class CartUpdateView(View):
    """
    Update product quantity in cart (AJAX).
    """

    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, pk=product_id)

        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

        if quantity > 0:
            cart.add(product=product, quantity=quantity, override_quantity=True)
        else:
            cart.remove(product)

        # Calculate item total
        item = cart.get_item(product_id)
        item_total = float(item['price']) * item['quantity'] if item else 0

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': len(cart),
                'cart_total': float(cart.get_total_price()),
                'item_total': item_total,
                'quantity': quantity if quantity > 0 else 0,
            })

        return redirect('cart:detail')


class CartRemoveView(View):
    """
    Remove product from cart (AJAX).
    """

    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, pk=product_id)

        cart.remove(product)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': len(cart),
                'cart_total': float(cart.get_total_price()),
                'message': 'Товар удалён из корзины',
            })

        return redirect('cart:detail')


class CartClearView(View):
    """
    Clear entire cart.
    """

    def post(self, request):
        cart = Cart(request)
        cart.clear()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': 0,
                'cart_total': 0,
                'message': 'Корзина очищена',
            })

        return redirect('cart:detail')


class CartCountView(View):
    """
    Get cart count and total (AJAX).
    Used for updating cart badge without page reload.
    """

    def get(self, request):
        cart = Cart(request)
        return JsonResponse({
            'cart_count': len(cart),
            'cart_total': float(cart.get_total_price()),
        })
