from django.db import models

from courses.models import Module
from users.models import CustomUser


class AdaptiveRecomendation(models.Model):
    user_id=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    module_id=models.ForeignKey(Module,on_delete=models.CASCADE)
    recommendation_type=models.CharField(max_length=50)
    recommendation_description=models.TextField()
    score_at_time = models.FloatField(null=True, blank=True)  # добавить
    attempt_number = models.IntegerField(null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)



# Create your models here.
