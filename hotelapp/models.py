from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

class UserRole(models.Model):
    ADMIN = 'admin'
    RECEPTIONIST = 'receptionist'
    GUEST = 'guest'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (RECEPTIONIST, 'Receptionist'),
        (GUEST, 'Guest'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=GUEST)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics', default='default.jpg', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    def is_admin(self):
        return self.role == self.ADMIN
    
    def is_receptionist(self):
        return self.role == self.RECEPTIONIST
    
    def is_guest(self):
        return self.role == self.GUEST

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    joining_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.user.username} - {self.position}"

class RoomType(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    amenities = models.TextField()
    capacity = models.IntegerField()
    
    def __str__(self):
        return f"{self.name} - ${self.price}"

class Room(models.Model):
    AVAILABLE = 'available'
    BOOKED = 'booked'
    MAINTENANCE = 'maintenance'
    
    STATUS_CHOICES = [
        (AVAILABLE, 'Available'),
        (BOOKED, 'Booked'),
        (MAINTENANCE, 'Maintenance'),
    ]
    
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=AVAILABLE)
    floor = models.IntegerField()
    image = models.ImageField(upload_to='room_images/', default='room_default.jpg')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Room {self.room_number} - {self.room_type.name} - {self.status}"
    
    @property
    def price(self):
        return self.room_type.price

class Booking(models.Model):
    PENDING = 'pending'
    CHECKED_IN = 'checked_in'
    CHECKED_OUT = 'checked_out'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CHECKED_IN, 'Checked In'),
        (CHECKED_OUT, 'Checked Out'),
        (CANCELLED, 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    guest_count = models.IntegerField()
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    special_requests = models.TextField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Booking {self.id} - {self.user.username} - Room {self.room.room_number}"
    
    def clean(self):
        # Check if check_out is after check_in
        if self.check_in is not None and self.check_out is not None:
            if self.check_out <= self.check_in:
                raise ValidationError("Check-out date must be after check-in date")
        
        # Check for booking conflicts
        if self.room_id is not None and self.check_in is not None and self.check_out is not None:
            overlapping_bookings = Booking.objects.filter(
                room_id=self.room_id,
                status__in=[self.PENDING, self.CHECKED_IN],
            ).exclude(id=self.id)
            
            for booking in overlapping_bookings:
                if (self.check_in <= booking.check_out and self.check_out >= booking.check_in):
                    raise ValidationError(f"The room is already booked during this period ({booking.check_in} to {booking.check_out})")
    
    def calculate_total_price(self):
        # Check if we have valid data
        if self.check_in is None or self.check_out is None or self.room is None:
            return 0
            
        # Calculate days
        delta = self.check_out - self.check_in
        days = delta.days
        if days <= 0:
            days = 1
        
        room_price = self.room.price * days
        return room_price
    
    def save(self, *args, **kwargs):
        # Calculate total price if not already set
        if not self.total_price and self.room is not None and self.check_in is not None and self.check_out is not None:
            self.total_price = self.calculate_total_price()
        
        # Update room status
        if self.status == self.CHECKED_IN and self.room is not None:
            self.room.status = Room.BOOKED
            self.room.save()
        elif self.status == self.CHECKED_OUT and self.room is not None:
            self.room.status = Room.AVAILABLE
            self.room.save()
            
        super().save(*args, **kwargs)

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - ${self.price}"

class BookingService(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    service_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    @property
    def total_price(self):
        return self.service.price * self.quantity
    
    def __str__(self):
        return f"{self.booking.id} - {self.service.name} x{self.quantity}"

class Bill(models.Model):
    CASH = 'cash'
    CARD = 'card'
    UPI = 'upi'
    
    PAYMENT_CHOICES = [
        (CASH, 'Cash'),
        (CARD, 'Card'),
        (UPI, 'UPI'),
    ]
    
    PENDING = 'pending'
    PAID = 'paid'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PAID, 'Paid'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    room_charge = models.DecimalField(max_digits=10, decimal_places=2)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, null=True, blank=True)
    payment_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    generated_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Bill for Booking {self.booking.id} - {self.total}"
    
    def calculate_charges(self):
        # Room charge is already in booking.total_price
        self.room_charge = self.booking.total_price
        
        # Calculate service charges
        services_total = sum(bs.total_price for bs in self.booking.services.all())
        self.service_charge = services_total
        
        # Calculate tax (assuming 18%)
        subtotal = self.room_charge + self.service_charge
        self.tax = subtotal * 0.18
        
        # Calculate total
        self.total = subtotal + self.tax
        
        return self.total
    
    def save(self, *args, **kwargs):
        if not self.total:
            self.calculate_charges()
        
        super().save(*args, **kwargs)

class Feedback(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback by {self.user.username} - Rating: {self.rating}"

class Notification(models.Model):
    STAFF = 'staff'
    GUEST = 'guest'
    ALL = 'all'
    
    TARGET_CHOICES = [
        (STAFF, 'Staff Only'),
        (GUEST, 'Guests Only'),
        (ALL, 'All Users'),
    ]
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    target_audience = models.CharField(max_length=10, choices=TARGET_CHOICES, default=ALL)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - For: {self.target_audience}"
