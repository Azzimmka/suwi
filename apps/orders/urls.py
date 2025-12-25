"""
URL configuration for orders app.
"""

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Checkout
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),

    # Order detail and status
    path('<int:pk>/', views.OrderDetailView.as_view(), name='detail'),
    path('<int:pk>/status/', views.OrderStatusView.as_view(), name='status'),

    # Order history
    path('history/', views.OrderHistoryView.as_view(), name='history'),

    # Repeat order
    path('<int:pk>/repeat/', views.RepeatOrderView.as_view(), name='repeat'),
]
