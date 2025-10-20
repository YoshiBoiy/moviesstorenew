from django.contrib import admin
from .models import MovieRating, RatingAggregate

@admin.register(MovieRating)
class MovieRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'rating', 'created_at']
    list_filter = ['rating', 'created_at', 'movie']
    search_fields = ['user__username', 'movie__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Rating Information', {
            'fields': ('user', 'movie', 'rating')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(RatingAggregate)
class RatingAggregateAdmin(admin.ModelAdmin):
    list_display = ['movie', 'average_rating', 'total_ratings', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['movie__name']
    readonly_fields = ['last_updated']
    ordering = ['-average_rating']
    
    fieldsets = (
        ('Movie Information', {
            'fields': ('movie',)
        }),
        ('Rating Statistics', {
            'fields': ('average_rating', 'total_ratings')
        }),
        ('Rating Distribution', {
            'fields': ('rating_1_count', 'rating_2_count', 'rating_3_count', 'rating_4_count', 'rating_5_count'),
            'classes': ('collapse',)
        }),
        ('Last Updated', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )

def get_queryset(self, request):
        return super().get_queryset(request).select_related('movie')
    


