from django.urls import path

from courses import views

urlpatterns = [
    path("courses/", views.CourseView.as_view(), name="courses"),
    path("courses/<int:id>", views.CourseDetailView.as_view(), name="course_detail"),
    path("courses/<int:course_id>/module/<int:module_id>",views.ModuleView.as_view(), name="module_lessons"),
    path("courses/<int:course_id>/module/<int:module_id>/lesson/<int:lesson_id>",views.LessonView.as_view(), name="lesson_detail"),
path('courses/<int:course_id>/module/<int:module_id>/test/',
     views.TestView.as_view(), name='test'),
path('courses/<int:course_id>/module/<int:module_id>/test/result/',
     views.TestResultView.as_view(), name='test_result'),
path('cabinet/', views.StudentCabinetView.as_view(), name='student_cabinet'),
path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
path('courses/<int:course_id>/module/create/', views.ModuleCreateView.as_view(), name='module_create'),
path('courses/<int:course_id>/module/<int:module_id>/manage/',
     views.ModuleManageView.as_view(), name='module_manage'),
path('teacher/cabinet/', views.TeacherCabinetView.as_view(), name='teacher_cabinet'),
# Курс
path('courses/<int:course_id>/edit/', views.CourseEditView.as_view(), name='course_edit'),
path('courses/<int:course_id>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),

# Модуль
path('courses/<int:course_id>/module/<int:module_id>/edit/', views.ModuleEditView.as_view(), name='module_edit'),
path('courses/<int:course_id>/module/<int:module_id>/delete/', views.ModuleDeleteView.as_view(), name='module_delete'),

# Вопрос
path('courses/<int:course_id>/module/<int:module_id>/question/<int:question_id>/edit/', views.QuestionEditView.as_view(), name='question_edit'),
path('courses/<int:course_id>/module/<int:module_id>/question/<int:question_id>/delete/', views.QuestionDeleteView.as_view(), name='question_delete'),

# Ответ
path('courses/<int:course_id>/module/<int:module_id>/answer/<int:answer_id>/delete/', views.AnswerDeleteView.as_view(), name='answer_delete'),
# Урок
path('courses/<int:course_id>/module/<int:module_id>/lesson/<int:lesson_id>/edit/',
     views.LessonEditView.as_view(), name='lesson_edit'),
path('courses/<int:course_id>/module/<int:module_id>/lesson/<int:lesson_id>/delete/',
     views.LessonDeleteView.as_view(), name='lesson_delete'),

# Тест
path('courses/<int:course_id>/module/<int:module_id>/test/<int:test_id>/edit/',
     views.TestEditView.as_view(), name='test_edit'),
path('courses/<int:course_id>/module/<int:module_id>/test/<int:test_id>/delete/',
     views.TestDeleteView.as_view(), name='test_delete'),
path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),

path('courses/<int:course_id>/statistics/',
         views.TeacherStatisticsView.as_view(),
         name='teacher_statistics'),

path('courses/<int:course_id>/module/<int:module_id>/statistics/',
         views.ModuleStatisticsView.as_view(),
         name='module_statistics'),

path('courses/<int:course_id>/module/<int:module_id>/materials/',
     views.ModuleMaterialsView.as_view(), name='module_materials'),
# Удаление материала
# Редактирование материала (отдельная страница)
path('courses/<int:course_id>/module/<int:module_id>/material/<int:material_id>/edit/',
     views.MaterialEditView.as_view(), name='material_edit'),

    # Удаление материала
path('courses/<int:course_id>/module/<int:module_id>/material/<int:material_id>/delete/',
         views.MaterialDeleteView.as_view(), name='material_delete'),

]