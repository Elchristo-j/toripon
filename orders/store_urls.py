from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('table/<str:seat_code>/', views.order_menu, name='menu'),
    path('produce/', views.produce_order_form, name='produce_form'),
    path('produce/order/', views.produce_order_submit, name='produce_submit'),
]
