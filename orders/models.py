from decimal import Decimal

from django.db import models
from django.utils import timezone


class FunnyNames:
    """Generator für lustige Namen wenn kein Name angegeben wurde"""
    ADJECTIVES = [
        'Schnelle', 'Hungrige', 'Geheimnisvolle', 'Mutige', 'Glückliche',
        'Freche', 'Träge', 'Wildeste', 'Geheime', 'Merkwürdige',
        'Verrückte', 'Zauberhafte', 'Lockende', 'Süße', 'Soziale',
        'Stumme', 'Redseelige', 'Sanfte', 'Starke', 'Weise',
        'Dumme', 'Kluge', 'Schöne', 'Hässliche', 'Komische',
        'Tragische', 'Epische', 'Dramatische', 'Romantische', 'Skeptische',
    ]
    
    NOUNS = [
        'Pizza-Ninja', 'Käse-König', 'Salami-Samurai', 'Knoblauch-Kobold',
        'Oregano-Oger', 'Teig-Troll', 'Ofen-Ork', 'Belag-Baron',
        'Kruste-Krake', 'Soße-Sultan', 'Mozzarella-Monster', 'Pepperoni-Pirat',
        'Basilikum-Bandit', 'Thunfisch-Titan', 'Schinken-Held', 'Spinat-Spion',
        'Zwiebel-Zauberer', 'Pilz-Prophet', 'Mais-Magier', 'Oliven-Oracle',
        'Tomate-Terrorist', 'Paprika-Phantom', 'Feta-Führer', 'Ricotta-Ritter',
        'Gorgonzola-Geist', 'Raclette-Räuber', 'PIZZA-GOTT', 'Cardia-Champion',
    ]
    
    @staticmethod
    def get_funny_name(order_id):
        """Generiert einen lustigen Namen basierend auf der Order-ID"""
        if not order_id:
            return "Anonyme Pizza"
        
        adj_index = (order_id * 7) % len(FunnyNames.ADJECTIVES)
        noun_index = (order_id * 13) % len(FunnyNames.NOUNS)
        
        return f"{FunnyNames.ADJECTIVES[adj_index]} {FunnyNames.NOUNS[noun_index]}"


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('pizza', 'Pizza'),
        ('drink', 'Getränk'),
    ]
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    purchase_price = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='pizza', db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['category']),
        ]

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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    is_paid = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_paid', 'status']),  # Composite index für Queries
            models.Index(fields=['-created_at']),  # Beschleunige ORDER BY -created_at
        ]

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    def recalculate_status(self):
        items = list(self.items.all())

        if not items:
            self.status = 'received'
            self.completed_at = None
            self.save(update_fields=['status', 'completed_at'])
            return

        if all(item.status == 'completed' for item in items):
            self.status = 'completed'
            if self.completed_at is None:
                self.completed_at = timezone.now()
            self.save(update_fields=['status', 'completed_at'])
            return

        self.completed_at = None
        if any(item.status == 'ready' for item in items):
            self.status = 'ready'
        elif any(item.status in ['topping', 'failed'] for item in items):
            self.status = 'topping'
        else:
            self.status = 'received'

        self.save(update_fields=['status', 'completed_at'])

    def unit_price_for_product(self, product):
        if self.order_type == 'kjgler':
            return Decimal('0.00')
        if self.order_type == 'purchase':
            return product.purchase_price if product.purchase_price is not None else product.price
        return product.price

    def get_display_name(self):
        """Gibt den anzeigbaren Namen zurück - lustiger Name wenn kein Name angegeben"""
        if self.customer_name:
            return self.customer_name
        return FunnyNames.get_funny_name(self.id)

    def __str__(self):
        return f"Bestellung #{self.id} - {self.get_display_name()}"

class OrderItem(models.Model):
    STATUS_CHOICES = [
        ('received', 'Eingegangen'),
        ('topping', 'Belegt'),
        ('ready', 'Ofenbereit'),
        ('completed', 'Ausgegeben'),
        ('failed', 'Fehlgeschlagen'),
    ]

    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, null=True, verbose_name="Extrawünsche")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received', db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['order', 'status']),  # Composite index für Filtering
        ]

    def change_status(self, new_status, action, note=None):
        old_status = self.status
        if old_status == new_status:
            return False

        self.status = new_status
        self.save(update_fields=['status'])

        OrderItemStatusLog.objects.create(
            order_item=self,
            action=action,
            from_status=old_status,
            to_status=new_status,
            note=note,
        )
        self.order.recalculate_status()
        return True

    def unit_price(self):
        return self.order.unit_price_for_product(self.product)

    def total_price(self):
        return self.unit_price() * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"


class OrderItemStatusLog(models.Model):
    ACTION_CHOICES = [
        ('start', 'Gestartet'),
        ('ready', 'Ofenbereit'),
        ('complete', 'Ausgegeben'),
        ('fail', 'Fehlgeschlagen'),
        ('reset', 'Zurückgesetzt'),
    ]

    order_item = models.ForeignKey(OrderItem, related_name='status_logs', on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_item} - {self.get_action_display()}"
