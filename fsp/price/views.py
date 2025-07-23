import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from .services import sber_service
from .models import APICallLog

logger = logging.getLogger('price')


@cache_page(30)  # Cache for 30 seconds
def index(request):
    """Main page showing current price evaluation"""
    try:
        data = sber_service.get_current_data()
        
        # Check if we have valid data
        if data['moex_price'] is None or data['fair_price'] is None:
            messages.error(request, 'Не удалось получить актуальные данные. Попробуйте позже.')
            data = {
                'moex_price': 'Н/Д',
                'fair_price': 'Н/Д',
                'fair_price_20_percent': 'Н/Д',
                'price_score': 'неизвестно'
            }
        
        logger.info('Index page loaded successfully')
        return render(request, 'index.html', data)
        
    except Exception as e:
        logger.error(f'Error in index view: {e}')
        messages.error(request, 'Произошла ошибка при загрузке данных.')
        return render(request, 'index.html', {
            'moex_price': 'Ошибка',
            'fair_price': 'Ошибка',
            'fair_price_20_percent': 'Ошибка',
            'price_score': 'неизвестно'
        })


@cache_page(60)  # Cache for 1 minute
def thesis(request):
    """Investment thesis page"""
    try:
        data = sber_service.get_current_data()
        context = {
            'moex_price': data['moex_price'] or 'Н/Д',
            'pb': data['pb_ratio'] or 'Н/Д',
        }
        
        logger.info('Thesis page loaded successfully')
        return render(request, 'thesis.html', context)
        
    except Exception as e:
        logger.error(f'Error in thesis view: {e}')
        messages.error(request, 'Произошла ошибка при загрузке данных.')
        return render(request, 'thesis.html', {
            'moex_price': 'Ошибка',
            'pb': 'Ошибка'
        })


@cache_page(300)  # Cache for 5 minutes (historical data changes rarely)
def history_data(request):
    """Historical data page"""
    try:
        # Get historical snapshots for the last 30 days
        snapshots = sber_service.get_historical_data(days=30)
        
        context = {
            'snapshots': snapshots,
            'has_data': snapshots.exists()
        }
        
        logger.info('History data page loaded successfully')
        return render(request, 'history_data.html', context)
        
    except Exception as e:
        logger.error(f'Error in history_data view: {e}')
        messages.error(request, 'Произошла ошибка при загрузке исторических данных.')
        return render(request, 'history_data.html', {'has_data': False})


@cache_page(15)  # Cache API for 15 seconds
def api_current_data(request):
    """API endpoint for current data (for AJAX calls)"""
    try:
        data = sber_service.get_current_data()
        
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if hasattr(timestamp, 'isoformat'):
            timestamp_str = timestamp.isoformat()
        else:
            timestamp_str = str(timestamp)
        
        response = JsonResponse({
            'success': True,
            'data': {
                'moex_price': data['moex_price'],
                'fair_price': data['fair_price'],
                'fair_price_20_percent': data['fair_price_20_percent'],
                'pb_ratio': data['pb_ratio'],
                'price_score': data['price_score'],
                'timestamp': timestamp_str
            }
        })
        
        # Add cache headers for better performance
        response['Cache-Control'] = 'public, max-age=15'
        return response
        
    except Exception as e:
        logger.error(f'Error in API endpoint: {e}')
        return JsonResponse({
            'success': False,
            'error': 'Не удалось получить данные'
        }, status=500)


def health_check(request):
    """Health check endpoint for monitoring"""
    try:
        from django.db import connection
        from django.conf import settings
        
        checks = {}
        overall_status = 'healthy'
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks['database'] = 'ok'
        except Exception as e:
            checks['database'] = f'error: {str(e)[:100]}'
            overall_status = 'unhealthy'
        
        # Check cache
        try:
            test_key = 'health_check_test'
            cache.set(test_key, 'ok', 10)
            cache_working = cache.get(test_key) == 'ok'
            cache.delete(test_key)
            checks['cache'] = 'ok' if cache_working else 'error'
            if not cache_working:
                overall_status = 'degraded'
        except Exception as e:
            checks['cache'] = f'error: {str(e)[:100]}'
            overall_status = 'degraded'
        
        # Get recent API call success rate
        try:
            recent_calls = APICallLog.objects.all()[:20]
            if recent_calls.exists():
                successful = recent_calls.filter(success=True).count()
                success_rate = (successful / recent_calls.count()) * 100
                checks['api_success_rate'] = f"{success_rate:.1f}%"
                if success_rate < 50:
                    overall_status = 'degraded'
            else:
                checks['api_success_rate'] = 'no_data'
        except Exception as e:
            checks['api_success_rate'] = f'error: {str(e)[:100]}'
        
        # Test external APIs
        try:
            test_data = sber_service.get_moex_price()
            checks['moex_api'] = 'ok' if test_data is not None else 'error'
        except Exception as e:
            checks['moex_api'] = f'error: {str(e)[:100]}'
            if overall_status == 'healthy':
                overall_status = 'degraded'
        
        status = {
            'status': overall_status,
            'timestamp': timezone.now().isoformat(),
            'checks': checks,
            'version': '1.0.0'
        }
        
        status_code = 200 if overall_status == 'healthy' else (503 if overall_status == 'unhealthy' else 200)
        return JsonResponse(status, status=status_code)
        
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)[:200],
            'timestamp': timezone.now().isoformat()
        }, status=500)


def save_snapshot(request):
    """Manually save a price snapshot"""
    if request.method == 'POST':
        try:
            snapshot = sber_service.save_snapshot()
            if snapshot:
                messages.success(request, f'Снимок данных сохранен: {snapshot.timestamp}')
            else:
                messages.error(request, 'Не удалось сохранить снимок данных')
        except Exception as e:
            logger.error(f'Error saving snapshot: {e}')
            messages.error(request, 'Произошла ошибка при сохранении снимка')
    
    return redirect('price:index')



