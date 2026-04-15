"""
Modèle pour le Chatbot FAQ
"""

from django.db import models
from .mixins import TimestampMixin


class FAQChatbot(TimestampMixin, models.Model):
    """
    Modèle pour les questions/réponses du chatbot FAQ.
    """
    question = models.TextField(verbose_name="Question")
    reponse = models.TextField(verbose_name="Réponse")
    categorie = models.CharField(max_length=100, blank=True, null=True, verbose_name="Catégorie")
    mots_cles = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mots-clés")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    usage_count = models.PositiveIntegerField(default=0, verbose_name="Nombre d'utilisations")
    
    class Meta:
        db_table = 'faq_chatbot'
        ordering = ['-usage_count', '-created_at']
        verbose_name = 'FAQ Chatbot'
        verbose_name_plural = 'FAQ Chatbots'
    
    def __str__(self):
        return f"{self.categorie}: {self.question[:50]}..."
