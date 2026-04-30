from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from .models import Equipment, Profile, Booking, ContactMessage
from .serializers import EquipmentSerializer, BookingSerializer, ContactMessageSerializer, UserManagementSerializer

class UserListView(generics.ListAPIView):
    serializer_class = UserManagementSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if not hasattr(self.request.user, 'profile') or self.request.user.profile.role != 'admin':
            return User.objects.none()
        
        status_query = self.request.query_params.get('status', 'pending')
        if status_query == 'pending':
            return User.objects.filter(profile__role='owner', profile__is_approved=False).order_by('-date_joined')
        return User.objects.all().order_by('-date_joined')

class ApproveUserView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, pk):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            return Response({"error": "Only admins can approve users"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user_to_approve = User.objects.get(pk=pk)
            if hasattr(user_to_approve, 'profile'):
                user_to_approve.profile.is_approved = True
                user_to_approve.profile.save()
                return Response(UserManagementSerializer(user_to_approve).data)
            return Response({"error": "User has no profile"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class UserDeleteView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_destroy(self, instance):
        if not hasattr(self.request.user, 'profile') or self.request.user.profile.role != 'admin':
            raise permissions.PermissionDenied("Only admins can delete users")
        instance.delete()

class EquipmentListCreateView(generics.ListCreateAPIView):
    serializer_class = EquipmentSerializer

    def get_queryset(self):
        status_query = self.request.query_params.get('status', 'approved')
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            user_profile = self.request.user.profile
            if user_profile.role == 'admin':
                if status_query == 'pending':
                    return Equipment.objects.filter(status='pending').order_by('-created_at')
                elif status_query == 'all':
                    return Equipment.objects.all().order_by('-created_at')
            
            if user_profile.role == 'owner' and status_query == 'my':
                return Equipment.objects.filter(owner=self.request.user).order_by('-created_at')
        
        return Equipment.objects.filter(status='approved').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class EquipmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

class ApproveEquipmentView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, pk):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            return Response({"error": "Only admins can approve equipment"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            equipment = Equipment.objects.get(pk=pk)
            equipment.status = 'approved'
            equipment.price = request.data.get('price', equipment.price)
            equipment.save()
            return Response(EquipmentSerializer(equipment).data)
        except Equipment.DoesNotExist:
            return Response({"error": "Equipment not found"}, status=status.HTTP_404_NOT_FOUND)

class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'profile'):
            return Booking.objects.none()
        
        if user.profile.role == 'farmer':
            return Booking.objects.filter(farmer=user)
        elif user.profile.role == 'owner':
            return Booking.objects.filter(equipment__owner=user)
        elif user.profile.role == 'admin':
            return Booking.objects.all()
        return Booking.objects.none()

    def perform_create(self, serializer):
        equipment = serializer.validated_data['equipment']
        duration = serializer.validated_data['duration_days']
        total_price = equipment.price * duration
        serializer.save(farmer=self.request.user, total_price=total_price)

class ContactMessageListCreateView(generics.ListCreateAPIView):
    queryset = ContactMessage.objects.all().order_by('-created_at')
    serializer_class = ContactMessageSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def list(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            return Response({"error": "Only admins can view messages"}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)

class ContactMessageDeleteView(generics.DestroyAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_destroy(self, instance):
        if not hasattr(self.request.user, 'profile') or self.request.user.profile.role != 'admin':
            raise permissions.PermissionDenied("Only admins can delete messages")
        instance.delete()

# Owner Dashboard APIs
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_my_equipment(request):
    equipment = Equipment.objects.filter(owner=request.user)
    serializer = EquipmentSerializer(equipment, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_equipment(request):
    serializer = EquipmentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(owner=request.user, status='pending')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_equipment(request, id):
    try:
        equipment = Equipment.objects.get(pk=id)
    except Equipment.DoesNotExist:
        return Response({"error": "Equipment not found"}, status=status.HTTP_404_NOT_FOUND)
        
    if equipment.owner != request.user:
        return Response({"error": "Not authorized to delete this equipment"}, status=status.HTTP_403_FORBIDDEN)
        
    equipment.delete()
    return Response({"message": "Equipment deleted successfully"}, status=status.HTTP_200_OK)
