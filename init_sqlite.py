import os
import subprocess
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Run migrations
subprocess.call(['python', 'manage.py', 'migrate'])

# Create superuser
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
    print("Created superuser 'admin' with password 'adminpassword'")
else:
    print("Admin user already exists")

print("Database initialization complete")