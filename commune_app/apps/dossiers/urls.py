from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DemandeViewSet, TraitementViewSet, PropositionRDVViewSet, RendezVousViewSet

router = DefaultRouter()
router.register(r'demandes', DemandeViewSet, basename='demandes')
router.register(r'traitements', TraitementViewSet, basename='traitements')
router.register(r'propositions-rdv', PropositionRDVViewSet, basename='propositions-rdv')
router.register(r'rendez-vous', RendezVousViewSet, basename='rendez-vous')

urlpatterns = [
    path('', include(router.urls)),
]
