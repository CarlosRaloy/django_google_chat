from django.db import models

class ModelGoogleGuest(models.Model):
    name = models.CharField(max_length=255)
    space = models.CharField(max_length=50)

    def __str__(self):
        return self.name
