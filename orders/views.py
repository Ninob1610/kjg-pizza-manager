from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Order, OrderItem
from .forms import OrderForm, OrderItemFormSet
from django.db.models import Sum, F
from django.db.models.functions import TruncDate
from django.contrib.admin.views.decorators import staff_member_required

def customer_order(request):
    products = Product.objects.all()
    # Online ordering disabled. Only display menu.
    return render(request, 'orders/customer_order.html', {
        'products': products,
    })

def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order_success.html', {'order': order})

def cashier_dashboard(request):
    orders = Order.objects.exclude(status='completed').order_by('-created_at')
    
    if request.method == 'POST':
        if 'mark_paid' in request.POST:
            order_id = request.POST.get('order_id')
            order = get_object_or_404(Order, id=order_id)
            order.is_paid = True
            order.save()
            return redirect('cashier_dashboard')

    return render(request, 'orders/cashier_dashboard.html', {'orders': orders})

def create_order_cashier(request):
    products = Product.objects.all()
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            # Process items from POST data (similar to customer view)
            has_items = False
            for key, value in request.POST.items():
                if key.startswith('product_') and key[8:].isdigit():
                    try:
                        p_id = int(key.split('_')[1])
                        quantity = int(value)
                        if quantity > 0:
                            product = Product.objects.get(id=p_id)
                            item_notes = request.POST.get(f'product_note_{p_id}', '').strip()
                            OrderItem.objects.create(
                                order=order,
                                product=product,
                                quantity=quantity,
                                notes=item_notes or None,
                            )
                            has_items = True
                    except (ValueError, Product.DoesNotExist):
                        continue
            
            if has_items:
                return redirect('cashier_dashboard')
            else:
                order.delete()
    else:
        form = OrderForm()
    
    return render(request, 'orders/create_order_cashier.html', {
        'form': form,
        'products': products
    })

def kitchen_view(request):
    orders = Order.objects.filter(status__in=['received', 'topping']).order_by('created_at')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(Order, id=order_id, status__in=['received', 'topping'])
        next_status = request.POST.get('next_status')

        if not next_status:
            next_status = 'topping' if order.status == 'received' else 'ready'

        if order.status == 'received' and next_status == 'topping':
            order.status = 'topping'
        elif order.status == 'topping' and next_status == 'ready':
            order.status = 'ready'
        else:
            return redirect('kitchen_view')

        order.save()
        return redirect('kitchen_view')

    return render(request, 'orders/kitchen_view.html', {
        'orders': orders,
    })


def output_view(request):
    orders = Order.objects.filter(status='ready').order_by('created_at')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(Order, id=order_id, status='ready')
        order.status = 'completed'
        order.save()
        return redirect('output_view')

    return render(request, 'orders/kitchen_view.html', {
        'orders': orders,
        'page_title': 'Ausgabe',
        'page_subtitle': 'Person D übergibt die fertigen Bestellungen an den Kunden.',
        'button_label': 'Ausgegeben',
        'empty_message': 'Aktuell keine Bestellungen zur Ausgabe.',
        'card_border_class': 'border-primary',
        'header_class': 'bg-primary',
        'header_text_class': 'text-white',
        'button_class': 'btn-primary',
        'simple_ready_view': True,
    })

@staff_member_required
def analytics_view(request):
    from django.db.models.functions import ExtractHour
    from django.db.models import Count
    import json
    from django.core.serializers.json import DjangoJSONEncoder

    # 1. Detailed Table Data (Existing)
    stats = OrderItem.objects.annotate(date=TruncDate('order__created_at')) \
        .values('date', 'product__name') \
        .annotate(total_quantity=Sum('quantity'), total_revenue=Sum(F('quantity') * F('product__price'))) \
        .order_by('-date', 'product__name')

    # 2. Daily Revenue (Line Chart)
    daily_data = Order.objects.annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(revenue=Sum(F('items__quantity') * F('items__product__price'))) \
        .order_by('date')
    
    daily_labels = [d['date'] for d in daily_data]
    daily_values = [d['revenue'] for d in daily_data]

    # 3. Product Popularity (Pie/Bar Chart)
    product_data = OrderItem.objects.values('product__name') \
        .annotate(total_qty=Sum('quantity')) \
        .order_by('-total_qty')
    
    product_labels = [p['product__name'] for p in product_data]
    product_values = [p['total_qty'] for p in product_data]

    # 4. Hourly Activity (Bar Chart)
    hourly_data = Order.objects.annotate(hour=ExtractHour('created_at')) \
        .values('hour') \
        .annotate(count=Count('id')) \
        .order_by('hour')
    
    # Ensure all hours 0-23 are represented
    hours_dict = {h['hour']: h['count'] for h in hourly_data}
    hourly_labels = [f"{h}:00" for h in range(24)]
    hourly_values = [hours_dict.get(h, 0) for h in range(24)]

    context = {
        'stats': stats,
        'daily_labels': json.dumps(daily_labels, cls=DjangoJSONEncoder),
        'daily_values': json.dumps(daily_values, cls=DjangoJSONEncoder),
        'product_labels': json.dumps(product_labels),
        'product_values': json.dumps(product_values),
        'hourly_labels': json.dumps(hourly_labels),
        'hourly_values': json.dumps(hourly_values),
    }
    
    return render(request, 'orders/analytics.html', context)


