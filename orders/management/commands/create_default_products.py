from decimal import Decimal

from django.core.management.base import BaseCommand

from orders.models import Product


class Command(BaseCommand):
    help = 'Creates or updates the default pizza products'

    DEFAULT_PRODUCTS = [
        {
            'name': 'Margherita',
            'price': Decimal('5.00'),
            'purchase_price': Decimal('3.00'),
        },
        {
            'name': 'Mary',
            'price': Decimal('6.00'),
            'purchase_price': Decimal('3.50'),
        },
        {
            'name': 'Prosciutto',
            'price': Decimal('6.00'),
            'purchase_price': Decimal('3.50'),
        },
        {
            'name': 'Spezial',
            'price': Decimal('6.00'),
            'purchase_price': Decimal('3.50'),
        },
    ]

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for product_data in self.DEFAULT_PRODUCTS:
            _, created = Product.objects.update_or_create(
                name=product_data['name'],
                category='pizza',
                defaults={
                    'price': product_data['price'],
                    'purchase_price': product_data['purchase_price'],
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Default pizzas synced: {created_count} created, {updated_count} updated'
            )
        )
