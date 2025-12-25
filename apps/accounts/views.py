"""
Authentication views for Suwi.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import CustomerRegistrationForm, CustomerLoginForm, CustomerProfileForm
from .models import Customer


class RegisterView(FormView):
    """
    Customer registration view.
    """
    template_name = 'accounts/register.html'
    form_class = CustomerRegistrationForm
    success_url = reverse_lazy('menu:catalog')

    def dispatch(self, request, *args, **kwargs):
        # Redirect authenticated users
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend='apps.accounts.backends.PhoneBackend')
        messages.success(
            self.request,
            f'Добро пожаловать, {user.first_name}! Регистрация прошла успешно.'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Регистрация'
        return context


class LoginView(FormView):
    """
    Customer login view.
    """
    template_name = 'accounts/login.html'
    form_class = CustomerLoginForm
    success_url = reverse_lazy('menu:catalog')

    def dispatch(self, request, *args, **kwargs):
        # Redirect authenticated users
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        user = form.get_user()
        remember_me = form.cleaned_data.get('remember_me', False)

        login(self.request, user, backend='apps.accounts.backends.PhoneBackend')

        # Set session expiry
        if not remember_me:
            # Session expires when browser closes
            self.request.session.set_expiry(0)
        else:
            # Session expires in 30 days
            self.request.session.set_expiry(60 * 60 * 24 * 30)

        messages.success(self.request, f'С возвращением, {user.first_name or user.phone}!')

        # Redirect to 'next' URL if provided
        next_url = self.request.GET.get('next')
        if next_url:
            return redirect(next_url)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Вход'
        return context


class LogoutView(TemplateView):
    """
    Customer logout view.
    """
    template_name = 'accounts/logout.html'

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, 'Вы вышли из аккаунта.')
        return redirect('menu:catalog')

    def get(self, request, *args, **kwargs):
        # Also allow GET for convenience
        logout(request)
        messages.info(request, 'Вы вышли из аккаунта.')
        return redirect('menu:catalog')


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    Customer profile view and edit.
    """
    model = Customer
    form_class = CustomerProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Мой профиль'
        context['orders'] = self.request.user.orders.all()[:5]
        return context


class OrderHistoryView(LoginRequiredMixin, TemplateView):
    """
    Customer order history view.
    """
    template_name = 'accounts/order_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'История заказов'
        context['orders'] = self.request.user.orders.all()
        return context
