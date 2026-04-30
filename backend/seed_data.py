import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kisan_backend.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Equipment

# Ensure admin user exists
admin_user, _ = User.objects.get_or_create(username='admin')
if _:
    admin_user.set_password('admin123')
    admin_user.email = 'admin@example.com'
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.save()
    
    # Ensure admin profile exists and has the correct role
    if hasattr(admin_user, 'profile'):
        admin_user.profile.role = 'admin'
        admin_user.profile.is_approved = True
        admin_user.profile.save()

initial_data = [
    {
        "name": "Mahindra Arjun Novo 605",
        "category": "Tractor",
        "price": 1800,
        "image": "assets/mahindra_novo.png",
        "description": "The powerhouse of Indian fields. 57 HP, advanced synchromesh transmission.",
        "status": "approved",
    },
    {
        "name": "Preet 987 Combine",
        "category": "Harvester",
        "price": 8500,
        "image": "assets/preet_combine.png",
        "description": "India's most trusted combine harvester. Optimized for wheat, paddy, and soybean.",
        "status": "approved",
    },
    {
        "name": "Swaraj 855 FE",
        "category": "Tractor",
        "price": 1500,
        "image": "assets/swaraj_855.png",
        "description": "Legendary 52 HP performance. Known for high torque and low maintenance.",
        "status": "approved",
    },
    {
        "name": "Shaktiman Rotavator",
        "category": "Implements",
        "price": 600,
        "image": "assets/shaktiman_rotavator.png",
        "description": "Heavy-duty soil preparation. 7-feet width, ideal for tough soil.",
        "status": "approved",
    },
    {
        "name": "Mahindra Jivo 225 DI",
        "category": "Tractor",
        "price": 900,
        "image": "assets/mahindra_jivo.png",
        "description": "20 HP compact mini-tractor. Perfect for orchards and small row farming.",
        "status": "approved",
    },
    {
        "name": "Sonalika Tiger DI 65",
        "category": "Tractor",
        "price": 1700,
        "image": "assets/sonalika_tiger.png",
        "description": "Best-in-class mileage and lifting power. Built for high productivity.",
        "status": "approved",
    },
    {
        "name": "John Deere 5050 D",
        "category": "Tractor",
        "price": 2100,
        "image": "assets/john_deere_5050d.png",
        "description": "Modern technology meets reliability. 50 HP, high torque reserve for heavy duty.",
        "status": "approved",
    },
    {
        "name": "Kubota MU4501",
        "category": "Tractor",
        "price": 1950,
        "image": "assets/kubota_mu4501.png",
        "description": "Japanese precision for Indian soil. Balancer shaft technology for low vibration.",
        "status": "approved",
    },
    {
        "name": "CLAAS JAGUAR 860",
        "category": "Harvester",
        "price": 12500,
        "image": "assets/claas_jaguar_860.png",
        "description": "The peak of forage harvesting. Unmatched efficiency and throughput for large estates.",
        "status": "approved",
    }
]

for item in initial_data:
    Equipment.objects.update_or_create(
        name=item['name'],
        defaults={
            "category": item['category'],
            "price": item['price'],
            "image": item['image'],
            "description": item['description'],
            "status": item['status'],
            "owner": admin_user
        }
    )

print("Successfully seeded data and updated images.")
