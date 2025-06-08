from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import (
    UserRole, Room, RoomType, Booking, 
    Service, BookingService, Bill,
    Feedback, Notification
)

# User Forms
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserRole
        fields = ['role', 'phone', 'address', 'profile_picture']

# Room Forms
class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['name', 'price', 'description', 'amenities', 'capacity']

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'status', 'floor', 'image']

# Booking Forms
class DateInput(forms.DateInput):
    input_type = 'date'

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['room', 'check_in', 'check_out', 'guest_count', 'special_requests']
        widgets = {
            'check_in': DateInput(),
            'check_out': DateInput(),
        }
    
    def clean_check_in(self):
        check_in = self.cleaned_data.get('check_in')
        today = timezone.now().date()
        
        if check_in < today:
            raise forms.ValidationError("Check-in date cannot be in the past.")
        return check_in
    
    def clean_check_out(self):
        check_out = self.cleaned_data.get('check_out')
        check_in = self.cleaned_data.get('check_in')
        
        if check_in and check_out:
            if check_out < check_in:
                raise forms.ValidationError("Check-out date must be after check-in date.")
        return check_out

class CheckInOutForm(forms.Form):
    CHOICES = [
        ('check_in', 'Check In'),
        ('check_out', 'Check Out')
    ]
    action = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)

# Service Forms
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'price', 'is_available']

class BookingServiceForm(forms.ModelForm):
    class Meta:
        model = BookingService
        fields = ['service', 'quantity', 'notes']

class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['payment_method']

# Feedback Form
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')]),
            'comment': forms.Textarea(attrs={'rows': 5}),
        }

# Notification Form
class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'content', 'target_audience', 'is_active']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }
