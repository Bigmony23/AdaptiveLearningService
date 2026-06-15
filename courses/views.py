from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from rest_framework import viewsets
from rest_framework.response import Response
from adaptive_engine.algorithm import generate_recommendation
from .forms import CourseForm, ModuleForm, LessonForm, TestForm, QuestionForm, AnswerForm, RequiredMaterialForm, \
    AdvancedMaterialForm
from adaptive_engine.models import AdaptiveRecomendation
from courses.models import Course, Module, Lesson, Test, Question, Answer, User_progerss, TestResult, LessonProgress, \
    StudentMaterialProgress, ModuleMaterial
from courses.serializers import CourseSerializer
from users.mixin import TeacherRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from adaptive_engine.notifications import (
    send_new_module_notification,
    send_new_lesson_notification,
    send_new_test_notification,
    send_teacher_alert_about_failing_student
)
from .forms import ModuleMaterialForm

class HomeView(View):
    def get(self, request):
        popular_courses = Course.objects.filter(is_published=True)[:6]
        return render(request, 'home.html', {'popular_courses': popular_courses})

class CourseView(View):
    def get(self, request):
        courses = Course.objects.all()
        context = {'courses': courses}
        return render(request,'courses/list_of_courses.html', context)

class CourseDetailView(View):
    def get(self, request, id):
        course = get_object_or_404(Course, id=id)
        modules = Module.objects.filter(course_id=course)

        user_progress = None

        if request.user.is_authenticated:
            user_progress = User_progerss.objects.filter(
                user_id=request.user
            )

        context = {
            'course': course,
            'modules': modules,
            'user_progress': user_progress
        }

        return render(request, 'courses/course_detail.html', context)



class ModuleView(LoginRequiredMixin,View):
    def get(self, request, course_id, module_id):
        module = Module.objects.get(id=module_id)
        lessons = Lesson.objects.filter(module_id=module).order_by('order_index')

        # Проверка — пройден ли предыдущий модуль
        previous_module = Module.objects.filter(
            course_id=module.course_id,
            order_index=module.order_index - 1
        ).first()

        if previous_module:
            previous_progress = User_progerss.objects.filter(
                user_id=request.user,
                module_id=previous_module
            ).first()
            if not previous_progress or previous_progress.score < 60:
                return redirect('course_detail', id=course_id)

        # Получаем пройденные уроки через LessonProgress
        completed_lessons_ids = LessonProgress.objects.filter(
            user_id=request.user,
            lesson_id__in=lessons,
            is_completed=True
        ).values_list('lesson_id', flat=True)

        completed_count = completed_lessons_ids.count()
        total_count = lessons.count()
        progress_percentage = (completed_count / total_count * 100) if total_count > 0 else 0

        context = {
            'module': module,
            'lessons': lessons,
            'course_id': course_id,
            'module_id': module_id,
            'completed_lessons_ids': list(completed_lessons_ids),
            'completed_count': completed_count,
            'total_count': total_count,
            'progress_percentage': int(progress_percentage),
        }
        return render(request, 'courses/module_lessons.html', context)


class LessonView(View):
    def get(self, request, course_id, module_id, lesson_id):
        lesson = Lesson.objects.get(id=lesson_id)

        # Все уроки модуля по порядку
        all_lessons = Lesson.objects.filter(
            module_id=module_id
        ).order_by('order_index')
        lessons_list = list(all_lessons)

        # Находим текущий индекс
        current_index = next(
            (i for i, l in enumerate(lessons_list) if l.id == lesson_id),
            None
        )

        # Проверка — просмотрен ли предыдущий урок
        if current_index > 0:
            previous_lesson = lessons_list[current_index - 1]
            previous_completed = LessonProgress.objects.filter(
                user_id=request.user,
                lesson_id=previous_lesson,
                is_completed=True
            ).first()
            if not previous_completed:
                return redirect('lesson',
                    course_id=course_id,
                    module_id=module_id,
                    lesson_id=previous_lesson.id
                )

        # Отмечаем текущий урок как просмотренный
        from django.utils import timezone
        LessonProgress.objects.get_or_create(
            user_id=request.user,
            lesson_id=lesson,
            defaults={
                'is_completed': True,
                'completed_at': timezone.now()
            }
        )

        # Определяем следующий урок
        is_last_lesson = (current_index == len(lessons_list) - 1)
        next_lesson = lessons_list[current_index + 1] if not is_last_lesson else None

        # Прогресс по урокам через LessonProgress
        completed_count = LessonProgress.objects.filter(
            user_id=request.user,
            lesson_id__in=all_lessons,
            is_completed=True
        ).count()

        total_lessons = all_lessons.count()
        progress_percentage = (completed_count / total_lessons * 100) if total_lessons > 0 else 0

        context = {
            'lesson': lesson,
            'course_id': course_id,
            'module_id': module_id,
            'is_last_lesson': is_last_lesson,
            'next_lesson': next_lesson,
            'completed_count': completed_count,
            'total_lessons': total_lessons,
            'progress_percentage': int(progress_percentage),
        }
        return render(request, 'courses/lesson_detail.html', context)


