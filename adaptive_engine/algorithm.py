from django.db.models import Avg, Sum

from courses.models import Module, User_progerss, Course
from users.models import CustomUser
from adaptive_engine.models import AdaptiveRecomendation


# adaptive_engine/algorithm.py

def generate_recommendation(user_id, module_id, score, request=None):
    user = CustomUser.objects.get(id=user_id)
    module = Module.objects.get(id=module_id)

    progress = User_progerss.objects.get(user_id=user, module_id=module)
    attempts = progress.attempts

    # Получаем слабые темы (уже сохраненные в progress)
    weak_topics = progress.weak_topics if progress.weak_topics else []

    # Анализируем прогресс
    previous_scores = User_progerss.objects.filter(
        user_id=user, module_id=module
    ).exclude(id=progress.id).values_list('score', flat=True)
    avg_previous_score = sum(previous_scores) / len(previous_scores) if previous_scores else score

    # ===== ЛОГИКА РЕКОМЕНДАЦИЙ =====
    if score < 60:
        if attempts > 3:
            recommendation_type = 'additional'
            if weak_topics:
                recommendation_description = f"""
                Вы набрали {score:.1f}% за {attempts} попыток.

                📊 Анализ результатов:
                • Сложные темы: {', '.join(weak_topics)}
                • Рекомендуемое время на изучение: 2-3 часа

                📚 Дополнительные материалы:
                • Видео-уроки по сложным темам
                • Интерактивные тренажеры

                💡 Совет: Обратите особое внимание на выделенные темы.
                """
            else:
                recommendation_description = f"""
                Вы набрали {score:.1f}% за {attempts} попыток.

                📊 Ваша статистика:
                • Средний балл за все попытки: {avg_previous_score:.1f}%
                • Использовано попыток: {attempts}/3

                📚 Рекомендованные дополнительные материалы:
                • Базовые видео-лекции по всему модулю
                • Пошаговые руководства с примерами
                • Практические задания для закрепления

                💡 Стратегия улучшения:
                1. Начните с повторения базовых понятий
                2. Выполните практические упражнения
                3. Обратитесь к преподавателю за помощью
                """
        else:
            recommendation_type = 'repeat'
            recommendation_description = f"""
            Вы набрали {score:.1f}% на {attempts} попытке.

            📊 Ваши результаты:
            • Нужно улучшить до 60% для продолжения
            • Осталось попыток: {3 - attempts}

            🎯 План действий:
            1. 📖 Внимательно перечитайте теоретический материал
            2. ✍️ Сделайте конспект основных определений
            3. 📝 Выполните дополнительные упражнения
            4. 🔄 Пройдите тест заново

            💡 Фокус на: {', '.join(weak_topics) if weak_topics else 'темах, где были ошибки'}
            """

    elif score >= 85:
        recommendation_type = 'advanced'
        improvement = progress.improvement_rate or 0
        recommendation_description = f"""
        Поздравляем! Отличный результат — {score:.1f}%!

        📊 Ваше достижение:
        • {'📈 Улучшение на ' + f'{improvement:.1f}%' if improvement > 0 else '⭐ Стабильно высокий результат'}

        🚀 Углубленное изучение:
        • Проектная работа по теме модуля
        • Исследовательские задания
        • Дополнительные главы из продвинутого курса

        
        """

    else:  # 60% <= score < 85%
        recommendation_type = 'next'
        if score < 70:
            focus_areas = "требуют внимания: разберите ошибки в тесте"
            bonus = ""
        elif score < 78:
            focus_areas = "хорошо, но можно лучше: повторите сложные моменты"
            bonus = ""
        else:
            focus_areas = "отлично! вы готовы к следующему модулю"
            bonus = "\n🎓 "

        recommendation_description = f"""
        Хороший результат — {score:.1f}%!

        📊 Оценка:
        • {'Неплохо, но есть потенциал для роста' if score < 75 else 'Стабильный прогресс'}
        • Вы освоили {int(score)}% материала
        {f'• Слабые темы: {", ".join(weak_topics)}' if weak_topics else ''}

        ➡️ Рекомендация: перейти к следующему модулю

        📌 На что обратить внимание:
        • {focus_areas}
        • Закрепите знания быстрым повторением перед следующим модулем
        {bonus}

        🎯 Следующие шаги:
        1. Сохраните конспект текущего модуля
        2. Переходите к изучению следующего модуля
        3. Периодически возвращайтесь для повторения
        """

    # Сохраняем рекомендацию
    AdaptiveRecomendation.objects.create(
        user_id=user,
        module_id=module,
        recommendation_type=recommendation_type,
        recommendation_description=recommendation_description.strip(),
        score_at_time=score,
        attempt_number=attempts
    )


