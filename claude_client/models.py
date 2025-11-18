from django.db import models
from authentication.models import AuthUser
from flashcards.models import Card

class DFBLUserInteraction(models.Model):
    class TutorStyle(models.TextChoices):
        STRICT = "strict", "Strict"
        FRIENDLY = "friendly", "Friendly"
        PROFESSIONAL = "professional", "Professional"
        SPEED_RUN = "speed_run", "Speed run"
        SOCRATIC = "socratic", "Socratic"
        SUPPORTIVE = "supportive", "Supportive"
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    neuro_response = models.TextField()

    tutor_style = models.CharField(max_length=255, choices=TutorStyle.choices, default=TutorStyle.SOCRATIC)

    # Explanation field
    explanation = models.TextField(null=True, blank=True)
    
    # Connection fields
    principles = models.JSONField(default=list, null=True, blank=True)
    solution_summary = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def tutor_style_descriptions():
        return {
                UPSUserInteraction.TutorStyle.STRICT:
                    "A no-nonsense tutor who challenges you and pushes you hard.",
                UPSUserInteraction.TutorStyle.FRIENDLY:
                    "A warm, casual tutor who explains things gently and encourages you.",
                UPSUserInteraction.TutorStyle.PROFESSIONAL:
                    "A polished, classroom-style instructor with clear reasoning.",
                UPSUserInteraction.TutorStyle.SPEED_RUN:
                    "Fast-paced, optimized explanations focusing on efficiency.",
                UPSUserInteraction.TutorStyle.SOCRATIC:
                    "A question-driven tutor that guides you to discover the answer.",
                UPSUserInteraction.TutorStyle.SUPPORTIVE:
                    "A motivational guide who reassures you and celebrates progress."
        }

    def get_style_description(self):
        return self.tutor_style_descriptions()[self.tutor_style]

class UPSUserInteraction(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    question = models.TextField()
    neuro_response = models.TextField()

    # Explanation field
    explanation = models.TextField(null=True, blank=True)
    
    # Connection fields
    principles = models.JSONField(default=list, null=True, blank=True)
    solution_summary = models.TextField(null=True, blank=True)