class TestView(View):
    def get(self, request, course_id, module_id):
        module = Module.objects.get(id=module_id)
        lessons = Lesson.objects.filter(module_id=module)

        # 1. Все ли уроки пройдены?
        completed_count = LessonProgress.objects.filter(
            user_id=request.user,
            lesson_id__in=lessons,
            is_completed=True
        ).count()

        if completed_count < lessons.count():
            completed_ids = LessonProgress.objects.filter(
                user_id=request.user,
                lesson_id__in=lessons,
                is_completed=True
            ).values_list('lesson_id', flat=True)

            first_uncompleted = lessons.exclude(
                id__in=completed_ids
            ).order_by('order_index').first()

            return redirect('lesson',
                            course_id=course_id,
                            module_id=module_id,
                            lesson_id=first_uncompleted.id)

        # 2. Обязательные материалы — если attempts >= 3 and score < 60
        progress = User_progerss.objects.filter(user_id=request.user, module_id=module).first()
        if progress and progress.attempts >= 3 and progress.score < 60:
            required_materials = ModuleMaterial.objects.filter(module=module, is_required=True)
            if required_materials.exists():
                viewed_count = StudentMaterialProgress.objects.filter(
                    student=request.user,
                    material__in=required_materials,
                    viewed=True
                ).count()
                if viewed_count < required_materials.count():
                    return redirect('module_materials', course_id=course_id, module_id=module_id)

        # 3. Показать тест
        tests = Test.objects.get(module_id=module_id)
        questions = Question.objects.filter(test_id=tests)
        context = {
            'tests': tests,
            'questions': questions,
            'course_id': course_id,
            'module_id': module_id,
        }
        return render(request, 'courses/tests.html', context)

    def post(self, request, course_id, module_id):
        test = Test.objects.get(module_id=module_id)
        questions = Question.objects.filter(test_id=test)
        correct = 0
        total = questions.count()

        module = Module.objects.get(id=module_id)

        for question in questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                answer = Answer.objects.get(id=selected_answer_id)
                if answer.is_correct:
                    correct += 1
                TestResult.objects.create(
                    user_id=request.user,
                    question=question,
                    module_id=module,
                    selected_answer=answer,
                    is_correct=answer.is_correct
                )

        score = (correct / total) * 100 if total > 0 else 0

        progress, created = User_progerss.objects.get_or_create(
            user_id=request.user,
            module_id=module
        )
        progress.attempts += 1
        progress.score = score
        if score > progress.best_score:  # <-- ДОБАВИТЬ
            progress.best_score = score  # <-- ДОБАВИТЬ

        wrong_answers = TestResult.objects.filter(
            user_id=request.user,
            module_id=module,
            is_correct=False
        )
        weak = list(set([
            a.question.topic for a in wrong_answers
            if a.question.topic
        ]))

        previous_progress = User_progerss.objects.filter(
            user_id=request.user,
            module_id=module
        ).last()
        improvement = score - previous_progress.score if previous_progress else 0

        progress.weak_topics = weak
        progress.improvement_rate = improvement

        if score >= 60:
            from django.utils import timezone
            progress.completed_at = timezone.now()

        progress.save()

        if score < 60 and progress.attempts in [3, 6, 9]:
            send_teacher_alert_about_failing_student(
                request.user,
                module,
                progress.attempts
            )

        generate_recommendation(request.user.id, module_id, score, request)
        return redirect('test_result', course_id=course_id, module_id=module_id)

