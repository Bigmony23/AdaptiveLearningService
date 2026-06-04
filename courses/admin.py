from django.contrib import admin
from courses.models import Course,Module,Lesson,Question,Answer,User_progerss,Test

class CourseAdmin(admin.ModelAdmin):
    list_display=['title','description','author','difficulty_level','is_published','created_at','updated_at']

class ModuleAdmin(admin.ModelAdmin):
    list_display=['course_id','title','description','order_index','difficulty_level','created_at']

class LessonAdmin(admin.ModelAdmin):
    list_display=['module_id',"title","content_type","order_index","created_at"]

class QuestionAdmin(admin.ModelAdmin):
    list_display=["test_id","question_text","question_type","points"]

class AnswerAdmin(admin.ModelAdmin):
    list_display=["qustion_id",'answer_text',"is_correct"]

class User_progerssAdmin(admin.ModelAdmin):
    list_display=["user_id",'module_id','score','attempts','time_spent','status','created_at']

class TestAdmin(admin.ModelAdmin):
    list_display=['module_id','title','passing_score','max_score','created_at']

# Register your models here.
admin.site.register(Course,CourseAdmin)
admin.site.register(Module,ModuleAdmin)
admin.site.register(Lesson,LessonAdmin)
admin.site.register(Question,QuestionAdmin)
admin.site.register(Answer,AnswerAdmin)
admin.site.register(Test,TestAdmin)
admin.site.register(User_progerss,User_progerssAdmin)
