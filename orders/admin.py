from django.contrib import admin
from .models import MenuCategory, MenuItem, Order, OrderItem


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ['name', 'price', 'order', 'is_available']


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_editable = ['order']
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'order', 'is_available']
    list_editable = ['price', 'order', 'is_available']
    list_filter = ['category', 'is_available']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['menu_item', 'quantity', 'status']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['pk', 'seat_code', 'group_id', 'status', 'created_at']
    list_filter = ['status']
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'quantity', 'status', 'order', 'created_at']
    list_filter = ['status']