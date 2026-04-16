#!/usr/bin/env python
"""
================================================================================
FICHIER: manage.py
PROJET: Api_python
RÔLE: Point d'entrée Django pour les commandes administratives

USAGE:
    python manage.py runserver          # Démarrer le serveur
    python manage.py makemigrations     # Créer les migrations
    python manage.py migrate            # Appliquer les migrations
    python manage.py createsuperuser    # Créer un admin
    python manage.py shell              # Shell Django
    python manage.py test               # Lancer les tests

Django administrative utility.
================================================================================
"""

import os
import sys


def main():
    """Run administrative tasks."""
    # Définir les settings par défaut
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Api_python.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Exécuter la commande
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
