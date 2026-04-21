from django.test import TestCase

from django.urls import reverse

from .forms import OrderForm
from .models import Order, OrderItem, Product


class OrderFormTests(TestCase):
	def test_form_saves_paid_status_from_intake(self):
		form = OrderForm(data={
			'customer_name': 'Anna',
			'notes': 'Ohne Zwiebeln',
		})

		self.assertTrue(form.is_valid())
		order = form.save()

		self.assertTrue(order.is_paid)


class StationWorkflowTests(TestCase):
	def setUp(self):
		self.product = Product.objects.create(name='Salami', price='8.50', category='pizza')

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

	def test_station_view_rejects_wrong_status(self):
		order = self.create_order('ready')

		response = self.client.post(reverse('kitchen_view'), {'order_id': order.id})

		self.assertEqual(response.status_code, 404)
		order.refresh_from_db()
		self.assertEqual(order.status, 'ready')
