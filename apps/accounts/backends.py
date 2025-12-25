"""
Custom authentication backend for phone-based login.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

Customer = get_user_model()


class PhoneBackend(ModelBackend):
    """
    Authentication backend that uses phone number instead of username.
    """

    def authenticate(self, request, phone=None, password=None, **kwargs):
        """
        Authenticate user by phone number and password.
        """
        if phone is None:
            phone = kwargs.get(Customer.USERNAME_FIELD)

        if phone is None or password is None:
            return None

        try:
            # Normalize phone number
            phone = ''.join(filter(lambda x: x.isdigit() or x == '+', phone))
            user = Customer.objects.get(phone=phone)
        except Customer.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            Customer().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        """
        Get user by ID.
        """
        try:
            return Customer.objects.get(pk=user_id)
        except Customer.DoesNotExist:
            return None
