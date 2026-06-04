from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser


@admin.action(description='✅ Активировать выбранных студентов')
def activate_users(modeladmin, request, queryset):
    count = queryset.filter(is_active=False).update(is_active=True)
    modeladmin.message_user(request, f'Активировано {count} студентов')


@admin.action(description='❌ Деактивировать выбранных студентов')
def deactivate_users(modeladmin, request, queryset):
    count = queryset.filter(is_active=True).update(is_active=False)
    modeladmin.message_user(request, f'Деактивировано {count} студентов')


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    # Какие поля показывать в списке пользователей
    list_display = ['username', 'email', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    actions = [activate_users, deactivate_users]
    search_fields = ('username', 'first_name', 'last_name', 'email')

    # Поля на странице редактирования
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'patronymic', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': '⚠️ Для студентов: отметьте is_active чтобы активировать аккаунт'
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Role'), {'fields': ('role',)}),
    )

    # Поля при добавлении нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'role', 'is_active'),
        }),
    )

    readonly_fields = ['date_joined', 'last_login']

    def get_readonly_fields(self, request,obj=None):
        if request.user.is_superuser:
            return ['date_joined', 'last_login']
        return ['date_joined', 'last_login', 'is_superuser', 'user_permissions']