from django.urls import path

from users.views import LoginView, LogoutView, CustomLoginView, RegisterView, RegistrationPendingView, \
    AdminDashboardView, ApproveUserView, ModulesAdminView, CoursesAdminView, TeachersView, StudentsView, \
    PendingUsersView, RejectUserView

urlpatterns=(
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),

path('registration/pending/',
     RegistrationPendingView.as_view(), name='registration_pending'),
    path(
        'admin_panel/',AdminDashboardView.as_view(),name='admin_dashboard'),
path(
    'admin-panel/approve/<int:user_id>/', ApproveUserView.as_view(), name='approve_user'),
path(
        'admin-panel/students/',StudentsView.as_view(),
        name='admin_students'),

    path(
        'admin-panel/teachers/',
        TeachersView.as_view(),
        name='admin_teachers'
    ),

    path(
        'admin-panel/courses/',
        CoursesAdminView.as_view(),
        name='admin_courses'
    ),

    path(
        'admin-panel/modules/',
        ModulesAdminView.as_view(),
        name='admin_modules'
    ),
    path(
        'admin-panel/pending-users/',
        PendingUsersView.as_view(),
        name='admin_pending_users'
    ),
path('admin-panel/reject/<int:user_id>/', RejectUserView.as_view(), name='reject_user'),

)