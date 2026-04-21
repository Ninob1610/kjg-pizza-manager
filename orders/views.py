from django.shortcuts import render, redirect, get_object_or_404
from types import SimpleNamespace

from .models import Product, Order, OrderItem, OrderItemStatusLog
from .forms import OrderForm, OrderItemFormSet
from django.db.models import Sum, F, DurationField, ExpressionWrapper, Q
from django.db.models.functions import TruncDate


def _apply_item_action(item, action):
    action_map = {
        'start': ('topping', 'start'),
        'ready': ('ready', 'ready'),
        'complete': ('completed', 'complete'),
        'fail': ('failed', 'fail'),
        'reset': ('received', 'reset'),
    }

    if action not in action_map:
        return False

    new_status, log_action = action_map[action]
    return item.change_status(new_status, log_action)


def _bulk_advance_order(order, next_status):
    if next_status == 'topping':
        for item in order.items.exclude(status='completed').filter(status='received'):
            item.change_status('topping', 'start')
    elif next_status == 'ready':
        for item in order.items.exclude(status='completed').filter(status='topping'):
            item.change_status('ready', 'ready')

    order.recalculate_status()


def _build_display_orders(orders, mode):
    display_orders = []

    for order in orders:
        visible_items = []

        for item in order.items.all():
            if mode == 'kitchen' and item.status in ['ready', 'completed']:
                continue
            if mode == 'output' and item.status != 'ready':
                continue

            visible_items.append(item)

        if visible_items:
            display_orders.append(SimpleNamespace(order=order, items=visible_items))

    return display_orders

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
    if request.method == 'POST':
        action = request.POST.get('action')
        order_id = request.POST.get('order_id')

        if action == 'mark_paid' and order_id:
            order = get_object_or_404(Order, id=order_id, is_paid=False)
            order.is_paid = True
            order.save(update_fields=['is_paid'])

        return redirect('cashier_dashboard')

    # Completed orders stay visible until they are paid.
    orders = Order.objects.exclude(status='completed', is_paid=True).order_by('-created_at')

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
    orders = Order.objects.exclude(status='completed').order_by('created_at')

    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        item_action = request.POST.get('item_action')
        order_id = request.POST.get('order_id')
        next_status = request.POST.get('next_status')

        if item_id and item_action:
            item = get_object_or_404(OrderItem.objects.select_related('order'), id=item_id, order__status__in=['received', 'topping', 'ready'])
            _apply_item_action(item, item_action)
            return redirect('kitchen_view')

        if not order_id:
            return redirect('kitchen_view')

        order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id, status__in=['received', 'topping', 'ready'])

        if not next_status:
            next_status = 'topping' if order.status == 'received' else 'ready'

        if order.status == 'received' and next_status == 'topping':
            _bulk_advance_order(order, 'topping')
        elif order.status in ['received', 'topping'] and next_status == 'ready':
            _bulk_advance_order(order, 'ready')
        else:
            return redirect('kitchen_view')

        return redirect('kitchen_view')

    return render(request, 'orders/kitchen_view.html', {
        'orders': _build_display_orders(orders, 'kitchen'),
        'failed_logs': OrderItemStatusLog.objects.filter(action='fail').select_related('order_item__order', 'order_item__product').order_by('-created_at')[:10],
    })


def output_view(request):
    orders = Order.objects.filter(status='ready').order_by('created_at')

    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        item_action = request.POST.get('item_action')
        order_id = request.POST.get('order_id')
        if item_id and item_action:
            item = get_object_or_404(OrderItem.objects.select_related('order'), id=item_id, order__status='ready')
            _apply_item_action(item, item_action)
            return redirect('output_view')

        if not order_id:
            return redirect('output_view')

        order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id, status='ready')
        for item in order.items.filter(status='ready'):
            item.change_status('completed', 'complete')
        return redirect('output_view')

    return render(request, 'orders/kitchen_view.html', {
        'orders': _build_display_orders(orders, 'output'),
        'page_title': 'Ausgabe',
        'page_subtitle': 'Person D übergibt die fertigen Bestellungen an den Kunden.',
        'button_label': 'Ausgegeben',
        'empty_message': 'Aktuell keine Bestellungen zur Ausgabe.',
        'card_border_class': 'border-primary',
        'header_class': 'bg-primary',
        'header_text_class': 'text-white',
        'button_class': 'btn-primary',
        'simple_ready_view': True,
        'failed_logs': OrderItemStatusLog.objects.filter(action='fail').select_related('order_item__order', 'order_item__product').order_by('-created_at')[:10],
    })

def analytics_view(request):
    from django.db.models.functions import ExtractHour
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

    # 4. Pizza Quantity by Hour and Product (Stacked Bar Chart)
    hourly_pizza_data = OrderItem.objects.filter(product__category='pizza') \
        .annotate(hour=ExtractHour('order__created_at')) \
        .values('hour', 'product__name') \
        .annotate(total_qty=Sum('quantity')) \
        .order_by('product__name', 'hour')

    hourly_pizza_labels = [f"{h}:00" for h in range(24)]
    pizza_series = {}
    for row in hourly_pizza_data:
        hour = row['hour']
        if hour is None:
            continue
        product_name = row['product__name']
        if product_name not in pizza_series:
            pizza_series[product_name] = [0] * 24
        pizza_series[product_name][hour] = row['total_qty']

    pizza_colors = [
        '#006d84',
        '#00b6be',
        '#E30613',
        '#198754',
        '#fd7e14',
        '#6f42c1',
        '#0d6efd',
        '#ffc107',
    ]

    hourly_pizza_datasets = []
    for index, product_name in enumerate(sorted(pizza_series.keys())):
        hourly_pizza_datasets.append({
            'label': product_name,
            'data': pizza_series[product_name],
            'backgroundColor': pizza_colors[index % len(pizza_colors)],
            'stack': 'pizza',
        })

    # 5. Average Duration per Pizza from Order Creation to Completion
    duration_expression = ExpressionWrapper(
        F('completed_at') - F('created_at'),
        output_field=DurationField(),
    )
    completed_orders = Order.objects.filter(
        status='completed',
        completed_at__isnull=False,
    ).annotate(
        duration=duration_expression,
        pizza_qty=Sum('items__quantity', filter=Q(items__product__category='pizza')),
    )

    avg_completion_minutes = None
    total_pizza_duration_seconds = 0
    total_pizza_count = 0
    for order in completed_orders:
        if not order.duration or not order.pizza_qty:
            continue
        total_pizza_duration_seconds += order.duration.total_seconds() * order.pizza_qty
        total_pizza_count += order.pizza_qty

    if total_pizza_count > 0:
        avg_completion_minutes = round((total_pizza_duration_seconds / total_pizza_count) / 60, 1)

    context = {
        'stats': stats,
        'daily_labels': json.dumps(daily_labels, cls=DjangoJSONEncoder),
        'daily_values': json.dumps(daily_values, cls=DjangoJSONEncoder),
        'product_labels': json.dumps(product_labels),
        'product_values': json.dumps(product_values),
        'hourly_pizza_labels': json.dumps(hourly_pizza_labels),
        'hourly_pizza_datasets': json.dumps(hourly_pizza_datasets),
        'avg_completion_minutes': avg_completion_minutes,
    }
    
    return render(request, 'orders/analytics.html', context)


