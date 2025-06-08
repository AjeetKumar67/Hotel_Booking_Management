from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from functools import wraps
import datetime
import weasyprint
import tempfile

from .models import (
    UserRole, Staff, Room, RoomType, 
    Booking, Service, BookingService, 
    Bill, Feedback, Notification
)

from .forms import (
    UserRegisterForm, UserUpdateForm, UserRoleForm,
    RoomForm, RoomTypeForm, BookingForm, CheckInOutForm,
    ServiceForm, BookingServiceForm, BillForm,
    FeedbackForm, NotificationForm
)

# ========== Helper Functions ==========
def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                if request.user.userrole.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
            except:
                pass
            return HttpResponseForbidden("You don't have permission to access this page.")
        return _wrapped_view
    return decorator

# ========== User Management Views ==========
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Set role to guest by default
            user_role = UserRole.objects.get(user=user)
            user_role.role = UserRole.GUEST
            user_role.save()
            messages.success(request, f'Your account has been created! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        r_form = UserRoleForm(request.POST, request.FILES, instance=request.user.userrole)
        
        if u_form.is_valid() and r_form.is_valid():
            u_form.save()
            r_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        r_form = UserRoleForm(instance=request.user.userrole)
        
    context = {
        'u_form': u_form,
        'r_form': r_form,
    }
    return render(request, 'users/profile.html', context)

@login_required
def dashboard(request):
    user_role = request.user.userrole.role
    
    context = {
        'user_role': user_role,
    }
    
    if user_role == UserRole.ADMIN:
        # Admin dashboard data
        context['total_users'] = User.objects.count()
        context['total_guests'] = UserRole.objects.filter(role=UserRole.GUEST).count()
        context['total_staff'] = Staff.objects.count()
        context['recent_bookings'] = Booking.objects.order_by('-booking_date')[:5]
        return render(request, 'users/dashboard_admin.html', context)
    
    elif user_role == UserRole.RECEPTIONIST:
        # Receptionist dashboard data
        context['pending_bookings'] = Booking.objects.filter(status=Booking.PENDING).count()
        context['checked_in_guests'] = Booking.objects.filter(status=Booking.CHECKED_IN).count()
        context['today_checkouts'] = Booking.objects.filter(check_out=datetime.date.today(), status=Booking.CHECKED_IN).count()
        context['bookings'] = Booking.objects.order_by('-booking_date')[:10]
        return render(request, 'users/dashboard_receptionist.html', context)
    
    else:  # Guest or default
        # Guest dashboard data
        context['bookings'] = Booking.objects.filter(user=request.user).order_by('-booking_date')
        context['notifications'] = Notification.objects.filter(target_audience__in=[Notification.ALL, Notification.GUEST], is_active=True)[:5]
        return render(request, 'users/dashboard_guest.html', context)

class StaffListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Staff
    template_name = 'users/staff_list.html'
    context_object_name = 'staffs'
    
    def test_func(self):
        return hasattr(self.request.user, 'userrole') and self.request.user.userrole.role == UserRole.ADMIN

# ========== Room Management Views ==========
class RoomListView(ListView):
    model = Room
    template_name = 'rooms/room_list.html'
    context_object_name = 'rooms'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room_types'] = RoomType.objects.all()
        return context

class RoomDetailView(DetailView):
    model = Room
    template_name = 'rooms/room_detail.html'

@login_required
@role_required([UserRole.ADMIN, UserRole.RECEPTIONIST])
def create_room(request):
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room created successfully!')
            return redirect('room-list')
    else:
        form = RoomForm()
    return render(request, 'rooms/room_form.html', {'form': form})

@login_required
@role_required([UserRole.ADMIN, UserRole.RECEPTIONIST])
def update_room(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room updated successfully!')
            return redirect('room-detail', pk=room.pk)
    else:
        form = RoomForm(instance=room)
    return render(request, 'rooms/room_form.html', {'form': form, 'room': room})

@login_required
@role_required([UserRole.ADMIN])
def delete_room(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Room deleted successfully!')
        return redirect('room-list')
    return render(request, 'rooms/room_confirm_delete.html', {'room': room})

@login_required
@role_required([UserRole.ADMIN])
def create_room_type(request):
    if request.method == 'POST':
        form = RoomTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room type created successfully!')
            return redirect('room-list')
    else:
        form = RoomTypeForm()
    return render(request, 'rooms/room_type_form.html', {'form': form})

# ========== Booking Management Views ==========
class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        user_role = self.request.user.userrole.role
        if user_role in [UserRole.ADMIN, UserRole.RECEPTIONIST]:
            return Booking.objects.all().order_by('-booking_date')
        else:
            return Booking.objects.filter(user=self.request.user).order_by('-booking_date')

class BookingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    
    def test_func(self):
        booking = self.get_object()
        user_role = self.request.user.userrole.role
        return user_role in [UserRole.ADMIN, UserRole.RECEPTIONIST] or booking.user == self.request.user

@login_required
def create_booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            
            # Calculate total price
            booking.total_price = booking.calculate_total_price()
            
            # Update room status
            room = booking.room
            room.status = Room.BOOKED
            room.save()
            
            booking.save()
            messages.success(request, 'Booking created successfully!')
            return redirect('booking-detail', pk=booking.pk)
    else:
        form = BookingForm()
        # Only show available rooms
        form.fields['room'].queryset = Room.objects.filter(status=Room.AVAILABLE)
    
    return render(request, 'bookings/booking_form.html', {'form': form})

@login_required
@role_required([UserRole.ADMIN, UserRole.RECEPTIONIST])
def check_in_out(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    
    if request.method == 'POST':
        form = CheckInOutForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            
            if action == 'check_in':
                booking.status = Booking.CHECKED_IN
                booking.room.status = Room.BOOKED
                booking.room.save()
                messages.success(request, 'Guest has been checked in successfully!')
            elif action == 'check_out':
                booking.status = Booking.CHECKED_OUT
                booking.room.status = Room.AVAILABLE
                booking.room.save()
                
                # Create bill if it doesn't exist
                if not hasattr(booking, 'bill'):
                    bill = Bill(booking=booking)
                    bill.calculate_charges()
                    bill.save()
                
                messages.success(request, 'Guest has been checked out successfully!')
            
            booking.save()
            return redirect('booking-detail', pk=booking.pk)
    else:
        form = CheckInOutForm()
    
    return render(request, 'bookings/check_in_out.html', {'form': form, 'booking': booking})

@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    
    # Verify permission
    if booking.user != request.user and request.user.userrole.role not in [UserRole.ADMIN, UserRole.RECEPTIONIST]:
        messages.error(request, "You don't have permission to cancel this booking.")
        return redirect('booking-list')
    
    if request.method == 'POST':
        booking.status = Booking.CANCELLED
        booking.room.status = Room.AVAILABLE
        booking.room.save()
        booking.save()
        messages.success(request, 'Booking cancelled successfully!')
        return redirect('booking-list')
    
    return render(request, 'bookings/booking_confirm_cancel.html', {'booking': booking})

# ========== Service Management Views ==========
class ServiceListView(ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    
    def get_queryset(self):
        return Service.objects.filter(is_available=True)

@login_required
@role_required([UserRole.ADMIN, UserRole.RECEPTIONIST])
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service created successfully!')
            return redirect('service-list')
    else:
        form = ServiceForm()
    
    return render(request, 'services/service_form.html', {'form': form})

@login_required
@role_required([UserRole.ADMIN, UserRole.RECEPTIONIST])
def add_service_to_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        form = BookingServiceForm(request.POST)
        if form.is_valid():
            booking_service = form.save(commit=False)
            booking_service.booking = booking
            booking_service.save()
            
            messages.success(request, 'Service added to booking successfully!')
            return redirect('booking-detail', pk=booking.id)
    else:
        form = BookingServiceForm()
    
    return render(request, 'services/booking_service_form.html', {
        'form': form, 
        'booking': booking
    })

@login_required
@role_required([UserRole.ADMIN, UserRole.RECEPTIONIST])
def generate_bill(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if bill exists
    try:
        bill = Bill.objects.get(booking=booking)
    except Bill.DoesNotExist:
        # Create new bill
        bill = Bill(booking=booking)
        bill.calculate_charges()
        bill.save()
    
    if request.method == 'POST':
        form = BillForm(request.POST, instance=bill)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.payment_status = Bill.PAID
            bill.paid_at = timezone.now()
            bill.save()
            
            messages.success(request, 'Payment processed successfully!')
            return redirect('invoice', bill_id=bill.id)
    else:
        form = BillForm(instance=bill)
    
    return render(request, 'services/bill.html', {
        'bill': bill,
        'form': form
    })

@login_required
def invoice(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    
    # Check if user is authorized to view this bill
    if not (request.user.userrole.role in [UserRole.ADMIN, UserRole.RECEPTIONIST] or bill.booking.user == request.user):
        messages.error(request, "You don't have permission to view this invoice.")
        return redirect('dashboard')
    
    return render(request, 'services/invoice.html', {'bill': bill})

@login_required
def download_invoice(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    
    # Check if user is authorized to download this bill
    if not (request.user.userrole.role in [UserRole.ADMIN, UserRole.RECEPTIONIST] or bill.booking.user == request.user):
        messages.error(request, "You don't have permission to download this invoice.")
        return redirect('dashboard')
    
    # Render the invoice template to string
    html_string = render_to_string('services/invoice_pdf.html', {'bill': bill})
    
    # Create a PDF file
    html = weasyprint.HTML(string=html_string)
    result = html.write_pdf()
    
    # Generate response
    response = HttpResponse(result, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=invoice_{bill.id}.pdf'
    
    return response

# ========== Feedback Views ==========
class FeedbackListView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = 'feedback/feedback_list.html'
    context_object_name = 'feedbacks'
    
    def get_queryset(self):
        if self.request.user.userrole.role in [UserRole.ADMIN, UserRole.RECEPTIONIST]:
            return Feedback.objects.all()
        else:
            return Feedback.objects.filter(is_approved=True)

@login_required
def create_feedback(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if the booking belongs to the current user
    if booking.user != request.user:
        messages.error(request, "You don't have permission to leave feedback for this booking.")
        return redirect('booking-list')
    
    # Check if feedback already exists
    existing_feedback = Feedback.objects.filter(booking=booking, user=request.user).first()
    if existing_feedback:
        messages.info(request, "You've already submitted feedback for this booking.")
        return redirect('feedback-list')
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.booking = booking
            feedback.user = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('feedback-list')
    else:
        form = FeedbackForm()
    
    return render(request, 'feedback/feedback_form.html', {'form': form, 'booking': booking})

@login_required
@role_required([UserRole.ADMIN, UserRole.RECEPTIONIST])
def approve_feedback(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)
    feedback.is_approved = True
    feedback.save()
    messages.success(request, 'Feedback approved successfully!')
    return redirect('feedback-list')

# ========== Notification Views ==========
class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    
    def get_queryset(self):
        user_role = self.request.user.userrole.role
        
        if user_role == UserRole.ADMIN:
            # Admin sees all notifications
            return Notification.objects.all().order_by('-created_at')
        
        elif user_role == UserRole.RECEPTIONIST:
            # Receptionist sees staff and all notifications
            return Notification.objects.filter(
                target_audience__in=[Notification.STAFF, Notification.ALL],
                is_active=True
            ).order_by('-created_at')
        
        else:  # Guest
            # Guest sees guest and all notifications
            return Notification.objects.filter(
                target_audience__in=[Notification.GUEST, Notification.ALL],
                is_active=True
            ).order_by('-created_at')

@login_required
@role_required([UserRole.ADMIN])
def create_notification(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.created_by = request.user
            notification.save()
            messages.success(request, 'Notification created successfully!')
            return redirect('notification-list')
    else:
        form = NotificationForm()
    
    return render(request, 'notifications/notification_form.html', {'form': form})

@login_required
@role_required([UserRole.ADMIN])
def update_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    
    if request.method == 'POST':
        form = NotificationForm(request.POST, instance=notification)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification updated successfully!')
            return redirect('notification-list')
    else:
        form = NotificationForm(instance=notification)
    
    return render(request, 'notifications/notification_form.html', {
        'form': form,
        'notification': notification
    })

@login_required
@role_required([UserRole.ADMIN])
def delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted successfully!')
        return redirect('notification-list')
    
    return render(request, 'notifications/notification_confirm_delete.html', {
        'notification': notification
    })
