from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('owner', 'Owner'),
        ('admin', 'Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='farmer')
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Equipment(models.Model):
    CATEGORY_CHOICES = [
        ('Tractor', 'Tractor'),
        ('Harvester', 'Harvester'),
        ('Implements', 'Implements'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
    ]
    
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.IntegerField() # Price per day
    image = models.URLField(max_length=500, default="https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&q=80&w=800")
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipment')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Booking(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    duration_days = models.IntegerField()
    total_price = models.IntegerField()
    status = models.CharField(max_length=20, default='Confirmed')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipment.name} booked by {self.farmer.username}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.email}"

# Signals to create Profile automatically
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
