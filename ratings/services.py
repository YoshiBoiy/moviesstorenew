from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from .models import MovieRating, RatingAggregate
from movies.models import Movie

class RatingService:
    """Service class for managing movie ratings and calculations"""
    
    @staticmethod
    def create_or_update_rating(user, movie, rating_value):
        """Create a new rating or update an existing one"""
        if not (1 <= rating_value <= 5):
            raise ValueError("Rating must be between 1 and 5")
        
        with transaction.atomic():
            # Create or update the rating
            rating, created = MovieRating.objects.get_or_create(
                user=user,
                movie=movie,
                defaults={'rating': rating_value}
            )
            
            if not created:
                rating.rating = rating_value
                rating.save()
            
            # Update the aggregate statistics
            RatingService.update_movie_rating_aggregate(movie)
            
            return rating, created
    
    @staticmethod
    def delete_rating(user, movie):
        """Delete a user's rating for a movie"""
        try:
            rating = MovieRating.objects.get(user=user, movie=movie)
            rating.delete()
            
            # Update the aggregate statistics
            RatingService.update_movie_rating_aggregate(movie)
            
            return True
        except MovieRating.DoesNotExist:
            return False
    
    @staticmethod
    def get_user_rating(user, movie):
        """Get a user's rating for a specific movie"""
        try:
            return MovieRating.objects.get(user=user, movie=movie)
        except MovieRating.DoesNotExist:
            return None
    
    @staticmethod
    def get_movie_rating_stats(movie):
        """Get comprehensive rating statistics for a movie"""
        try:
            aggregate = RatingAggregate.objects.get(movie=movie)
            return {
                'average_rating': aggregate.average_rating,
                'total_ratings': aggregate.total_ratings,
                'rating_distribution': {
                    1: aggregate.rating_1_count,
                    2: aggregate.rating_2_count,
                    3: aggregate.rating_3_count,
                    4: aggregate.rating_4_count,
                    5: aggregate.rating_5_count,
                },
                'last_updated': aggregate.last_updated
            }
        except RatingAggregate.DoesNotExist:
            return {
                'average_rating': 0.0,
                'total_ratings': 0,
                'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'last_updated': None
            }
    
    @staticmethod
    def update_movie_rating_aggregate(movie):
        """Update the rating aggregate for a specific movie"""
        aggregate, created = RatingAggregate.objects.get_or_create(movie=movie)
        aggregate.update_aggregate()
        return aggregate
    
    @staticmethod
    def update_all_rating_aggregates():
        """Update rating aggregates for all movies"""
        movies = Movie.objects.all()
        for movie in movies:
            RatingService.update_movie_rating_aggregate(movie)
    
    @staticmethod
    def get_top_rated_movies(limit=10):
        """Get the top rated movies"""
        return RatingAggregate.objects.filter(
            total_ratings__gte=1
        ).order_by('-average_rating', '-total_ratings')[:limit]
    
    @staticmethod
    def get_most_rated_movies(limit=10):
        """Get the most rated movies"""
        return RatingAggregate.objects.filter(
            total_ratings__gte=1
        ).order_by('-total_ratings', '-average_rating')[:limit]
    
    @staticmethod
    def get_user_rating_history(user, limit=20):
        """Get a user's rating history"""
        return MovieRating.objects.filter(user=user).order_by('-created_at')[:limit]
    
    @staticmethod
    def get_recent_ratings(limit=20):
        """Get recent ratings across all movies"""
        return MovieRating.objects.select_related('user', 'movie').order_by('-created_at')[:limit]
    
    class RatingCalculator:
        """Service class for advanced rating calculations and analytics"""
    
    @staticmethod
    def calculate_weighted_average_rating(movie, time_weight=True):
        """Calculate weighted average rating with optional time weighting"""
        ratings = MovieRating.objects.filter(movie=movie)
        
        if not ratings.exists():
            return 0.0
        
        if not time_weight:
            return sum(r.rating for r in ratings) / ratings.count()
        
        # Time-weighted calculation (recent ratings have more weight)
        now = timezone.now()
        total_weight = 0
        weighted_sum = 0
        
        for rating in ratings:
            # Calculate weight based on recency (more recent = higher weight)
            days_old = (now - rating.created_at).days
            weight = max(0.1, 1.0 - (days_old / 365.0))  # Decay over a year
            
            weighted_sum += rating.rating * weight
            total_weight += weight
        
        return round(weighted_sum / total_weight, 1) if total_weight > 0 else 0.0
    
    @staticmethod
    def calculate_rating_trends(movie, days=30):
        """Calculate rating trends over time"""
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        ratings = MovieRating.objects.filter(
            movie=movie,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('created_at')
        
        # Group by day and calculate daily averages
        daily_ratings = {}
        for rating in ratings:
            date_key = rating.created_at.date()
            if date_key not in daily_ratings:
                daily_ratings[date_key] = []
            daily_ratings[date_key].append(rating.rating)
        
        trends = []
        for date, rating_list in daily_ratings.items():
            trends.append({
                'date': date,
                'average_rating': round(sum(rating_list) / len(rating_list), 1),
                'count': len(rating_list)
            })
        
        return trends
    
    @staticmethod
    def get_rating_correlation_with_purchases(movie):
        """Analyze correlation between ratings and purchase patterns"""
        from cart.models import Item
        from geographic.models import MoviePurchase
        
        # Get rating data
        rating_stats = RatingService.get_movie_rating_stats(movie)
        
        # Get purchase data
        purchase_count = Item.objects.filter(movie=movie).count()
        geographic_purchases = MoviePurchase.objects.filter(movie=movie).count()
        
        return {
            'movie': movie.name,
            'average_rating': rating_stats['average_rating'],
            'total_ratings': rating_stats['total_ratings'],
            'purchase_count': purchase_count,
            'geographic_purchases': geographic_purchases,
            'rating_purchase_ratio': round(rating_stats['total_ratings'] / max(purchase_count, 1), 2)
        }