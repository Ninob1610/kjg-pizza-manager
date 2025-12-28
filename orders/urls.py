from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_order, name='customer_order'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('kasse/', views.cashier_dashboard, name='cashier_dashboard'),
    path('kasse/neu/', views.create_order_cashier, name='create_order_cashier'),
    path('kueche/', views.kitchen_view, name='kitchen_view'),
    path('auswertung/', views.analytics_view, name='analytics_view'),
]
