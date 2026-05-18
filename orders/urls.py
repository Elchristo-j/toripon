from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('table/<str:seat_code>/', views.order_menu, name='menu'),
    path('submit/', views.order_submit, name='submit'),
    path('staff/', views.staff_order_list, name='staff_order_list'),
    path('staff/merge/', views.staff_order_merge, name='staff_order_merge'),
    path('staff/close/', views.staff_order_close, name='staff_order_close'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('produce/staff/', views.produce_staff_list, name='produce_staff_list'),
    path('produce/staff/action/', views.produce_staff_action, name='produce_staff_action'),
]
