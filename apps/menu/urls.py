"""
URL configuration for menu app.
"""

from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    # Catalog
    path('', views.CatalogView.as_view(), name='catalog'),

    # Category
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category'),

    # Product detail
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product'),

    # Search
    path('search/', views.SearchView.as_view(), name='search'),

    # Favorites
    path('favorites/', views.FavoritesView.as_view(), name='favorites'),
    path('favorite/toggle/<int:product_id>/', views.ToggleFavoriteView.as_view(), name='toggle_favorite'),
]
