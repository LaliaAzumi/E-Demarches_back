#!/usr/bin/env python
"""
Script pour créer et vérifier la base de données SQLite.
"""
import os
import sys
import sqlite3

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Api_python.settings')

# Vérifier si le fichier db.sqlite3 existe
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
print(f"Database path: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")

try:
    import django
    django.setup()
    
    from django.core.management import call_command
    from django.db import connection
    
    # Créer les migrations pour core
    print("\n=== Création des migrations ===")
    call_command('makemigrations', 'core', verbosity=2)
    
    # Migrer toutes les apps
    print("\n=== Exécution des migrations ===")
    call_command('migrate', '--run-syncdb', verbosity=2)
    
    # Vérifier les tables
    print("\n=== Tables créées ===")
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        core_tables = []
        auth_tables = []
        django_tables = []
        other_tables = []
        
        for (table_name,) in tables:
            if table_name.startswith('core_'):
                core_tables.append(table_name)
            elif table_name.startswith('auth_'):
                auth_tables.append(table_name)
            elif table_name.startswith('django_'):
                django_tables.append(table_name)
            else:
                other_tables.append(table_name)
        
        print(f"\nTables Core ({len(core_tables)}):")
        for t in core_tables:
            print(f"  - {t}")
            
        print(f"\nTables Auth ({len(auth_tables)}):")
        for t in auth_tables:
            print(f"  - {t}")
            
        print(f"\nTables Django ({len(django_tables)}):")
        for t in django_tables:
            print(f"  - {t}")
            
        if other_tables:
            print(f"\nAutres tables ({len(other_tables)}):")
            for t in other_tables:
                print(f"  - {t}")
    
    # Créer un super utilisateur si aucun n'existe
    print("\n=== Vérification super utilisateur ===")
    from core.models import Utilisateur
    
    if not Utilisateur.objects.filter(role='administrateur').exists():
        print("Aucun administrateur trouvé. Création d'un super utilisateur...")
        print("Email: admin@example.com")
        print("Mot de passe: admin123")
        
        admin = Utilisateur.objects.create_superuser(
            email='admin@example.com',
            nom='Admin',
            prenom='Super',
            telephone='123456789',
            password='admin123'
        )
        print(f"Super utilisateur créé: {admin.email}")
    else:
        print("Un administrateur existe déjà.")
    
    print("\n=== BASE DE DONNÉES PRÊTE ===")
    print(f"Fichier: {db_path}")
    print(f"Taille: {os.path.getsize(db_path) / 1024:.2f} KB")
    
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
