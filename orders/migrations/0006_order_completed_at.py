from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_product_purchase_price_order_order_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
