# Django Frontend for Privacy Scanner

This is a Django-based frontend for the Privacy Scanner API, styled with [shadcn/ui](https://ui.shadcn.com/) components and [Tailwind CSS](https://tailwindcss.com/). It provides a modern, user-friendly web interface to interact with the FastAPI backend for scanning databases for privacy-related information.

## Features

- Modern UI with shadcn/ui components
- Responsive design
- Dark mode support
- Dashboard with statistics and API status
- Database configuration management
- Scan job management
- Detailed scan results view
- API proxy using django-ninja

## Setup

1. Make sure you have Python 3.13+ installed
2. Install the required Python packages:
   ```
   pip install -r ../requirements.txt
   ```
3. Install Node.js and npm (if not already installed)
4. Install the required npm packages:
   ```
   cd django_frontend
   npm install
   ```
5. Build the CSS:
   ```
   npm run build
   ```
6. Make sure the FastAPI backend is running (default: http://localhost:18000)
7. Run the Django development server:
   ```
   python manage.py runserver 8000
   ```
8. Access the frontend at http://localhost:8000

## Development

For development, you can use the watch mode to automatically rebuild the CSS when files change:

```
npm run dev
```

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
- `static/` - Static files
  - `css/` - CSS files
    - `globals.css` - Tailwind CSS directives and shadcn/ui component styles
    - `output.css` - Compiled CSS file
  - `js/` - JavaScript files
- `tailwind.config.js` - Tailwind CSS configuration
- `postcss.config.js` - PostCSS configuration
- `package.json` - npm dependencies and scripts

## Usage

1. First, create a database configuration in the "Database Settings" page
2. Start a scan using the saved configuration or manual settings
3. View the scan results when the scan is completed
4. Download the results in JSON or text format

## UI Components

The UI is built with shadcn/ui components, which are based on Tailwind CSS. The components are styled to match the shadcn/ui design system, with a focus on simplicity and usability.

### Available Components

- Buttons
- Cards
- Forms
- Tables
- Alerts
- Navigation
- List groups

## Notes

- The frontend automatically refreshes the scan job status and results pages
- All API requests are proxied through the Django Ninja API to the FastAPI backend
- The UI supports both light and dark modes (currently defaults to light mode)
