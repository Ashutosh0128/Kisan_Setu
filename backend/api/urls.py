from django.urls import path
from .views import (
    EquipmentListCreateView, 
    EquipmentDetailView, ApproveEquipmentView, BookingListCreateView, 
    ContactMessageListCreateView, ContactMessageDeleteView,
    get_my_equipment, add_equipment, delete_equipment,
    UserListView, ApproveUserView, UserDeleteView
)

urlpatterns = [
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/approve/', ApproveUserView.as_view(), name='user_approve'),
    path('users/<int:pk>/', UserDeleteView.as_view(), name='user_delete'),
    path('equipment/', EquipmentListCreateView.as_view(), name='equipment_list_create'),
    path('equipment/<int:pk>/', EquipmentDetailView.as_view(), name='equipment_detail'),
    path('equipment/<int:pk>/approve/', ApproveEquipmentView.as_view(), name='equipment_approve'),
    path('bookings/', BookingListCreateView.as_view(), name='booking_list_create'),
    path('contact/', ContactMessageListCreateView.as_view(), name='contact_message_list_create'),
    path('contact/<int:pk>/', ContactMessageDeleteView.as_view(), name='contact_message_delete'),
    path('my-equipment/', get_my_equipment, name='get_my_equipment'),
    path('add-equipment/', add_equipment, name='add_equipment'),
    path('delete-equipment/<int:id>/', delete_equipment, name='delete_equipment'),
]
