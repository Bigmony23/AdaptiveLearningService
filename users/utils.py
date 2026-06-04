from notifications.models import Notification
from users.models import CustomUser


def send_admin_notification(user):
    """Отправить уведомление администраторам о новой регистрации"""
    admins = CustomUser.objects.filter(is_staff=True)

    for admin in admins:
        Notification.objects.create(
            user=admin,
            title='Новая регистрация пользователя',
            message=f'Пользователь {user.get_full_name() or user.username} ({user.email}) ждёт активации аккаунта.',
            notification_type='registration'
        )