def get_weak_topics(user_id, module_id):
    """Анализирует, какие темы вызвали трудности"""
    from courses.models import TestResult, Question

    # Получаем неправильные ответы студента
    wrong_answers = TestResult.objects.filter(
        user_id=user_id,
        module_id=module_id,
        is_correct=False
    ).select_related('question')

    # Группируем по темам
    weak_topics = {}
    for wrong in wrong_answers:
        topic = wrong.question.topic or 'Общая тема'
        weak_topics[topic] = weak_topics.get(topic, 0) + 1

    # Возвращаем самые проблемные темы (топ-3)
    sorted_topics = sorted(weak_topics.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, count in sorted_topics[:3]]


def send_personalized_notification(user, module, score, recommendation_type):
    """Отправляет персонализированное уведомление студенту"""
    from notifications.models import Notification

    notification_templates = {
        'repeat': {
            'title': '📚 Требуется повторение материала',
            'message': f'Ваш результат: {score:.1f}%. Повторите модуль "{module.title}" и попробуйте снова.'
        },
        'additional': {
            'title': '📖 Дополнительные материалы',
            'message': f'Для модуля "{module.title}" подготовлены дополнительные материалы для лучшего усвоения.'
        },
        'next': {
            'title': '🎯 Переход к следующему модулю',
            'message': f'Поздравляем! Вы успешно освоили модуль "{module.title}". Переходите к следующему.'
        },
        'advanced': {
            'title': '🚀 Углубленное изучение',
            'message': f'Отличный результат! Вам доступны продвинутые материалы по модулю "{module.title}".'
        }
    }

    template = notification_templates.get(recommendation_type)
    if template:
        Notification.objects.create(
            user=user,
            title=template['title'],
            message=template['message'],
            notification_type='recommendation'
        )

class ProgressAnalytics:
    """Аналитика прогресса студента для улучшения адаптивности"""

    @staticmethod
    def get_student_performance(user_id):
        user = CustomUser.objects.get(id=user_id)
        progress_records = User_progerss.objects.filter(user_id=user)

        analytics = {
            'total_modules': progress_records.count(),
            'average_score': progress_records.aggregate(Avg('score'))['score__avg'],
            'total_attempts': progress_records.aggregate(Sum('attempts'))['attempts__sum'],
            'success_rate': (progress_records.filter(
                score__gte=60).count() / progress_records.count() * 100) if progress_records else 0,
            'excellent_rate': (progress_records.filter(
                score__gte=85).count() / progress_records.count() * 100) if progress_records else 0,
            'weak_modules': [],
            'strong_modules': []
        }

        # Определяем слабые и сильные модули
        for progress in progress_records:
            if progress.score < 60 and progress.attempts >= 3:
                analytics['weak_modules'].append({
                    'module': progress.module.title,
                    'score': progress.score,
                    'attempts': progress.attempts
                })
            elif progress.score >= 85:
                analytics['strong_modules'].append({
                    'module': progress.module_id.title,
                    'score': progress.score
                })

        return analytics

    @staticmethod
    def get_learning_pace_recommendation(user_id):
        """Рекомендация по темпу обучения"""
        analytics = ProgressAnalytics.get_student_performance(user_id)

        if analytics['average_score'] >= 80:
            return "Высокий темп - можно ускориться"
        elif analytics['average_score'] >= 60:
            return "Средний темп - продолжайте в том же духе"
        else:
            return "Низкий темп - рекомендуется замедлиться и больше практиковаться"


def get_adaptive_learning_path(user_id, course_id):
    """Формирует адаптивный путь обучения на основе статистики"""
    user = CustomUser.objects.get(id=user_id)
    course = Course.objects.get(id=course_id)
    modules = Module.objects.filter(course=course)

    learning_path = []

    for module in modules:
        progress = User_progerss.objects.filter(user_id=user, module_id=module).first()

        module_info = {
            'module': module,
            'status': 'not_started',
            'estimated_time': module.estimated_hours,
            'recommendation': None
        }

        if not progress:
            module_info['status'] = 'not_started'
            module_info['recommendation'] = 'Начать изучение'
        elif progress.score < 60:
            if progress.attempts >= 3:
                module_info['status'] = 'need_help'
                module_info['recommendation'] = 'Требуется помощь преподавателя'
            else:
                module_info['status'] = 'need_repeat'
                module_info['recommendation'] = 'Рекомендуется повторить'
        elif progress.score < 85:
            module_info['status'] = 'completed_basic'
            module_info['recommendation'] = 'Можно переходить дальше'
        else:
            module_info['status'] = 'completed_advanced'
            module_info['recommendation'] = 'Доступны углубленные материалы'

        learning_path.append(module_info)

    return learning_path