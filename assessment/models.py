from django.db import models
from organize_test.models import newTest
import uuid
# Create your models here.

class TestAttempt(models.Model):
    test = models.ForeignKey(newTest, on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(default='not_started', max_length=20)
    
    def __str__(self):
        return self.email
        