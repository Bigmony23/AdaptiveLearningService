from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View

from courses.models import Course, Module
from users.forms import  CustomAuthenticationForm, CustomUserCreationForm
from users.utils import send_admin_notification

from django.views import View
from django.shortcuts import render, redirect

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from users.models import CustomUser
from django.shortcuts import redirect, get_object_or_404

class RegisterView(View):
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'users/register.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Сохраняем пользователя
            user = form.save(commit=False)
            user.is_active = False
            user.role = 'student'
            user.save()

            # Отправляем уведомление администраторам
            send_admin_notification(user)

            return redirect('registration_pending')

        return render(request, 'users/register.html', {'form': form})


class RegistrationPendingView(View):
    def get(self, request):
        return render(request,'users/registration_pending.html')
class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('home')

class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request,'Вы вышли из системы')
        return redirect('login')
# Create your views here.

# users/views_admin.py




class AdminDashboardView(LoginRequiredMixin, View):
    def get(self, request):

        context = {
            'pending_count': CustomUser.objects.filter(is_active=False).count(),
            'students_count': CustomUser.objects.filter(role='student').count(),
            'teachers_count': CustomUser.objects.filter(role='teacher').count(),
            'courses_count': Course.objects.count(),
            'modules_count': Module.objects.count(),
        }

        return render(
            request,
            'admin_panel/dashboard.html',
            context
        )
# users/views_admin.py




from django.contrib import messages

class ApproveUserView(LoginRequiredMixin, View):
    def post(self, request, user_id):

        if request.user.role != 'admin':
            return redirect('home')

        user = get_object_or_404(
            CustomUser,
            id=user_id
        )

        user.is_active = True
        user.save()

        messages.success(
            request,
            f'Пользователь {user.username} успешно активирован'
        )

        return redirect('admin_pending_users')

class PendingUsersView(LoginRequiredMixin, View):
    def get(self, request):

        if request.user.role != 'admin':
            return redirect('home')

        users = CustomUser.objects.filter(
            is_active=False
        )

        return render(
            request,
            'admin_panel/pending_users.html',
            {
                'pending_users': users
            }
        )
class StudentsView(LoginRequiredMixin, View):
    def get(self, request):

        students = CustomUser.objects.filter(
            role='student'
        )

        return render(
            request,
            'admin_panel/students.html',
            {'students': students}
        )

class TeachersView(LoginRequiredMixin, View):
    def get(self, request):

        teachers = CustomUser.objects.filter(
            role='teacher'
        )

        return render(
            request,
            'admin_panel/teachers.html',
            {'teachers': teachers}
        )
from courses.models import Course

class CoursesAdminView(LoginRequiredMixin, View):
    def get(self, request):

        courses = Course.objects.all()

        return render(
            request,
            'admin_panel/courses.html',
            {'courses': courses}
        )

from courses.models import Module

class ModulesAdminView(LoginRequiredMixin, View):
    def get(self, request):

        modules = Module.objects.select_related(
            'course_id'
        )

        return render(
            request,
            'admin_panel/modules.html',
            {'modules': modules}
        )