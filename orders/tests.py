from django.test import TestCase

from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .forms import OrderForm
from .models import Order, OrderItem, Product


class OrderFormTests(TestCase):
	def test_form_saves_paid_status_from_intake(self):
		form = OrderForm(data={
			'order_type': 'regular',
			'customer_name': 'Anna',
			'notes': 'Ohne Zwiebeln',
		})

		self.assertTrue(form.is_valid())
		order = form.save()

		self.assertTrue(order.is_paid)

	def test_name_required_for_kjgler_and_purchase_orders(self):
		kjgler_form = OrderForm(data={
			'order_type': 'kjgler',
			'customer_name': '',
			'notes': '',
		})
		purchase_form = OrderForm(data={
			'order_type': 'purchase',
			'customer_name': '',
			'notes': '',
		})

		self.assertFalse(kjgler_form.is_valid())
		self.assertIn('customer_name', kjgler_form.errors)
		self.assertFalse(purchase_form.is_valid())
		self.assertIn('customer_name', purchase_form.errors)


class StationWorkflowTests(TestCase):
	def setUp(self):
		self.product = Product.objects.create(name='Salami', price='8.50', purchase_price='5.00', category='pizza')

	def test_analytics_view_is_accessible_without_login(self):
		response = self.client.get(reverse('analytics_view'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Auswertung')

	def test_cashier_order_stores_item_note_per_product(self):
		response = self.client.post(reverse('create_order_cashier'), {
			'order_type': 'regular',
			'customer_name': 'Lina',
			'notes': 'Bitte schnell',
			f'product_{self.product.id}': '2',
			f'product_note_{self.product.id}': 'ohne Zwiebeln',
		})

		self.assertRedirects(response, reverse('cashier_dashboard'))
		order = Order.objects.latest('id')
		item = order.items.get(product=self.product)
		self.assertEqual(item.quantity, 2)
		self.assertEqual(item.notes, 'ohne Zwiebeln')

	def test_kjgler_order_is_free(self):
		response = self.client.post(reverse('create_order_cashier'), {
			'order_type': 'kjgler',
			'customer_name': 'Tom',
			'notes': '',
			f'product_{self.product.id}': '2',
		})

		self.assertRedirects(response, reverse('cashier_dashboard'))
		order = Order.objects.latest('id')
		self.assertEqual(order.order_type, 'kjgler')
		self.assertEqual(order.total_price(), 0)

	def test_purchase_order_uses_purchase_price(self):
		response = self.client.post(reverse('create_order_cashier'), {
			'order_type': 'purchase',
			'customer_name': 'Partner X',
			'notes': '',
			f'product_{self.product.id}': '3',
		})

		self.assertRedirects(response, reverse('cashier_dashboard'))
		order = Order.objects.latest('id')
		self.assertEqual(order.order_type, 'purchase')
		self.assertEqual(float(order.total_price()), 15.0)

	def create_order(self, status):
		order = Order.objects.create(customer_name='Max', status=status, is_paid=True)
		OrderItem.objects.create(order=order, product=self.product, quantity=1)
		return order

	def test_topping_board_advances_received_orders_to_topping(self):
		order = self.create_order('received')

		response = self.client.post(reverse('kitchen_view'), {'order_id': order.id})

		self.assertRedirects(response, reverse('kitchen_view'))
		order.refresh_from_db()
		self.assertEqual(order.status, 'topping')

	def test_topping_board_advances_topping_orders_to_ready(self):
		order = self.create_order('topping')

		response = self.client.post(reverse('kitchen_view'), {'order_id': order.id})

		self.assertRedirects(response, reverse('kitchen_view'))
		order.refresh_from_db()
		self.assertEqual(order.status, 'ready')

	def test_output_board_advances_ready_orders_to_completed(self):
		order = self.create_order('ready')

		response = self.client.post(reverse('output_view'), {'order_id': order.id})

		self.assertRedirects(response, reverse('output_view'))
		order.refresh_from_db()
		self.assertEqual(order.status, 'completed')
		self.assertIsNotNone(order.completed_at)

	def test_station_view_rejects_wrong_status(self):
		order = self.create_order('ready')

		response = self.client.post(reverse('kitchen_view'), {'order_id': order.id})

		self.assertEqual(response.status_code, 404)
		order.refresh_from_db()
		self.assertEqual(order.status, 'ready')

	def test_cashier_can_mark_unpaid_order_as_paid(self):
		order = Order.objects.create(customer_name='Nora', status='completed', is_paid=False)
		OrderItem.objects.create(order=order, product=self.product, quantity=1)

		response = self.client.post(reverse('cashier_dashboard'), {
			'action': 'mark_paid',
			'order_id': str(order.id),
		})

		self.assertRedirects(response, reverse('cashier_dashboard'))
		order.refresh_from_db()
		self.assertTrue(order.is_paid)

	def test_analytics_contains_average_completion_minutes(self):
		order = Order.objects.create(customer_name='Eva', status='completed', is_paid=True)
		OrderItem.objects.create(order=order, product=self.product, quantity=2)
		Order.objects.filter(id=order.id).update(
			created_at=timezone.now() - timedelta(minutes=20),
			completed_at=timezone.now() - timedelta(minutes=5),
		)

		response = self.client.get(reverse('analytics_view'))

		self.assertEqual(response.status_code, 200)
		self.assertIsNotNone(response.context['avg_completion_minutes'])
		self.assertAlmostEqual(response.context['avg_completion_minutes'], 15.0, places=1)
