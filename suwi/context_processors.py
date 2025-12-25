"""
Global context processors for Suwi project.
"""

from django.conf import settings


def restaurant_settings(request):
    """
    Add restaurant settings to template context.
    """
    return {
        'RESTAURANT_NAME': getattr(settings, 'RESTAURANT_NAME', 'Суши love'),
        'RESTAURANT_PHONE': getattr(settings, 'RESTAURANT_PHONE', ''),
        'RESTAURANT_ADDRESS': getattr(settings, 'RESTAURANT_ADDRESS', ''),
    }
