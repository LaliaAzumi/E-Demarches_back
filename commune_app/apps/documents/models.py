from django.db import models
from apps.dossiers.models import Demande


class Document(models.Model):
    id = models.AutoField(primary_key=True)
    demande = models.ForeignKey(
        Demande,
        on_delete=models.CASCADE,
        db_column='demande_id'
    )
    nom_fichier = models.CharField(max_length=255, null=True, blank=True)
    type_document = models.CharField(max_length=50, db_column='type')
    url = models.TextField()
    date_upload = models.DateTimeField(auto_now_add=True, db_column='date_upload')

    class Meta:
        db_table = 'documents'
        ordering = ['-date_upload']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        indexes = [
            models.Index(fields=['demande']),
            models.Index(fields=['date_upload']),
            models.Index(fields=['type_document']),
        ]

    def __str__(self):
        return f"Document #{self.id} - {self.nom_fichier}"
