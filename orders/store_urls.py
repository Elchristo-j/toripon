from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('table/<str:seat_code>/', views.order_menu, name='menu'),
]
