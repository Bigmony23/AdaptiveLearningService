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
    """Уведомление преподавателю о студенте, который не может сдать тест после 6 попыток"""
    teacher = module.course_id.author

    Notification.objects.create(
        user=teacher,
        title=f'Студент испытывает трудности',
        message=f'Студент {student.get_full_name() or student.username} ({student.email}) не может сдать тест "{module.title}" после {attempts_count} попыток. Обратите внимание!',
        notification_type='student_failed'
    )

