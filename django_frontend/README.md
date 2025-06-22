# Django Frontend for Privacy Scanner

This is a Django-based frontend for the Privacy Scanner API. It provides a user-friendly web interface to interact with the FastAPI backend for scanning databases for privacy-related information.

## Features

- Dashboard with statistics and API status
- Database configuration management
- Scan job management
- Detailed scan results view
- API proxy using django-ninja

## Setup

1. Make sure you have Python 3.13+ installed
2. Install the required packages:
   ```
   pip install -r ../requirements.txt
   ```
3. Make sure the FastAPI backend is running (default: http://localhost:18000)
4. Run the Django development server:
   ```
   cd django_frontend
   python manage.py runserver 8000
   ```
5. Access the frontend at http://localhost:8000

## Configuration

The frontend is configured to connect to the FastAPI backend at http://localhost:18000 by default. You can change this in the `settings.py` file:

```python
# FastAPI Backend URL
FASTAPI_BACKEND_URL = 'http://localhost:18000'
API_TOKEN = 'your-secret-token'
```

## Project Structure

- `piiscan_frontend/` - Django project settings
- `scanner_frontend/` - Django app for the frontend
  - `api.py` - Django Ninja API endpoints that proxy to the FastAPI backend
  - `models.py` - Django models for database configurations and scan jobs
  - `views.py` - Django views for rendering templates
  - `urls.py` - URL routing
- `templates/scanner_frontend/` - HTML templates
  - `base.html` - Base template with common layout
  - `index.html` - Dashboard
  - `database_configs.html` - Database configuration management
  - `scan_jobs.html` - Scan job management
  - `scan_results.html` - Scan results view

## Usage

1. First, create a database configuration in the "Database Settings" page
2. Start a scan using the saved configuration or manual settings
3. View the scan results when the scan is completed
4. Download the results in JSON or text format

## Notes

- The frontend automatically refreshes the scan job status and results pages
- All API requests are proxied through the Django Ninja API to the FastAPI backend