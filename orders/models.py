from django.db import models
from decimal import Decimal

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('pizza', 'Pizza'),
        ('drink', 'Getränk'),
    ]
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    purchase_price = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='pizza')

    def __str__(self):
        return f"{self.name} ({self.price}€)"

class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('regular', 'Normal'),
        ('kjgler', 'KjGler-Pizza (kostenlos)'),
        ('purchase', 'Einkaufspreis-Pizza (Partner)'),
    ]
    STATUS_CHOICES = [
        ('received', 'Eingegangen'),
        ('topping', 'Belegt'),
        ('ready', 'Abholbereit'),
        ('completed', 'Ausgegeben'),
    ]
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='regular')
    notes = models.TextField(blank=True, null=True, verbose_name="Anmerkungen / Extrawünsche")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    def unit_price_for_product(self, product):
        if self.order_type == 'kjgler':
            return Decimal('0.00')
        if self.order_type == 'purchase':
            return product.purchase_price if product.purchase_price is not None else product.price
        return product.price

    def __str__(self):
        return f"Bestellung #{self.id} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, null=True, verbose_name="Extrawünsche")

    def unit_price(self):
        return self.order.unit_price_for_product(self.product)

    def total_price(self):
        return self.unit_price() * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
