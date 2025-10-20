from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q
import json
from .models import MovieRating, RatingAggregate
from .services import RatingService, RatingCalculator
from movies.models import Movie

class RatingView(View):
    """View for displaying movie rating interface"""
    
    @method_decorator(login_required)
    def get(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)
        user_rating = RatingService.get_user_rating(request.user, movie)
        rating_stats = RatingService.get_movie_rating_stats(movie)
        
        context = {
            'movie': movie,
            'user_rating': user_rating,
            'rating_stats': rating_stats,
        }
        return render(request, 'ratings/rate_movie.html', context)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def submit_rating_api(request, movie_id):
    """API endpoint to submit or update a movie rating"""
    try:
        movie = get_object_or_404(Movie, id=movie_id)
        data = json.loads(request.body)
        rating_value = data.get('rating')
        
        if not rating_value or not isinstance(rating_value, int):
            return JsonResponse({
                'success': False,
                'error': 'Rating value is required and must be an integer'
            }, status=400)
        
        if not (1 <= rating_value <= 5):
            return JsonResponse({
                'success': False,
                'error': 'Rating must be between 1 and 5'
            }, status=400)
        
        # Create or update the rating
        rating, created = RatingService.create_or_update_rating(
            request.user, movie, rating_value
        )
        
        # Get updated rating statistics
        rating_stats = RatingService.get_movie_rating_stats(movie)
        
        return JsonResponse({
            'success': True,
            'message': 'Rating submitted successfully' if created else 'Rating updated successfully',
            'rating': {
                'id': rating.id,
                'rating': rating.rating,
                'created_at': rating.created_at.isoformat(),
                'updated_at': rating.updated_at.isoformat()
            },
            'movie_stats': rating_stats
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_rating_api(request, movie_id):
    """API endpoint to delete a user's rating for a movie"""
    try:
        movie = get_object_or_404(Movie, id=movie_id)
        
        success = RatingService.delete_rating(request.user, movie)
        
        if success:
            # Get updated rating statistics
            rating_stats = RatingService.get_movie_rating_stats(movie)
            
            return JsonResponse({
                'success': True,
                'message': 'Rating deleted successfully',
                'movie_stats': rating_stats
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No rating found to delete'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_movie_rating_api(request, movie_id):
    """API endpoint to get rating statistics for a movie"""
    try:
        movie = get_object_or_404(Movie, id=movie_id)
        rating_stats = RatingService.get_movie_rating_stats(movie)
        
        # Add user's rating if authenticated
        user_rating = None
        if request.user.is_authenticated:
            user_rating_obj = RatingService.get_user_rating(request.user, movie)
            if user_rating_obj:
                user_rating = {
                    'rating': user_rating_obj.rating,
                    'created_at': user_rating_obj.created_at.isoformat()
                }
        
        return JsonResponse({
            'success': True,
            'data': {
                'movie_id': movie.id,
                'movie_name': movie.name,
                'rating_stats': rating_stats,
                'user_rating': user_rating
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def get_user_ratings_api(request):
    """API endpoint to get user's rating history"""
    try:
        ratings = RatingService.get_user_rating_history(request.user)
        
        rating_data = []
        for rating in ratings:
            rating_data.append({
                'id': rating.id,
                'movie_id': rating.movie.id,
                'movie_name': rating.movie.name,
                'movie_image': rating.movie.image.url if rating.movie.image else None,
                'rating': rating.rating,
                'created_at': rating.created_at.isoformat(),
                'updated_at': rating.updated_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'data': rating_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_top_rated_movies_api(request):
    """API endpoint to get top rated movies"""
    try:
        limit = int(request.GET.get('limit', 10))
        movies = RatingService.get_top_rated_movies(limit)
        
        movie_data = []
        for aggregate in movies:
            movie_data.append({
                'id': aggregate.movie.id,
                'name': aggregate.movie.name,
                'image': aggregate.movie.image.url if aggregate.movie.image else None,
                'price': aggregate.movie.price,
                'average_rating': aggregate.average_rating,
                'total_ratings': aggregate.total_ratings,
                'rating_distribution': {
                    1: aggregate.rating_1_count,
                    2: aggregate.rating_2_count,
                    3: aggregate.rating_3_count,
                    4: aggregate.rating_4_count,
                    5: aggregate.rating_5_count,
                }
            })
        
        return JsonResponse({
            'success': True,
            'data': movie_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_rating_analytics_api(request, movie_id):
    """API endpoint to get detailed rating analytics for a movie"""
    try:
        movie = get_object_or_404(Movie, id=movie_id)
        
        # Get basic rating stats
        rating_stats = RatingService.get_movie_rating_stats(movie)
        
        # Get weighted average
        weighted_avg = RatingCalculator.calculate_weighted_average_rating(movie)
        
        # Get rating trends (last 30 days)
        trends = RatingCalculator.calculate_rating_trends(movie, days=30)
        
        # Get correlation with purchases
        correlation = RatingCalculator.get_rating_correlation_with_purchases(movie)
        
        return JsonResponse({
            'success': True,
            'data': {
                'movie_id': movie.id,
                'movie_name': movie.name,
                'basic_stats': rating_stats,
                'weighted_average': weighted_avg,
                'trends': trends,
                'correlation': correlation
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def my_ratings_view(request):
    """View for displaying user's rating history"""
    ratings = RatingService.get_user_rating_history(request.user)
    
    context = {
        'title': 'My Movie Ratings',
        'ratings': ratings
    }
    return render(request, 'ratings/my_ratings.html', context)