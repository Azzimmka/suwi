"""
Context processor for cart.
Makes cart available in all templates.
"""


def cart(request):
    """
    Add cart to template context.
    """
    from apps.cart.cart import Cart
    return {'cart': Cart(request)}
