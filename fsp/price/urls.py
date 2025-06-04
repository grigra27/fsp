from django.urls import path

from price import views


app_name = 'price'

urlpatterns = [
    path('thesis/', views.thesis, name='thesis'),
    path('history_data/', views.history_data, name='history_data'),
    path('otladka/', views.otladka, name='otladka'),
    path('', views.index, name='index'),
]