class TestResultView(View):
    def get(self, request, course_id, module_id):
        user_progress=User_progerss.objects.get(user_id=request.user,module_id=Module.objects.get(id=module_id))
        adaptive_recommendation = AdaptiveRecomendation.objects.filter(
            user_id=request.user,
            module_id=Module.objects.get(id=module_id)
        ).last()
        remaining_attempts = max(0, 3 - user_progress.attempts)
        context={
            'progress':user_progress,
            'recommendation':adaptive_recommendation,
            'course_id':course_id,
            'module_id':module_id,
            'remaining_attempts':remaining_attempts,
            'show_advanced_materials': user_progress.score >= 85
        }
        return render(request,'courses/test_result.html',context)





class StudentCabinetView(LoginRequiredMixin, View):
    def get(self, request):
        progress = User_progerss.objects.filter(user_id=request.user)
        recommendations = AdaptiveRecomendation.objects.filter(
            user_id=request.user
        ).order_by('-created_at')

        context = {
            'progress': progress,
            'recommendations': recommendations,
        }
        return render(request, 'courses/student_cabinet.html', context)


class CourseCreateView(TeacherRequiredMixin, View):
    def get(self, request):
        form = CourseForm()
        return render(request, 'courses/course_create.html', {'form': form})

    def post(self, request):
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.author = request.user
            course.save()
            form.save_m2m()
            return redirect('courses')
        return render(request, 'courses/course_create.html', {'form': form})


# Создание модуля
class ModuleCreateView(TeacherRequiredMixin, View):
    def get(self, request, course_id):
        form = ModuleForm()
        return render(request, 'courses/module_create.html', {'form': form, 'course_id': course_id})

    def post(self, request, course_id):
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course_id = Course.objects.get(id=course_id)
            module.save()
            send_new_module_notification(module)
            return redirect('course_detail', id=course_id)
        return render(request, 'courses/module_create.html', {'form': form, 'course_id': course_id})


class ModuleManageView(TeacherRequiredMixin, View):
    def get_context(self, request, course_id, module_id):
        module = Module.objects.get(id=module_id)
        lessons = Lesson.objects.filter(module_id=module)
        test = Test.objects.filter(module_id=module).first()
        questions = Question.objects.filter(test_id=test) if test else []
        return {
            'module': module,
            'lessons': lessons,
            'test': test,
            'questions': questions,
            'course_id': course_id,
            'lesson_form': LessonForm(),
            'test_form': TestForm(),
            'question_form': QuestionForm(),
            'answer_form': AnswerForm(),
            'required_material_form': RequiredMaterialForm(),  # добавить
            'advanced_material_form': AdvancedMaterialForm(),  # добавить
            'materials': module.materials.all(),
        }

    def get(self, request, course_id, module_id):
        context = self.get_context(request, course_id, module_id)
        return render(request, 'courses/module_manage.html', context)

    def post(self, request, course_id, module_id):
        module = Module.objects.get(id=module_id)
        action = request.POST.get('action')

        # Добавление урока
        if action == 'add_lesson':
            form = LessonForm(request.POST)
            if form.is_valid():
                lesson = form.save(commit=False)
                lesson.module_id = module
                lesson.save()
                send_new_lesson_notification(lesson)

                # Создание теста
        elif action == 'add_test':
            lessons_count = Lesson.objects.filter(module_id=module).count()
            if lessons_count == 0:
                context = self.get_context(request, course_id, module_id)
                context['test_error'] = 'Нельзя создать тест пока нет ни одного урока'
                return render(request, 'courses/module_manage.html', context)

            form = TestForm(request.POST)
            if form.is_valid():
                test = form.save(commit=False)
                test.module_id = module
                test.save()
                send_new_test_notification(test)

        # Добавление вопроса
        elif action == 'add_question':
            test = Test.objects.get(module_id=module)
            form = QuestionForm(request.POST)
            if form.is_valid():
                question = form.save(commit=False)
                question.test_id = test
                question.save()

        # Добавление ответа
        elif action == 'add_answer':
            question_id = request.POST.get('question_id')
            if question_id:
                question = Question.objects.get(id=question_id)
                form = AnswerForm(request.POST)
                if form.is_valid():
                    answer = form.save(commit=False)
                    answer.qustion_id = question  # с опечаткой как в модели
                    answer.save()
        elif action == 'add_required_material':
            form = RequiredMaterialForm(request.POST)
            if form.is_valid():
                material = form.save(commit=False)
                material.module = module
                material.is_required = True
                material.is_advanced = False
                material.save()

        elif action == 'add_advanced_material':
            form = AdvancedMaterialForm(request.POST)
            if form.is_valid():
                material = form.save(commit=False)
                material.module = module
                material.is_required = False
                material.is_advanced = True
                material.save()

        return redirect('module_manage', course_id=course_id, module_id=module_id)

