from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # User Management
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('staff/', views.StaffListView.as_view(), name='staff-list'),
    
    # Room Management
    path('rooms/', views.RoomListView.as_view(), name='room-list'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room-detail'),
    path('rooms/new/', views.create_room, name='room-create'),
    path('rooms/<int:pk>/update/', views.update_room, name='room-update'),
    path('rooms/<int:pk>/delete/', views.delete_room, name='room-delete'),
    path('rooms/type/new/', views.create_room_type, name='room-type-create'),
    
    # Booking Management
    path('bookings/', views.BookingListView.as_view(), name='booking-list'),
    path('bookings/<int:pk>/', views.BookingDetailView.as_view(), name='booking-detail'),
    path('bookings/new/', views.create_booking, name='booking-create'),
    path('bookings/<int:pk>/check-in-out/', views.check_in_out, name='check-in-out'),
    path('bookings/<int:pk>/cancel/', views.cancel_booking, name='booking-cancel'),
    
    # Service Management
    path('services/', views.ServiceListView.as_view(), name='service-list'),
    path('services/new/', views.service_create, name='service-create'),
    path('services/booking/<int:booking_id>/add/', views.add_service_to_booking, name='add-service-to-booking'),
    path('services/booking/<int:booking_id>/bill/', views.generate_bill, name='generate-bill'),
    path('services/bill/<int:bill_id>/invoice/', views.invoice, name='invoice'),
    path('services/bill/<int:bill_id>/download/', views.download_invoice, name='download-invoice'),
    
    # Feedback
    path('feedback/', views.FeedbackListView.as_view(), name='feedback-list'),
    path('feedback/booking/<int:booking_id>/create/', views.create_feedback, name='feedback-create'),
    path('feedback/<int:pk>/approve/', views.approve_feedback, name='feedback-approve'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/new/', views.create_notification, name='notification-create'),
    path('notifications/<int:pk>/update/', views.update_notification, name='notification-update'),
    path('notifications/<int:pk>/delete/', views.delete_notification, name='notification-delete'),
]
