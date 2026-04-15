"""
Serializers pour les profils (Citoyen, Agent, Administrateur)
"""

from rest_framework import serializers

from ..models import Citoyen, AgentAdministratif, Administrateur, Utilisateur


class CitoyenSerializer(serializers.ModelSerializer):
    """
    Serializer pour Citoyen.
    """
    utilisateur = serializers.SerializerMethodField()
    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.filter(role='citoyen'),
        source='utilisateur',
        write_only=True,
        required=False
    )
    age = serializers.IntegerField(source='get_age', read_only=True)
    
    class Meta:
        model = Citoyen
        fields = [
            'id', 'utilisateur', 'utilisateur_id',
            'date_naissance', 'lieu_naissance', 'age',
            'adresse', 'ville', 'code_postal', 'pays',
            'numero_identite', 'numero_carte_identite',
            'situation_professionnelle'
        ]
        read_only_fields = ['numero_identite']
    
    def get_utilisateur(self, obj):
        """Retourne les données utilisateur embarquées."""
        from .utilisateur_serializers import UtilisateurSerializer
        return UtilisateurSerializer(obj.utilisateur).data


class AgentSerializer(serializers.ModelSerializer):
    """
    Serializer pour AgentAdministratif.
    """
    utilisateur = serializers.SerializerMethodField()
    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.filter(role='agent'),
        source='utilisateur',
        write_only=True,
        required=False
    )
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    anciennete = serializers.IntegerField(source='get_anciennete', read_only=True)
    
    class Meta:
        model = AgentAdministratif
        fields = [
            'id', 'utilisateur', 'utilisateur_id',
            'matricule', 'departement', 'fonction',
            'date_embauche', 'statut', 'statut_display',
            'anciennete', 'niveau_autorisation'
        ]
        read_only_fields = ['matricule']
    
    def get_utilisateur(self, obj):
        """Retourne les données utilisateur embarquées."""
        from .utilisateur_serializers import UtilisateurSerializer
        return UtilisateurSerializer(obj.utilisateur).data


class AdministrateurSerializer(serializers.ModelSerializer):
    """
    Serializer pour Administrateur.
    """
    utilisateur = serializers.SerializerMethodField()
    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.filter(role='administrateur'),
        source='utilisateur',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Administrateur
        fields = [
            'id', 'utilisateur', 'utilisateur_id',
            'niveau_admin', 'derniere_connexion_admin',
            'actions_logees'
        ]
    
    def get_utilisateur(self, obj):
        """Retourne les données utilisateur embarquées."""
        from .utilisateur_serializers import UtilisateurSerializer
        return UtilisateurSerializer(obj.utilisateur).data