class TeacherCabinetView(TeacherRequiredMixin, View):
    def get(self, request):
        # Курсы где пользователь главный автор
        owned_courses = Course.objects.filter(author=request.user)
        # Курсы где пользователь со-преподаватель
        co_courses = Course.objects.filter(co_authors=request.user)
        # Объединяем
        courses = (owned_courses | co_courses).distinct()
        context = {
            'courses': courses,
        }
        return render(request, 'courses/teacher_cabinet.html', context)

# Удаление курса
class CourseDeleteView(TeacherRequiredMixin, View):
    def post(self, request, course_id):
        course = Course.objects.get(id=course_id)
        course.delete()
        return redirect('courses')

# Редактирование курса
class CourseEditView(TeacherRequiredMixin, View):
    def get(self, request, course_id):
        course = Course.objects.get(id=course_id)
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()  # save_m2m вызывается автоматически когда instance задан
            return redirect('teacher_cabinet')
        return render(request, 'courses/course_edit.html', {'form': form, 'course': course})

    def post(self, request, course_id):
        course = Course.objects.get(id=course_id)
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('teacher_cabinet')
        return render(request, 'courses/course_edit.html', {'form': form})

# Удаление модуля
class ModuleDeleteView(TeacherRequiredMixin, View):
    def post(self, request, course_id, module_id):
        module = Module.objects.get(id=module_id)
        module.delete()
        return redirect('course_detail', id=course_id)

# Редактирование модуля
class ModuleEditView(TeacherRequiredMixin, View):
    def get(self, request, course_id, module_id):
        module = Module.objects.get(id=module_id)
        form = ModuleForm(instance=module)
        return render(request, 'courses/module_edit.html', {
            'form': form,
            'course_id': course_id,
            'module_id': module_id
        })

    def post(self, request, course_id, module_id):
        module = Module.objects.get(id=module_id)
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            return redirect('module_manage', course_id=course_id, module_id=module_id)
        return render(request, 'courses/module_edit.html', {'form': form})

# Удаление вопроса
class QuestionDeleteView(TeacherRequiredMixin, View):
    def post(self, request, course_id, module_id, question_id):
        question = Question.objects.get(id=question_id)
        question.delete()
        User_progerss.objects.filter(
            module_id=module_id
        ).update(best_score=0)
        return redirect('module_manage', course_id=course_id, module_id=module_id)

# Редактирование вопроса
class QuestionEditView(TeacherRequiredMixin, View):
    def get(self, request, course_id, module_id, question_id):
        question = Question.objects.get(id=question_id)
        form = QuestionForm(instance=question)

        return render(request, 'courses/question_edit.html', {
            'form': form,
            'course_id': course_id,
            'module_id': module_id,
            'question_id': question_id
        })

    def post(self, request, course_id, module_id, question_id):
        question = Question.objects.get(id=question_id)
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            User_progerss.objects.filter(
                module_id=module_id
            ).update(best_score=0)
            return redirect('module_manage', course_id=course_id, module_id=module_id)
        return render(request, 'courses/question_edit.html', {'form': form})

    # Удаление ответа
class AnswerDeleteView(TeacherRequiredMixin, View):
    def post(self, request, course_id, module_id, answer_id):
        answer = Answer.objects.get(id=answer_id)
        answer.delete()
        User_progerss.objects.filter(
            module_id=module_id
        ).update(best_score=0)
        return redirect('module_manage', course_id=course_id, module_id=module_id)


