from notifications.models import Notification
from users.models import CustomUser


def send_new_module_notification(module):
    """Уведомление студентам о новом модуле"""
    students = CustomUser.objects.filter(role='student')

    for student in students:
        Notification.objects.create(
            user=student,
            title=f'Новый модуль: {module.title}',
            message=f'В курсе "{module.course_id.title}" добавлен новый модуль "{module.title}". Приступайте к изучению!',
            notification_type='new_module'
        )


def send_new_lesson_notification(lesson):
    """Уведомление студентам о новом уроке"""
    students = CustomUser.objects.filter(role='student')

    for student in students:
        Notification.objects.create(
            user=student,
            title=f'Новый урок: {lesson.title}',
            message=f'В модуле "{lesson.module_id.title}" добавлен новый урок "{lesson.title}".',
            notification_type='new_lesson'
        )


def send_new_test_notification(test):
    """Уведомление студентам о новом тесте"""
    students = CustomUser.objects.filter(role='student')

    for student in students:
        Notification.objects.create(
            user=student,
            title=f'Новый тест: {test.title}',
            message=f'В модуле "{test.module_id.title}" появился новый тест "{test.title}".',
            notification_type='new_test'
        )


def send_teacher_alert_about_failing_student(student, module, attempts_count):
    """Уведомление преподавателю каждые 3 неудачные попытки"""
    teacher = module.course_id.author

    if attempts_count == 3:
        title = 'Студент не сдаёт тест (3 попытки)'
        message = (
            f'Студент {student.get_full_name() or student.username} ({student.email}) '
            f'не смог сдать тест модуля "{module.title}" после 3 попыток. '
            f'Рекомендуется обратить внимание.'
        )
    elif attempts_count == 6:
        title = 'Студент испытывает серьёзные трудности (6 попыток)'
        message = (
            f'Студент {student.get_full_name() or student.username} ({student.email}) '
            f'не смог сдать тест модуля "{module.title}" после 6 попыток. '
            f'Необходима помощь преподавателя!'
        )
    elif attempts_count == 9:
        title = 'Критическая ситуация! Студент не сдаёт тест (9 попыток)'
        message = (
            f'Студент {student.get_full_name() or student.username} ({student.email}) '
            f'не смог сдать тест модуля "{module.title}" после 9 попыток. '
            f'Срочно свяжитесь со студентом!'
        )
    else:
        return  # Не отправляем при других попытках

    Notification.objects.create(
        user=teacher,
        title=title,
        message=message,
        notification_type='student_failed'
    )


def send_admin_notification_about_registration(user):
    """Уведомление администраторам о новой регистрации студента"""
    from users.models import CustomUser

    # Отправляем всем администраторам/учителям
    staff_users = CustomUser.objects.filter(is_staff=True)

    for staff in staff_users:
        Notification.objects.create(
            user=staff,
            title=f'Новая регистрация: {user.get_full_name() or user.username}',
            message=f'Студент {user.email} зарегистрировался и требует активации.',
            notification_type='registration'
        )