from django.db import models


class Statistique(models.Model):
    date = models.DateField()
    type_stat = models.CharField(max_length=50)
    categorie = models.CharField(max_length=100)
    valeur = models.IntegerField(default=0)
    details = models.JSONField(default=dict, blank=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'statistiques'
        unique_together = ['date', 'type_stat', 'categorie']
        ordering = ['-date']
        verbose_name = 'Statistique'
        verbose_name_plural = 'Statistiques'

    def __str__(self):
        return f"{self.type_stat} - {self.categorie} ({self.date})"
