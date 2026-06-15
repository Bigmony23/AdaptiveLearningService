from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models

from users.models import CustomUser


class Course(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    co_authors = models.ManyToManyField(CustomUser, related_name='co_authored_courses', blank=True)
    difficulty_level = models.IntegerField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='courses/', null=True, blank=True,default='default/course.jpg')

    def __str__(self):
        return self.title

class Module(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    order_index = models.IntegerField()
    difficulty_level = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    # В courses/models.py в модель Module добавить
    estimated_hours = models.IntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    module_id = models.ForeignKey(Module, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = RichTextUploadingField(verbose_name='Содержание урока')
    content_type=models.CharField(max_length=100)
    video_url = models.URLField(blank=True, null=True)
    order_index = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order_index']
        # УБЕРИТЕ unique_together или исправьте его
        # unique_together = ['module_id', 'order_index']  # Если нужно уникальность






class User_progerss(models.Model):
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    module_id = models.ForeignKey(Module, on_delete=models.CASCADE)
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, null=True, blank=True)
    score = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)
    time_spent = models.IntegerField(default=0)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    weak_topics = models.JSONField(default=list)
    improvement_rate = models.FloatField(default=0)
    best_score = models.FloatField(default=0)

    class Meta:
        unique_together = ['user_id', 'module_id', 'lesson']  # Исправлено

class Test(models.Model):
    module_id = models.ForeignKey(Module, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    passing_score = models.IntegerField()
    max_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

class Question(models.Model):
    test_id = models.ForeignKey(Test, on_delete=models.CASCADE)
    question_text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=100)
    points = models.IntegerField()
    topic = models.CharField(max_length=100, null=True, blank=True)
    keyword = models.CharField(max_length=100, null=True, blank=True)
# Create your models here.
class Answer(models.Model):
    qustion_id = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

class TestResult(models.Model):
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    module_id = models.ForeignKey(Module, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


# courses/models.py
class LessonProgress(models.Model):
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    lesson_id = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user_id', 'lesson_id']

class ModuleMaterial(models.Model):
    MATERIAL_TYPES = [
        ('video', 'Видеоурок'),
        ('interactive', 'Интерактивный тренажёр'),
        ('text', 'Текстовая лекция'),
        ('advanced', 'Углублённый материал'),
    ]
    module = models.ForeignKey('Module', on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200, verbose_name='Название материала')
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES, verbose_name='Тип материала')
    url = models.URLField(blank=True, null=True, verbose_name='Ссылка на видео/тренажёр')
    content = RichTextUploadingField(blank=True, null=True, verbose_name='Содержание')
    order_index = models.IntegerField(default=0, verbose_name='Порядок')
    is_required = models.BooleanField(default=False, verbose_name='Обязателен для просмотра после 3 провалов')
    is_advanced = models.BooleanField(default=False, verbose_name='Углублённый материал (для отличников)')

    class Meta:
        ordering = ['order_index']
        verbose_name = 'Материал модуля'
        verbose_name_plural = 'Материалы модулей'

class StudentMaterialProgress(models.Model):
    student = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    material = models.ForeignKey(ModuleMaterial, on_delete=models.CASCADE)
    viewed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['student', 'material']