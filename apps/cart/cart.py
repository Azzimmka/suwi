"""
Shopping cart implementation using Django sessions.
"""

from decimal import Decimal
from django.conf import settings
from apps.menu.models import Product


class Cart:
    """
    Shopping cart class that stores items in session.
    """

    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.

        Args:
            product: Product instance to add
            quantity: Number of items to add
            override_quantity: If True, replace quantity; if False, add to existing
        """
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        # Remove item if quantity is 0 or less
        if self.cart[product_id]['quantity'] <= 0:
            del self.cart[product_id]

        self.save()

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        """
        Mark the session as modified to make sure it gets saved.
        """
        self.session.modified = True

    def clear(self):
        """
        Remove cart from session.
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products from the database.
        """
        product_ids = self.cart.keys()
        # Get the product objects and add them to the cart
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Calculate the total cost of all items in the cart.
        """
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def get_item(self, product_id):
        """
        Get a specific item from the cart.
        """
        product_id = str(product_id)
        if product_id in self.cart:
            return self.cart[product_id]
        return None

    def get_quantity(self, product_id):
        """
        Get quantity of a specific product in cart.
        """
        item = self.get_item(product_id)
        return item['quantity'] if item else 0

    @property
    def is_empty(self):
        """
        Check if cart is empty.
        """
        return len(self.cart) == 0

    def to_order_items(self):
        """
        Convert cart items to order items data.
        Returns list of dicts ready for OrderItem creation.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        products_dict = {str(p.id): p for p in products}

        items = []
        for product_id, item_data in self.cart.items():
            product = products_dict.get(product_id)
            if product:
                items.append({
                    'product': product,
                    'product_name': product.name,
                    'price': product.price,
                    'quantity': item_data['quantity'],
                })
        return items
