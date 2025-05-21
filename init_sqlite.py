import os
import subprocess
import sys

# Run migrations
subprocess.call(['python', 'manage.py', 'migrate'])

# Create superuser if needed
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')

print("Database initialized with admin user.")