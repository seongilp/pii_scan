from django.urls import path
from .views import index, database_configs, scan_jobs, scan_results
from .api import api

urlpatterns = [
    # Frontend views
    path('', index, name='index'),
    path('database-configs/', database_configs, name='database_configs'),
    path('scan-jobs/', scan_jobs, name='scan_jobs'),
    path('scan-results/<str:job_id>/', scan_results, name='scan_results'),
    
    # Django Ninja API
    path('api/', api.urls),
]