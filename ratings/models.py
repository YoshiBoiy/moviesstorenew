from django.db import models
from django.contrib.auth.models import User
from movies.models import Movie
from django.core.validators import MinValueValidator, MaxValueValidator

class MovieRating(models.Model):
    """Model for storing user ratings of movies (1-5 stars)"""
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movie_ratings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'movie']  # One rating per user per movie
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['movie', 'rating']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} rated {self.movie.name} {self.rating} stars"
    
    @classmethod
    def get_average_rating(cls, movie):
        """Get the average rating for a movie"""
        ratings = cls.objects.filter(movie=movie)
        if not ratings.exists():
            return 0.0
        
        total_ratings = sum(rating.rating for rating in ratings)
        return round(total_ratings / ratings.count(), 1)
    
    @classmethod
    def get_rating_count(cls, movie):
        """Get the total number of ratings for a movie"""
        return cls.objects.filter(movie=movie).count()
    
    @classmethod
    def get_rating_distribution(cls, movie):
        """Get the distribution of ratings for a movie"""
        distribution = {}
        for rating_value, _ in cls.RATING_CHOICES:
            count = cls.objects.filter(movie=movie, rating=rating_value).count()
            distribution[rating_value] = count
        return distribution
    
    class RatingAggregate(models.Model):
        """Model for storing pre-calculated rating statistics for performance"""
    id = models.AutoField(primary_key=True)
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name='rating_aggregate')
    average_rating = models.FloatField(default=0.0)
    total_ratings = models.IntegerField(default=0)
    rating_1_count = models.IntegerField(default=0)
    rating_2_count = models.IntegerField(default=0)
    rating_3_count = models.IntegerField(default=0)
    rating_4_count = models.IntegerField(default=0)
    rating_5_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.movie.name} - {self.average_rating}/5 ({self.total_ratings} ratings)"
    
    def update_aggregate(self):
        """Update the aggregate statistics from actual ratings"""
        ratings = MovieRating.objects.filter(movie=self.movie)
        
        if not ratings.exists():
            self.average_rating = 0.0
            self.total_ratings = 0
            self.rating_1_count = 0
            self.rating_2_count = 0
            self.rating_3_count = 0
            self.rating_4_count = 0
            self.rating_5_count = 0
        else:
            self.total_ratings = ratings.count()
            self.average_rating = round(sum(r.rating for r in ratings) / self.total_ratings, 1)
            
            # Count each rating level
            distribution = MovieRating.get_rating_distribution(self.movie)
            self.rating_1_count = distribution.get(1, 0)
            self.rating_2_count = distribution.get(2, 0)
            self.rating_3_count = distribution.get(3, 0)
            self.rating_4_count = distribution.get(4, 0)
            self.rating_5_count = distribution.get(5, 0)
        
        self.save()