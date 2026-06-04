from rest_framework import serializers

from adaptive_engine.models import AdaptiveRecomendation


class AdaptiveEngineSerializer(serializers.ModelSerializer):
    class Meta:
        model=AdaptiveRecomendation
        fields='__all__'