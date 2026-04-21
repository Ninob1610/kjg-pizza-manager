from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_orderitem_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='purchase_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='order_type',
            field=models.CharField(
                choices=[
                    ('regular', 'Normal'),
                    ('kjgler', 'KjGler-Pizza (kostenlos)'),
                    ('purchase', 'Einkaufspreis-Pizza (Partner)'),
                ],
                default='regular',
                max_length=20,
            ),
        ),
    ]
