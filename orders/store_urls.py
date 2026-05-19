from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('table/<str:seat_code>/', views.order_menu, name='menu'),
    path('produce/', views.produce_order_form, name='produce_form'),
    path('produce/order/', views.produce_order_submit, name='produce_submit'),
    path('delivery/', views.delivery_order_form, name='delivery_form'),
    path('delivery/order/', views.delivery_order_submit, name='delivery_submit'),
]
