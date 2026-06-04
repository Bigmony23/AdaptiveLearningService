from django.contrib import admin

from adaptive_engine.models import AdaptiveRecomendation


class AdaptiveEngineAdmin(admin.ModelAdmin):
    list_display = ["user_id",'module_id',"recommendation_type","recommendation_description",'created_at']

admin.site.register(AdaptiveRecomendation,AdaptiveEngineAdmin)
# Register your models here.
