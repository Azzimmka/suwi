"""
URL configuration for suwi project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Home redirect to menu
    path('', RedirectView.as_view(pattern_name='menu:catalog', permanent=False), name='home'),

    # Offline page for PWA
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),

    # Apps
    path('accounts/', include('apps.accounts.urls')),
    path('menu/', include('apps.menu.urls')),
    path('cart/', include('apps.cart.urls')),
    path('orders/', include('apps.orders.urls')),
    path('telegram/', include('apps.telegram_bot.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
