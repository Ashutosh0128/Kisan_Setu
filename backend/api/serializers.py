from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Equipment, Booking, ContactMessage

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['role', 'is_approved']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'profile']
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {
                'required': True,
                # 3. We remove UniqueValidator to let our validate_username handle auto-generation
                'validators': [] 
            },
            'email': {'required': True}
        }

    def validate_username(self, value):
        # 2. Trim whitespace
        username = value.strip()
        
        # 3. Case-insensitive check
        if User.objects.filter(username__iexact=username).exists():
            # 5. Optionally auto-generate a unique username
            base_username = username
            counter = 1
            while User.objects.filter(username__iexact=f"{base_username}{counter}").exists():
                counter += 1
            return f"{base_username}{counter}"
        
        return username

    def validate_email(self, value):
        # 2. Trim whitespace
        email = value.strip()
        
        # 6. Ensure email can also be checked for duplicates
        if User.objects.filter(email__iexact=email).exists():
            # 4. Return a clean error message
            raise serializers.ValidationError("A user with this email already exists.")
        
        return email

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        # Use create_user to properly hash password
        user = User.objects.create_user(**validated_data)
        
        # 7. Use update since a Profile is auto-created by signals in models.py
        # This avoids IntegrityError (500)
        Profile.objects.filter(user=user).update(**profile_data)
        
        return user

class UserManagementSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)
    is_approved = serializers.BooleanField(source='profile.is_approved', read_only=True)
    name = serializers.CharField(source='first_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'role', 'is_approved']

class EquipmentSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.username')
    
    class Meta:
        model = Equipment
        fields = '__all__'
        read_only_fields = ['owner', 'status']

class BookingSerializer(serializers.ModelSerializer):
    equipment_name = serializers.ReadOnlyField(source='equipment.name')
    farmer_name = serializers.ReadOnlyField(source='farmer.username')

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['farmer', 'status', 'created_at']

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'
