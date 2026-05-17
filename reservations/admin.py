"""
reservations/admin.py
"""

from django.contrib import admin
from .models import (
    SeatSection, Seat, SeatLink,
    Reservation, ReservationSeat, TimeSlot,
)


# ── Seat をインラインで SeatSection に表示 ──
class SeatInline(admin.TabularInline):
    model  = Seat
    extra  = 1
    fields = ("code", "capacity", "can_merge", "is_active", "sort_order")


@admin.register(SeatSection)
class SeatSectionAdmin(admin.ModelAdmin):
    list_display  = ("name", "section_type", "store", "sort_order")
    list_filter   = ("section_type", "store")
    inlines       = [SeatInline]


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display  = ("code", "section", "capacity", "can_merge", "is_active")
    list_filter   = ("section__section_type", "can_merge", "is_active")
    search_fields = ("code",)


@admin.register(SeatLink)
class SeatLinkAdmin(admin.ModelAdmin):
    list_display  = ("seat_a", "seat_b", "description")


# ── ReservationSeat をインラインで Reservation に表示 ──
class ReservationSeatInline(admin.TabularInline):
    model      = ReservationSeat
    extra      = 1
    fields     = ("seat", "is_primary")
    raw_id_fields = ("seat",)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display   = (
        "start_at", "guest_name", "party_size",
        "status", "channel", "seat_codes_display",
    )
    list_filter    = ("status", "channel", "store")
    search_fields  = ("guest_name", "guest_phone", "guest_email")
    date_hierarchy = "start_at"
    inlines        = [ReservationSeatInline]
    readonly_fields = ("ai_check_result", "created_at", "updated_at")

    def seat_codes_display(self, obj):
        return ", ".join(obj.seat_codes) or "（未割当）"
    seat_codes_display.short_description = "席"


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ("store", "start_time", "label", "is_active")
    list_filter  = ("store", "is_active")
