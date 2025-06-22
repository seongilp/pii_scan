#!/usr/bin/env python
"""
Run script for the Django frontend.
This script starts the Django development server on port 8000.
"""

import os
import sys
import subprocess

def main():
    """Run the Django development server"""
    print("Starting Django frontend server...")
    
    # Check if the FastAPI backend is running
    try:
        import requests
        response = requests.get("http://localhost:18000/health", timeout=2)
        if response.status_code == 200:
            print("✅ FastAPI backend is running")
        else:
            print("⚠️ FastAPI backend returned status code:", response.status_code)
    except Exception as e:
        print("⚠️ Warning: Could not connect to FastAPI backend:", str(e))
        print("   Make sure the backend is running on http://localhost:18000")
    
    # Run Django development server
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piiscan_frontend.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Run the server
    print("Starting Django server on http://localhost:8000")
    execute_from_command_line(['manage.py', 'runserver', '8000'])

if __name__ == '__main__':
    main()