from ckeditor.widgets import CKEditorWidget
from django import forms
from courses.models import Course, Module, Lesson, Test, Question, Answer, ModuleMaterial
from users.models import CustomUser


class CourseForm(forms.ModelForm):
    co_authors = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role='teacher'),
        required=False,
        label='Со-преподаватели',
        widget=forms.CheckboxSelectMultiple
    )
    class Meta:
        model = Course
        fields = ['title', 'description', 'difficulty_level', 'is_published', 'image', 'co_authors']
        labels = {
            'title': 'Название курса',
            'description': 'Описание',
            'difficulty_level': 'Уровень сложности',
            'is_published': 'Опубликован',
            'image': 'Изображение',
        }

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'order_index', 'difficulty_level']
        labels = {
            'title': 'Название модуля',
            'description': 'Описание',
            'order_index': 'Порядковый номер',
            'difficulty_level': 'Уровень сложности',
        }

class LessonForm(forms.ModelForm):
    content = forms.CharField(
        widget=CKEditorWidget(attrs={'id': 'lesson_content'}),
        required=False
    )
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'content_type', 'order_index']
        labels = {
            'title': 'Название урока',
            'content': 'Содержание',
            'content_type': 'Тип контента',
            'order_index': 'Порядковый номер',
        }

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'passing_score', 'max_score']
        labels = {
            'title': 'Название теста',
            'passing_score': 'Проходной балл (%)',
            'max_score': 'Максимальный балл',
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'points']
        labels = {
            'question_text': 'Текст вопроса',
            'question_type': 'Тип вопроса',
            'points': 'Количество баллов',
        }

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text', 'is_correct']
        labels = {
            'answer_text': 'Текст ответа',
            'is_correct': 'Правильный ответ',
        }

class RequiredMaterialForm(forms.ModelForm):
    content = forms.CharField(
        widget=CKEditorWidget(attrs={'id': 'required_material_content'}),
        required=False
    )
    class Meta:
        model = ModuleMaterial
        fields = ['title', 'material_type', 'url', 'content', 'order_index']
        labels = {
            'title': 'Название',
            'material_type': 'Тип',
            'url': 'Ссылка (для видео/тренажёра)',
            'content': 'Содержание (текст)',
            'order_index': 'Порядок',
        }

class AdvancedMaterialForm(forms.ModelForm):
    content = forms.CharField(
        widget=CKEditorWidget(attrs={'id': 'advanced_material_content'}),
        required=False
    )
    class Meta:
        model = ModuleMaterial
        fields = ['title', 'material_type', 'url', 'content', 'order_index']
        labels = {
            'title': 'Название',
            'material_type': 'Тип',
            'url': 'Ссылка (для видео/тренажёра)',
            'content': 'Содержание (текст)',
            'order_index': 'Порядок',
        }

    # courses/forms.py

class ModuleMaterialForm(forms.ModelForm):
    content = forms.CharField(
        widget=CKEditorWidget(),
        required=False
    )

    class Meta:
        model = ModuleMaterial
        fields = ['title', 'material_type', 'url', 'content', 'order_index']
        labels = {
            'title': 'Название',
            'material_type': 'Тип',
            'url': 'Ссылка (для видео/тренажёра)',
            'content': 'Содержание (текст)',
            'order_index': 'Порядок',
        }