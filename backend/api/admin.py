from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile, Equipment, Booking, ContactMessage

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profiles'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role', 'get_is_approved')
    
    @admin.display(description='Role', ordering='profile__role')
    def get_role(self, instance):
        return instance.profile.role if hasattr(instance, 'profile') else 'farmer'

    @admin.display(description='Approved', boolean=True, ordering='profile__is_approved')
    def get_is_approved(self, instance):
        return instance.profile.is_approved if hasattr(instance, 'profile') else False

    actions = ['approve_users']

    @admin.action(description='Approve selected users (Equipment Owners)')
    def approve_users(self, request, queryset):
        for user in queryset:
            if hasattr(user, 'profile'):
                user.profile.is_approved = True
                user.profile.save()

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Keep standard Profile registration as a fallback if needed
@admin.action(description='Approve selected users')
def approve_profiles(modeladmin, request, queryset):
    queryset.update(is_approved=True)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_approved')
    actions = [approve_profiles]

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Equipment)
admin.site.register(Booking)
admin.site.register(ContactMessage)
