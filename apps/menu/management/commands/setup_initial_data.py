"""
Management command to setup initial data for Sushi love.
Creates categories, products, and admin user.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.menu.models import Category, Product
from apps.telegram_bot.models import TelegramSettings


Customer = get_user_model()


class Command(BaseCommand):
    help = 'Setup initial data for Sushi love'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')

        # Create admin user
        self.create_admin()

        # Create categories
        self.create_categories()

        # Create products
        self.create_products()

        # Setup telegram
        self.setup_telegram()

        self.stdout.write(self.style.SUCCESS('Initial data setup complete!'))

    def create_admin(self):
        if not Customer.objects.filter(phone='+998901234567').exists():
            Customer.objects.create_superuser(
                phone='+998901234567',
                password='admin123',
                first_name='Admin'
            )
            self.stdout.write(self.style.SUCCESS('Admin created: +998901234567 / admin123'))
        else:
            self.stdout.write('Admin already exists')

    def create_categories(self):
        categories = [
            {'name': 'Роллы', 'slug': 'rolls', 'order': 1},
            {'name': 'Суши', 'slug': 'sushi', 'order': 2},
            {'name': 'Сеты', 'slug': 'sets', 'order': 3},
            {'name': 'Напитки', 'slug': 'drinks', 'order': 4},
        ]

        for cat_data in categories:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'order': cat_data['order'],
                    'is_active': True,
                }
            )
            status = 'created' if created else 'exists'
            self.stdout.write(f"Category {cat.name}: {status}")

    def create_products(self):
        rolls = Category.objects.get(slug='rolls')
        sushi = Category.objects.get(slug='sushi')

        products = [
            # Роллы
            {
                'category': rolls,
                'name': 'Филадельфия',
                'slug': 'philadelphia',
                'description': 'Лосось, сливочный сыр, огурец, авокадо',
                'price': 65000,
                'weight': '250г',
                'pieces': 8,
                'is_popular': True,
            },
            {
                'category': rolls,
                'name': 'Калифорния',
                'slug': 'california',
                'description': 'Краб, авокадо, огурец, тобико',
                'price': 55000,
                'weight': '220г',
                'pieces': 8,
                'is_popular': True,
            },
            {
                'category': rolls,
                'name': 'Дракон',
                'slug': 'dragon',
                'description': 'Угорь, огурец, авокадо, унаги соус',
                'price': 75000,
                'weight': '280г',
                'pieces': 8,
            },
            {
                'category': rolls,
                'name': 'Спайси тунец',
                'slug': 'spicy-tuna',
                'description': 'Тунец, спайси соус, огурец, кунжут',
                'price': 60000,
                'weight': '230г',
                'pieces': 8,
            },
            {
                'category': rolls,
                'name': 'Радуга',
                'slug': 'rainbow',
                'description': 'Лосось, тунец, угорь, креветка, авокадо',
                'price': 85000,
                'weight': '300г',
                'pieces': 8,
            },
            # Суши
            {
                'category': sushi,
                'name': 'Саке нигири',
                'slug': 'sake-nigiri',
                'description': 'Свежий лосось на рисе',
                'price': 25000,
                'weight': '35г',
                'pieces': 2,
                'is_popular': True,
            },
            {
                'category': sushi,
                'name': 'Магуро нигири',
                'slug': 'maguro-nigiri',
                'description': 'Тунец на рисе',
                'price': 28000,
                'weight': '35г',
                'pieces': 2,
            },
            {
                'category': sushi,
                'name': 'Эби нигири',
                'slug': 'ebi-nigiri',
                'description': 'Креветка на рисе',
                'price': 22000,
                'weight': '35г',
                'pieces': 2,
            },
            {
                'category': sushi,
                'name': 'Унаги нигири',
                'slug': 'unagi-nigiri',
                'description': 'Угорь на рисе с соусом',
                'price': 32000,
                'weight': '40г',
                'pieces': 2,
            },
            {
                'category': sushi,
                'name': 'Тамаго нигири',
                'slug': 'tamago-nigiri',
                'description': 'Японский омлет на рисе',
                'price': 18000,
                'weight': '35г',
                'pieces': 2,
            },
        ]

        for prod_data in products:
            prod, created = Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults={
                    'category': prod_data['category'],
                    'name': prod_data['name'],
                    'description': prod_data['description'],
                    'price': prod_data['price'],
                    'weight': prod_data.get('weight', ''),
                    'pieces': prod_data.get('pieces', 0),
                    'is_available': True,
                    'is_popular': prod_data.get('is_popular', False),
                }
            )
            status = 'created' if created else 'exists'
            self.stdout.write(f"Product {prod.name}: {status}")

    def setup_telegram(self):
        settings, created = TelegramSettings.objects.get_or_create(
            pk=1,
            defaults={
                'bot_token': '8535120808:AAGdSA0vcc-Sh3CW1cMkIBCMhdjY0ofU87E',
                'chat_id': '5586955727',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Telegram settings created'))
        else:
            self.stdout.write('Telegram settings already exist')
