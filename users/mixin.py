from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class TeacherRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != 'teacher':
            messages.error(request, 'Доступ только для преподавателей')
            return redirect('home')   # или редирект куда-то
        return super().dispatch(request, *args, **kwargs)