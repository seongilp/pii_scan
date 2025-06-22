from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests
from django.conf import settings
import json

# Backend API URL and token
BACKEND_URL = settings.FASTAPI_BACKEND_URL
API_TOKEN = settings.API_TOKEN

# Helper function for API requests
def make_api_request(method, endpoint, data=None):
    """Make a request to the FastAPI backend"""
    url = f"{BACKEND_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    if method.lower() == "get":
        response = requests.get(url, headers=headers)
    elif method.lower() == "post":
        response = requests.post(url, json=data, headers=headers)
    elif method.lower() == "put":
        response = requests.put(url, json=data, headers=headers)
    elif method.lower() == "delete":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    return response

def index(request):
    """Home page view"""
    # Get API status
    try:
        response = make_api_request("get", "/")
        api_status = response.json()
        
        # Get statistics
        stats_response = make_api_request("get", "/stats")
        stats = stats_response.json()
        
        context = {
            'api_status': api_status,
            'stats': stats,
            'error': None
        }
    except Exception as e:
        context = {
            'api_status': None,
            'stats': None,
            'error': str(e)
        }
    
    return render(request, 'scanner_frontend/index.html', context)

def database_configs(request):
    """Database configurations view"""
    error_message = None
    success_message = None
    
    # Handle form submission for creating a new database config
    if request.method == 'POST':
        try:
            # Extract form data
            config_data = {
                'name': request.POST.get('name'),
                'db_type': request.POST.get('db_type'),
                'host': request.POST.get('host'),
                'port': int(request.POST.get('port')),
                'user': request.POST.get('user'),
                'password': request.POST.get('password'),
                'sample_size': int(request.POST.get('sample_size', 100))
            }
            
            # Add optional fields based on db_type
            if config_data['db_type'] == 'mysql':
                config_data['database'] = request.POST.get('database')
            elif config_data['db_type'] == 'oracle':
                config_data['service_name'] = request.POST.get('service_name')
            
            # Send to API
            response = make_api_request("post", "/database-configs", data=config_data)
            
            if response.status_code == 201:
                success_message = "Database configuration created successfully!"
            else:
                error_message = f"Error: {response.json().get('detail', 'Unknown error')}"
                
        except Exception as e:
            error_message = f"Error: {str(e)}"
    
    # Get all database configs
    try:
        response = make_api_request("get", "/database-configs")
        configs = response.json()
    except Exception as e:
        configs = []
        error_message = f"Error fetching configurations: {str(e)}"
    
    context = {
        'configs': configs,
        'error_message': error_message,
        'success_message': success_message
    }
    
    return render(request, 'scanner_frontend/database_configs.html', context)

def scan_jobs(request):
    """Scan jobs view"""
    error_message = None
    success_message = None
    
    # Handle form submission for starting a new scan
    if request.method == 'POST':
        try:
            # Check if using saved config or manual entry
            if 'config_id' in request.POST and request.POST.get('config_id'):
                # Start scan with saved config
                config_id = int(request.POST.get('config_id'))
                scan_name = request.POST.get('scan_name', f"Scan with config {config_id}")
                
                # Additional scan options
                include_structure = request.POST.get('include_structure_analysis') == 'on'
                include_privacy = request.POST.get('include_privacy_scan') == 'on'
                include_summary = request.POST.get('include_executive_summary') == 'on'
                
                response = make_api_request("post", f"/scan/database-config/{config_id}")
                
            else:
                # Manual config entry
                config_data = {
                    'db_type': request.POST.get('db_type'),
                    'host': request.POST.get('host'),
                    'port': int(request.POST.get('port')),
                    'user': request.POST.get('user'),
                    'password': request.POST.get('password'),
                    'sample_size': int(request.POST.get('sample_size', 100))
                }
                
                # Add optional fields based on db_type
                if config_data['db_type'] == 'mysql':
                    config_data['database'] = request.POST.get('database')
                elif config_data['db_type'] == 'oracle':
                    config_data['service_name'] = request.POST.get('service_name')
                
                # Create scan request
                scan_data = {
                    'config': config_data,
                    'scan_name': request.POST.get('scan_name', 'Manual Scan'),
                    'include_structure_analysis': request.POST.get('include_structure_analysis') == 'on',
                    'include_privacy_scan': request.POST.get('include_privacy_scan') == 'on',
                    'include_executive_summary': request.POST.get('include_executive_summary') == 'on'
                }
                
                response = make_api_request("post", "/scan", data=scan_data)
            
            if response.status_code in (200, 201):
                result = response.json()
                job_id = result.get('job_id')
                success_message = f"Scan started successfully! Job ID: {job_id}"
            else:
                error_message = f"Error: {response.json().get('detail', 'Unknown error')}"
                
        except Exception as e:
            error_message = f"Error: {str(e)}"
    
    # Get all scan jobs
    try:
        response = make_api_request("get", "/jobs")
        jobs = response.json()
    except Exception as e:
        jobs = []
        error_message = f"Error fetching jobs: {str(e)}"
    
    # Get all database configs for the form
    try:
        configs_response = make_api_request("get", "/database-configs")
        configs = configs_response.json()
    except Exception as e:
        configs = []
    
    context = {
        'jobs': jobs,
        'configs': configs,
        'error_message': error_message,
        'success_message': success_message
    }
    
    return render(request, 'scanner_frontend/scan_jobs.html', context)

def scan_results(request, job_id):
    """Scan results view for a specific job"""
    error_message = None
    
    # Get job status
    try:
        job_response = make_api_request("get", f"/jobs/{job_id}")
        job = job_response.json()
        
        # Get results if job is completed
        results = None
        summary = None
        
        if job.get('status') == 'completed':
            try:
                results_response = make_api_request("get", f"/results/{job_id}")
                results = results_response.json()
                
                summary_response = make_api_request("get", f"/results/{job_id}/summary")
                summary = summary_response.json()
            except Exception as e:
                error_message = f"Error fetching results: {str(e)}"
    except Exception as e:
        job = None
        results = None
        summary = None
        error_message = f"Error fetching job: {str(e)}"
    
    context = {
        'job': job,
        'results': results,
        'summary': summary,
        'error_message': error_message
    }
    
    return render(request, 'scanner_frontend/scan_results.html', context)