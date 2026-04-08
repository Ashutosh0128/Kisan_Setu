from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from api.models import Profile
import json

def home(request):
    return render(request, 'index.html')

def signup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            password = data.get('password')
            full_name = data.get('name', '').strip()
            profile_data = data.get('profile', {})
            role = profile_data.get('role', 'farmer')

            # 1. Basic validation
            if not email or not password:
                return JsonResponse({'error': 'Email and password are required.'}, status=400)

            # 2. Email format validation
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({'error': 'Invalid email format.'}, status=400)

            # 3. Check duplicate user
            if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
                return JsonResponse({'error': 'A user with this email already exists.'}, status=400)

            # 4. Password strength validation
            try:
                validate_password(password)
            except ValidationError as e:
                return JsonResponse({'error': ' '.join(e.messages)}, status=400)

            # 5. Create user
            # We use email as username for simplicity and unique identification
            user = User.objects.create_user(username=email, email=email, password=password)
            user.first_name = full_name
            user.save()

            # 6. Update Profile role (Signal in api/models.py auto-creates the profile)
            if hasattr(user, 'profile'):
                user.profile.role = role
                if role != 'owner':
                    user.profile.is_approved = True
                user.profile.save()
            else:
                Profile.objects.create(user=user, role=role, is_approved=(role != 'owner'))

            # 7. Login immediately after successful signup
            if role == 'owner':
                return JsonResponse({'message': 'Registration successful! Your account is pending admin approval.', 'user': {'email': email, 'role': role}}, status=201)

            login(request, user)

            return JsonResponse({'message': 'Registration successful!', 'user': {'email': email, 'role': role}}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'An unexpected error occurred. Please try again.'}, status=500)
    return JsonResponse({'error': 'Method not allowed.'}, status=405)

def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            password = data.get('password')

            if not email or not password:
                return JsonResponse({'error': 'Please provide both email and password.'}, status=400)

            # 1. Fetch user by email to get their actual username
            try:
                user_obj = User.objects.get(email=email)
                username = user_obj.username
            except User.DoesNotExist:
                # We return a generic error to prevent email enumeration for security
                return JsonResponse({'error': 'Invalid email or password.'}, status=401)

            # 2. Authenticate using the fetched username
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                role = user.profile.role if hasattr(user, 'profile') else 'farmer'
                
                if role == 'owner' and not getattr(user.profile, 'is_approved', False):
                    return JsonResponse({'error': 'Your account is pending admin approval.'}, status=403)
                    
                login(request, user)
                return JsonResponse({
                    'message': 'Login successful!',
                    'user': {
                        'id': user.id,
                        'name': user.first_name or user.username,
                        'email': user.email,
                        'role': role
                    }
                })
            else:
                return JsonResponse({'error': 'Invalid email or password.'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid data format.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Login failed. Please try again later.'}, status=500)
    return JsonResponse({'error': 'Method not allowed.'}, status=405)

def current_user(request):
    if request.user.is_authenticated:
        role = 'farmer'
        if hasattr(request.user, 'profile') and request.user.profile:
            role = request.user.profile.role
            
        return JsonResponse({
            'authenticated': True,
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'profile': {'role': role}
        })
    return JsonResponse({'authenticated': False}, status=401)

def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logged out successfully'})
