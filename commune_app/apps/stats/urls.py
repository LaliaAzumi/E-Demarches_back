from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StatistiqueViewSet, StatistiqueCRUDViewSet

router = DefaultRouter()
router.register(r'crud', StatistiqueCRUDViewSet, basename='stats-crud')

urlpatterns = [
    path('', include(router.urls)),
    path('globale/', StatistiqueViewSet.as_view({'get': 'globale'}), name='stats-globale'),
    path('demandes-temps/', StatistiqueViewSet.as_view({'get': 'demandes_temps'}), name='stats-demandes-temps'),
    path('activite-recente/', StatistiqueViewSet.as_view({'get': 'activite_recente'}), name='stats-activite-recente'),
]
