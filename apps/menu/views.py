"""
Menu views for Suwi - catalog, categories, products, favorites.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from .models import Category, Product, Favorite


class CatalogView(ListView):
    """
    Main catalog view - shows all categories with products.
    """
    template_name = 'menu/catalog.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(is_active=True).prefetch_related(
            'products'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Меню'
        context['popular_products'] = Product.objects.filter(
            is_available=True,
            is_popular=True
        )[:8]

        # Get user's favorites if authenticated
        if self.request.user.is_authenticated:
            context['favorite_ids'] = set(
                Favorite.objects.filter(
                    customer=self.request.user
                ).values_list('product_id', flat=True)
            )
        else:
            context['favorite_ids'] = set()

        return context


class CategoryView(ListView):
    """
    Category view - shows products in a specific category.
    """
    template_name = 'menu/category.html'
    context_object_name = 'products'

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['slug'],
            is_active=True
        )
        return Product.objects.filter(
            category=self.category,
            is_available=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['title'] = self.category.name
        context['categories'] = Category.objects.filter(is_active=True)

        # Get user's favorites
        if self.request.user.is_authenticated:
            context['favorite_ids'] = set(
                Favorite.objects.filter(
                    customer=self.request.user
                ).values_list('product_id', flat=True)
            )
        else:
            context['favorite_ids'] = set()

        return context


class ProductDetailView(DetailView):
    """
    Product detail view.
    """
    model = Product
    template_name = 'menu/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_available=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.name

        # Related products from same category
        context['related_products'] = Product.objects.filter(
            category=self.object.category,
            is_available=True
        ).exclude(pk=self.object.pk)[:4]

        # Check if in favorites
        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(
                customer=self.request.user,
                product=self.object
            ).exists()
        else:
            context['is_favorite'] = False

        return context


class SearchView(ListView):
    """
    Product search view.
    """
    template_name = 'menu/search.html'
    context_object_name = 'products'

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if query:
            return Product.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query),
                is_available=True
            )
        return Product.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['title'] = f'Поиск: {context["query"]}'

        if self.request.user.is_authenticated:
            context['favorite_ids'] = set(
                Favorite.objects.filter(
                    customer=self.request.user
                ).values_list('product_id', flat=True)
            )
        else:
            context['favorite_ids'] = set()

        return context


class FavoritesView(LoginRequiredMixin, ListView):
    """
    User's favorite products view.
    """
    template_name = 'menu/favorites.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return Favorite.objects.filter(
            customer=self.request.user
        ).select_related('product', 'product__category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Избранное'
        return context


class ToggleFavoriteView(LoginRequiredMixin, View):
    """
    Toggle product favorite status (AJAX).
    """

    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id, is_available=True)

        favorite, created = Favorite.objects.get_or_create(
            customer=request.user,
            product=product
        )

        if not created:
            # Already exists, remove it
            favorite.delete()
            is_favorite = False
        else:
            is_favorite = True

        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_favorite': is_favorite,
                'product_id': product_id,
            })

        # Regular request - redirect back
        return redirect(request.META.get('HTTP_REFERER', 'menu:catalog'))
