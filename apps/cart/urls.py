"""
URL configuration for cart app.
"""

from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    # Cart detail page
    path('', views.CartDetailView.as_view(), name='detail'),

    # Cart operations (AJAX)
    path('add/<int:product_id>/', views.CartAddView.as_view(), name='add'),
    path('update/<int:product_id>/', views.CartUpdateView.as_view(), name='update'),
    path('remove/<int:product_id>/', views.CartRemoveView.as_view(), name='remove'),
    path('clear/', views.CartClearView.as_view(), name='clear'),

    # Cart count (AJAX)
    path('count/', views.CartCountView.as_view(), name='count'),
]
