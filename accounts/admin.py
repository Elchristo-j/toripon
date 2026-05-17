from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Store, Staff


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Staff)
class StaffAdmin(UserAdmin):
    list_display = ['username', 'store', 'role', 'is_active']
    list_filter = ['role', 'store']
    fieldsets = UserAdmin.fieldsets + (
        ('店舗情報', {'fields': ('store', 'role')}),
    )
    