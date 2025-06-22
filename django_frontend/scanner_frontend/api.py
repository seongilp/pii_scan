from ninja import NinjaAPI, Schema
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from django.conf import settings

# Create Ninja API instance
api = NinjaAPI(title="Privacy Scanner API", version="1.0.0")

# Backend API URL
BACKEND_URL = settings.FASTAPI_BACKEND_URL
API_TOKEN = settings.API_TOKEN

# Request and response schemas
class DatabaseConfigSchema(Schema):
    db_type: str
    host: str
    port: int = 3306
    database: Optional[str] = None
    service_name: Optional[str] = None
    user: str
    password: str
    sample_size: int = 100

class ScanRequestSchema(Schema):
    config: DatabaseConfigSchema
    scan_name: Optional[str] = None
    include_structure_analysis: bool = True
    include_privacy_scan: bool = True
    include_executive_summary: bool = True

class DatabaseConfigCreateSchema(DatabaseConfigSchema):
    name: str

class ScanJobSchema(Schema):
    job_id: str
    scan_name: Optional[str] = None
    status: str
    db_type: str
    host: str
    database: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    current_step: str = ""
    error_message: Optional[str] = None

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

# API endpoints
@api.get("/")
def root(request):
    """API status check"""
    response = make_api_request("get", "/")
    return response.json()

@api.post("/scan", response=Dict[str, Any])
def start_scan(request, scan_request: ScanRequestSchema):
    """Start a new scan job"""
    response = make_api_request("post", "/scan", data=scan_request.dict())
    return response.json()

@api.get("/jobs", response=List[ScanJobSchema])
def list_jobs(request):
    """List all scan jobs"""
    response = make_api_request("get", "/jobs")
    return response.json()

@api.get("/jobs/{job_id}", response=ScanJobSchema)
def get_job_status(request, job_id: str):
    """Get status of a specific job"""
    response = make_api_request("get", f"/jobs/{job_id}")
    return response.json()

@api.delete("/jobs/{job_id}", response=Dict[str, Any])
def cancel_job(request, job_id: str):
    """Cancel a running job"""
    response = make_api_request("delete", f"/jobs/{job_id}")
    return response.json()

@api.get("/results/{job_id}", response=Dict[str, Any])
def get_scan_results(request, job_id: str):
    """Get scan results for a job"""
    response = make_api_request("get", f"/results/{job_id}")
    return response.json()

@api.get("/results/{job_id}/summary", response=Dict[str, Any])
def get_scan_summary(request, job_id: str):
    """Get summary of scan results"""
    response = make_api_request("get", f"/results/{job_id}/summary")
    return response.json()

@api.get("/health", response=Dict[str, Any])
def health_check(request):
    """Health check"""
    response = make_api_request("get", "/health")
    return response.json()

@api.get("/stats", response=Dict[str, Any])
def get_statistics(request):
    """Get statistics"""
    response = make_api_request("get", "/stats")
    return response.json()

@api.post("/database-configs", response=Dict[str, Any])
def create_database_config(request, config: DatabaseConfigCreateSchema):
    """Create a new database configuration"""
    response = make_api_request("post", "/database-configs", data=config.dict())
    return response.json()

@api.get("/database-configs", response=List[Dict[str, Any]])
def list_database_configs(request):
    """List all database configurations"""
    response = make_api_request("get", "/database-configs")
    return response.json()

@api.get("/database-configs/{config_id}", response=Dict[str, Any])
def get_database_config(request, config_id: int):
    """Get a specific database configuration"""
    response = make_api_request("get", f"/database-configs/{config_id}")
    return response.json()

@api.put("/database-configs/{config_id}", response=Dict[str, Any])
def update_database_config(request, config_id: int, config: DatabaseConfigCreateSchema):
    """Update a database configuration"""
    response = make_api_request("put", f"/database-configs/{config_id}", data=config.dict())
    return response.json()

@api.delete("/database-configs/{config_id}", response=Dict[str, Any])
def delete_database_config(request, config_id: int):
    """Delete a database configuration"""
    response = make_api_request("delete", f"/database-configs/{config_id}")
    return response.json()