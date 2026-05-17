from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('new/',              views.reservation_create,        name='create'),
    path('staff/new/',        views.staff_reservation_create,  name='staff_create'),
    path('staff/list/',       views.staff_reservation_list,    name='staff_list'),
    path('staff/floor/',      views.staff_floor_map,           name='staff_floor'),
    path('staff/<int:pk>/',   views.staff_reservation_detail,  name='staff_detail'),
]