# Редактирование урока
class LessonEditView(TeacherRequiredMixin, View):
    def get(self, request, course_id, module_id, lesson_id):
        lesson = Lesson.objects.get(id=lesson_id)
        form = LessonForm(instance=lesson)
        return render(request, 'courses/lesson_edit.html', {
            'form': form,
            'course_id': course_id,
            'module_id': module_id,
        })

    def post(self, request, course_id, module_id, lesson_id):
        lesson = Lesson.objects.get(id=lesson_id)
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            return redirect('module_manage', course_id=course_id, module_id=module_id)
        return render(request, 'courses/lesson_edit.html', {'form': form})


# Удаление урока
class LessonDeleteView(TeacherRequiredMixin, View):
    def post(self, request, course_id, module_id, lesson_id):
        lesson = Lesson.objects.get(id=lesson_id)
        lesson.delete()
        lessons_remaining = Lesson.objects.filter(
            module_id=Module.objects.get(id=module_id)
        ).count()

        # Если уроков не осталось — удалить тест
        if lessons_remaining == 0:
            Test.objects.filter(
                module_id=Module.objects.get(id=module_id)
            ).delete()
        return redirect('module_manage', course_id=course_id, module_id=module_id)


# Редактирование теста
class TestEditView(TeacherRequiredMixin, View):
    def get(self, request, course_id, module_id, test_id):
        test = Test.objects.get(id=test_id)
        form = TestForm(instance=test)
        return render(request, 'courses/test_edit.html', {
            'form': form,
            'course_id': course_id,
            'module_id': module_id,
            'test_id': test_id,
        })

    def post(self, request, course_id, module_id, test_id):
        test = Test.objects.get(id=test_id)
        form = TestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            return redirect('module_manage', course_id=course_id, module_id=module_id)
        return render(request, 'courses/test_edit.html', {'form': form})


# Удаление теста
class TestDeleteView(TeacherRequiredMixin, View):
    def post(self, request, course_id, module_id, test_id):
        test = Test.objects.get(id=test_id)
        test.delete()
        return redirect('module_manage', course_id=course_id, module_id=module_id)


class ProfileEditView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'users/profile_edit.html', {'user': request.user})

    def post(self, request):
        user = request.user

        # Обновляем поля
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.username = request.POST.get('username', '')
        user.phone = request.POST.get('phone', '')
        user.bio = request.POST.get('bio', '')

        # Уведомления
        user.email_notifications = request.POST.get('email_notifications') == 'on'
        user.push_notifications = request.POST.get('push_notifications') == 'on'

        # Аватар
        if request.POST.get('delete_avatar') == 'on':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
        elif request.FILES.get('avatar'):
            if user.avatar:
                user.avatar.delete()
            user.avatar = request.FILES['avatar']

        user.save()
        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('student_cabinet')


class TeacherStatisticsView(TeacherRequiredMixin, View):
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, author=request.user)
        modules = Module.objects.filter(course_id=course).order_by('order_index')

        # Общие счетчики
        total_students = 0
        total_passed = 0
        total_avg_sum = 0
        total_avg_count = 0

        modules_stats = []
        for module in modules:
            test = Test.objects.filter(module_id=module).first()
            progress_records = User_progerss.objects.filter(
                module_id=module
            ).select_related('user_id')

            if progress_records.exists():
                stats = progress_records.aggregate(
                    avg_score=Avg('score'),
                    total_students=Count('user_id', distinct=True),
                    passed_count=Count('id', filter=Q(score__gte=60))
                )
                avg_score = stats['avg_score'] or 0
                total_students_module = stats['total_students']
                passed_count = stats['passed_count']
            else:
                avg_score = 0
                total_students_module = 0
                passed_count = 0

            # Добавляем к общим счетчикам
            total_students += total_students_module
            total_passed += passed_count
            if avg_score > 0:
                total_avg_sum += avg_score
                total_avg_count += 1

            modules_stats.append({
                'module': module,
                'test': test,
                'avg_score': round(avg_score, 1),
                'total_students': total_students_module,
                'passed_count': passed_count,
                'pass_rate': round(passed_count / total_students_module * 100) if total_students_module > 0 else 0,
                'progress_records': progress_records,
            })

        # Общая статистика курса
        course_stats = {
            'total_modules': modules.count(),
            'total_students': total_students,
            'total_passed': total_passed,
            'avg_score': round(total_avg_sum / total_avg_count, 1) if total_avg_count > 0 else 0,
        }

        context = {
            'course': course,
            'modules_stats': modules_stats,
            'course_stats': course_stats,  # Добавляем общую статистику
        }
        return render(request, 'courses/teacher_statistics.html', context)

