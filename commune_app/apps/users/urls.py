from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import UtilisateurViewSet, CitoyenViewSet, AgentViewSet

router = DefaultRouter()
router.register(r'utilisateurs', UtilisateurViewSet, basename='utilisateurs')
router.register(r'citoyens', CitoyenViewSet, basename='citoyens')
router.register(r'agents', AgentViewSet, basename='agents')

urlpatterns = [
    path('', include(router.urls)),
    # JWT Token endpoints (alternatifs aux endpoints custom)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
