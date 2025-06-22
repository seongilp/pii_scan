from django.db import models


class DatabaseConfig(models.Model):
    """Database configuration model"""
    DB_TYPE_CHOICES = [
        ('mysql', 'MySQL'),
        ('oracle', 'Oracle'),
    ]
    
    name = models.CharField(max_length=100)
    db_type = models.CharField(max_length=10, choices=DB_TYPE_CHOICES)
    host = models.CharField(max_length=255)
    port = models.IntegerField(default=3306)
    database = models.CharField(max_length=100, blank=True, null=True)
    service_name = models.CharField(max_length=100, blank=True, null=True)
    user = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    sample_size = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.db_type})"


class ScanJob(models.Model):
    """Scan job model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    job_id = models.CharField(max_length=36, primary_key=True)
    scan_name = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    db_type = models.CharField(max_length=10, choices=DatabaseConfig.DB_TYPE_CHOICES)
    host = models.CharField(max_length=255)
    database = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField()
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    progress = models.IntegerField(default=0)
    current_step = models.CharField(max_length=255, blank=True, default='')
    error_message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.job_id} - {self.scan_name or 'Unnamed'} ({self.status})"