from django.db import models
from django.contrib.auth.models import User

class Movie(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='movie_images/')

    def __str__(self):
        return str(self.id) + ' - ' + self.name

    def get_average_rating(self):
        """Get the average rating for this movie"""
        try:
            from ratings.models import RatingAggregate
            aggregate = RatingAggregate.objects.get(movie=self)
            return aggregate.average_rating
        except:
            return 0.0

    def get_rating_count(self):
        """Get the total number of ratings for this movie"""
        try:
            from ratings.models import RatingAggregate
            aggregate = RatingAggregate.objects.get(movie=self)
            return aggregate.total_ratings
        except:
            return 0

    def get_rating_stats(self):
        """Get comprehensive rating statistics for this movie"""
        try:
            from ratings.services import RatingService
            return RatingService.get_movie_rating_stats(self)
        except:
            return {
                'average_rating': 0.0,
                'total_ratings': 0,
                'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'last_updated': None
            }

class Review(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id) + ' - ' + self.movie.name