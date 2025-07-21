from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import PriceSnapshot, APICallLog


@admin.register(PriceSnapshot)
class PriceSnapshotAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'moex_price', 'fair_price', 'pb_ratio', 'price_score', 'colored_score']
    list_filter = ['price_score', 'timestamp']
    search_fields = ['price_score']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']
    
    def colored_score(self, obj):
        colors = {
            'дешево': 'green',
            'справедливо': 'blue',
            'чуть дорого': 'orange',
            'дорого': 'red',
        }
        color = colors.get(obj.price_score, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.price_score
        )
    colored_score.short_description = 'Цветная оценка'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(APICallLog)
class APICallLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'api_name', 'success_icon', 'status_code', 'response_time_ms', 'url_short']
    list_filter = ['success', 'api_name', 'status_code', 'timestamp']
    search_fields = ['api_name', 'url', 'error_message']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp', 'response_time_ms']
    
    def success_icon(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓</span>')
        else:
            return format_html('<span style="color: red;">✗</span>')
    success_icon.short_description = 'Успех'
    
    def url_short(self, obj):
        if len(obj.url) > 50:
            return obj.url[:47] + '...'
        return obj.url
    url_short.short_description = 'URL'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
