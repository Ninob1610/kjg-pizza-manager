from django.db import models

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('pizza', 'Pizza'),
        ('drink', 'Getränk'),
    ]
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='pizza')

    def __str__(self):
        return f"{self.name} ({self.price}€)"

class Order(models.Model):
    STATUS_CHOICES = [
        ('received', 'Eingegangen'),
        ('topping', 'Belegt'),
        ('ready', 'Abholbereit'),
        ('completed', 'Ausgegeben'),
    ]
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True, verbose_name="Anmerkungen / Extrawünsche")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    def __str__(self):
        return f"Bestellung #{self.id} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, null=True, verbose_name="Extrawünsche")

    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
