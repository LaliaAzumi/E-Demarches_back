from rest_framework import serializers
from .models import Utilisateur, Citoyen, Agent


class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id', 'email', 'nom', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UtilisateurCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Utilisateur
        fields = ['id', 'email', 'nom', 'role', 'password', 'is_active']

    def create(self, validated_data):
        user = Utilisateur.objects.create_user(**validated_data)
        return user


class CitoyenSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurSerializer(read_only=True)
    utilisateur_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Citoyen
        fields = ['id', 'utilisateur', 'utilisateur_id', 'cin', 'adresse']
        read_only_fields = ['id']


class AgentSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurSerializer(read_only=True)
    utilisateur_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Agent
        fields = ['id', 'utilisateur', 'utilisateur_id', 'matricule', 'service']
        read_only_fields = ['id']
