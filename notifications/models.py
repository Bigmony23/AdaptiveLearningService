from django.db import models
from users.models import CustomUser


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_module', 'Новый модуль'),
        ('new_lesson', 'Новый урок'),
        ('new_test', 'Новый тест'),
        ('student_failed', 'Студент не сдал тест'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, verbose_name='Тип')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'

    def __str__(self):
        return self.title

from django.db import models

# Create your models here.