class ModuleStatisticsView(TeacherRequiredMixin, View):
    """Детальная статистика по модулю с возможностью редактирования вопросов"""

    def get(self, request, course_id, module_id):
        course = get_object_or_404(Course, id=course_id, author=request.user)
        module = get_object_or_404(Module, id=module_id, course_id=course)
        test = Test.objects.filter(module_id=module).first()

        if test:
            # Получаем вопросы
            questions = Question.objects.filter(test_id=test)

            # Статистика по каждому вопросу
            questions_stats = []
            for question in questions:
                # Получаем ответы для вопроса (используем qustion_id)
                answers = Answer.objects.filter(qustion_id=question)

                questions_stats.append({
                    'question': question,
                    'answers': answers,
                    'total_attempts': 0,
                    'correct_percentage': 0,
                })
        else:
            questions = []
            questions_stats = []

        # Статистика по студентам
        progress_records = User_progerss.objects.filter(
            module_id=module
        ).select_related('user_id').order_by('-score')

        context = {
            'course': course,
            'module': module,
            'test': test,
            'questions': questions,
            'questions_stats': questions_stats,
            'progress_records': progress_records,
        }
        return render(request, 'courses/module_statistics.html', context)

class ModuleMaterialsView(LoginRequiredMixin, View):
    def get(self, request, course_id, module_id):
        module = get_object_or_404(Module, id=module_id)
        progress = User_progerss.objects.filter(user_id=request.user, module_id=module).first()

        # Определяем, какие материалы показывать
        if progress and progress.best_score >= 85:
            materials = ModuleMaterial.objects.filter(module=module, is_advanced=True)
            page_title = "Углублённые материалы"
        else:
            materials = ModuleMaterial.objects.filter(module=module, is_required=True)
            page_title = "Обязательные материалы для подготовки к пересдаче"

        # Получаем ID просмотренных материалов
        viewed_ids = StudentMaterialProgress.objects.filter(
            student=request.user, material__in=materials, viewed=True
        ).values_list('material_id', flat=True)

        context = {
            'module': module,
            'materials': materials,
            'viewed_ids': list(viewed_ids),
            'course_id': course_id,
            'page_title': page_title,
        }
        return render(request, 'courses/module_materials.html', context)

    def post(self, request, course_id, module_id):
        material_id = request.POST.get('material_id')
        if material_id:
            progress, created = StudentMaterialProgress.objects.get_or_create(
                student=request.user,
                material_id=material_id
            )
            if not progress.viewed:
                progress.viewed = True
                progress.viewed_at = timezone.now()
                progress.save()
        return redirect('module_materials', course_id=course_id, module_id=module_id)





class MaterialEditView(TeacherRequiredMixin, View):
    def get(self, request, course_id, module_id, material_id):
        material = get_object_or_404(ModuleMaterial, id=material_id, module_id=module_id)
        form = ModuleMaterialForm(instance=material)
        context = {
            'form': form,
            'material': material,
            'course_id': course_id,
            'module_id': module_id,
        }
        return render(request, 'courses/material_edit.html', context)

    def post(self, request, course_id, module_id, material_id):
        material = get_object_or_404(ModuleMaterial, id=material_id, module_id=module_id)
        form = ModuleMaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, 'Материал успешно обновлён')
            return redirect('module_manage', course_id=course_id, module_id=module_id)
        context = {
            'form': form,
            'material': material,
            'course_id': course_id,
            'module_id': module_id,
        }
        return render(request, 'courses/material_edit.html', context)

class MaterialDeleteView(TeacherRequiredMixin, View):
    def post(self, request, course_id, module_id, material_id):
        material = get_object_or_404(ModuleMaterial, id=material_id, module_id=module_id)
        material.delete()
        messages.success(request, 'Материал успешно удалён')
        return redirect('module_manage', course_id=course_id, module_id=module_id)