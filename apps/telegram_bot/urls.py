"""
URL configuration for telegram_bot app.
"""

from django.urls import path
from . import views

app_name = 'telegram_bot'

urlpatterns = [
    # Telegram webhook
    path('webhook/', views.WebhookView.as_view(), name='webhook'),

    # Setup webhook (admin only)
    path('set-webhook/', views.SetWebhookView.as_view(), name='set_webhook'),
]
