"""
Custom middleware for performance monitoring and optimization
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse

logger = logging.getLogger('price')


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """Middleware to monitor request performance"""
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log slow requests
            if duration > 2.0:  # Log requests taking more than 2 seconds
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s"
                )
            
            # Add performance header for monitoring
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response


class HealthCheckMiddleware(MiddlewareMixin):
    """Middleware to handle health checks efficiently"""
    
    def process_request(self, request):
        if request.path == '/api/health/' and request.method == 'GET':
            # Quick health check without full Django processing
            return HttpResponse(
                '{"status":"ok","timestamp":"' + 
                str(time.time()) + '"}',
                content_type='application/json'
            )
        return None