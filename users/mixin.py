
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from courses.models import Course


class TeacherRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != 'teacher':
            messages.error(request, 'Доступ только для преподавателей')
            return redirect('home')

        # Проверка доступа к конкретному курсу
        course_id = kwargs.get('course_id')
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                is_author = course.author == request.user
                is_co_author = course.co_authors.filter(id=request.user.id).exists()
                if not is_author and not is_co_author:
                    messages.error(request, 'У вас нет доступа к этому курсу')
                    return redirect('teacher_cabinet')
            except Course.DoesNotExist:
                pass

        return super().dispatch(request, *args, **kwargs)