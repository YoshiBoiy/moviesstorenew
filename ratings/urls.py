from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    # Rating views
    path('rate/<int:movie_id>/', views.RatingView.as_view(), name='rate_movie'),
    path('my-ratings/', views.my_ratings_view, name='my_ratings'),
    
    # API endpoints
    path('api/submit/<int:movie_id>/', views.submit_rating_api, name='submit_rating_api'),
    path('api/delete/<int:movie_id>/', views.delete_rating_api, name='delete_rating_api'),
    path('api/movie/<int:movie_id>/', views.get_movie_rating_api, name='get_movie_rating_api'),
    path('api/user-ratings/', views.get_user_ratings_api, name='get_user_ratings_api'),
    path('api/top-rated/', views.get_top_rated_movies_api, name='get_top_rated_movies_api'),
    path('api/analytics/<int:movie_id>/', views.get_rating_analytics_api, name='get_rating_analytics_api'),
]