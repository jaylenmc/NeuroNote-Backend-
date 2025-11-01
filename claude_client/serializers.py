from rest_framework import serializers
from .models import UPSUserInteraction

class UPSSerializer(serializers.Serializer):
    question = serializers.CharField()
    explanation = serializers.CharField(required=False)
    principles = serializers.JSONField(required=False, default=list)
    solution_summary = serializers.CharField(required=False)

    def validate(self, data):
        explanation = data.get("explanation")
        principles = data.get("principles")
        solution_summary = data.get("solution_summary")

        if not (
            (explanation and not principles and not solution_summary) or 
            (not explanation and (principles and solution_summary))
        ):
            raise serializers.ValidationError("Along with question include either 'Explanation' or 'Principles' and 'Solution Summary'")
        
        return data
    
    def create(self, data):
        type = self.context.get("type")
        user = self.context.get("user")

        if type == 'explain':
            explanation = data.get('explanation')
            question = data.get('question')

            explanation_obj = UPSUserInteraction.objects.create(
                user=user,
                explanation=explanation,
                question=question
            )
            return explanation_obj
        
        elif type == 'connection':
            principles = data.get('principles')
            solution_summary = data.get("solution_summary")
            user = user

            connection_obj = UPSUserInteraction.objects.create(
                user=user,
                principles=principles,
                solution_summary=solution_summary
            )
            return connection_obj