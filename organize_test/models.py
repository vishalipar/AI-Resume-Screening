from django.db import models

# Create your models here.

class Position(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.title

class newTest(models.Model):
    DIFFICULTY_CHOICES = {
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    }
    title = models.CharField(max_length=200)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    duration = models.IntegerField(help_text='Duration in minutes')
    passing_score = models.IntegerField(help_text='Passing score percentage')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title