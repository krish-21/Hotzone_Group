from django.db import models

# Create your models here.

class Location(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    x = models.IntegerField(default=0)
    y= models.IntegerField(default=0)

    def __str__(self):
        return self.name
        