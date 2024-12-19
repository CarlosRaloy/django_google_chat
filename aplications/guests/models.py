from django.db import models

class ModelGoogleGuest(models.Model):
    name = models.CharField(max_length=255)
    space = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class RespondedMessage(models.Model):
    message_id = models.CharField(max_length=255, unique=True)
    responded_at = models.DateTimeField(auto_now_add=True)
    message_user = models.TextField()
    status = models.BooleanField(default=False)

    def __str__(self):
        return self.message_id