from django import forms
from django.forms import inlineformset_factory
from .models import Order, OrderItem, Product

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_type', 'customer_name', 'notes']
        labels = {
            'order_type': 'Bestelltyp',
            'customer_name': 'Dein Name',
            'notes': 'Anmerkungen / Extrawünsche',
        }
        widgets = {
            'order_type': forms.Select(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name eingeben'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'z.B. Pizza Salami ohne Zwiebeln'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('order_type')
        customer_name = cleaned_data.get('customer_name')

        if order_type in ['kjgler', 'purchase'] and not customer_name:
            self.add_error('customer_name', 'Name ist für KjGler- und Einkaufspreis-Bestellungen erforderlich.')

        return cleaned_data

    def save(self, commit=True):
        order = super().save(commit=False)
        order.is_paid = True

        if commit:
            order.save()

        return order

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

OrderItemFormSet = inlineformset_factory(
    Order, OrderItem, form=OrderItemForm,
    extra=1, can_delete=True
)
