from django.urls import path

from price import views


app_name = 'price'

urlpatterns = [
    path('', views.index, name='index'),
    path('thesis/', views.thesis, name='thesis'),
    path('api/current/', views.api_current_data, name='api_current_data'),
    path('api/health/', views.health_check, name='health_check'),
]
