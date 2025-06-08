from django.contrib import admin
from .models import (
    UserRole, Staff, RoomType, Room,
    Booking, Service, BookingService,
    Bill, Feedback, Notification
)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'position', 'joining_date', 'salary')
    list_filter = ('department', 'position')
    search_fields = ('user__username', 'user__email')

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'capacity')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'status', 'floor')
    list_filter = ('room_type', 'status', 'floor')
    search_fields = ('room_number',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'room', 'check_in', 'check_out', 'status', 'total_price')
    list_filter = ('status', 'check_in', 'check_out')
    search_fields = ('user__username', 'room__room_number')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available')
    list_filter = ('is_available',)

@admin.register(BookingService)
class BookingServiceAdmin(admin.ModelAdmin):
    list_display = ('booking', 'service', 'quantity', 'service_date')
    list_filter = ('service',)

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('booking', 'room_charge', 'service_charge', 'tax', 'total', 'payment_status')
    list_filter = ('payment_status', 'payment_method')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'booking', 'rating', 'created_at', 'is_approved')
    list_filter = ('rating', 'is_approved')
    search_fields = ('user__username', 'comment')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'target_audience', 'is_active', 'created_at')
    list_filter = ('target_audience', 'is_active')
    search_fields = ('title', 'content')
