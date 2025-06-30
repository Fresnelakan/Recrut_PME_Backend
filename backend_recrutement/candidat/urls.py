# candidat/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CandidatureListCreateView
# Importe le ViewSet que nous venons de créer
from .views import (
    CandidatProfileViewSet,
    CandidatureListCreateView,
    OffreEmploiListView,
    OffreEmploiDetailView,
    CandidatureCandidateDetailView,
)

router = DefaultRouter()
# Enregistre le ViewSet pour le profil candidat
# 'profil/candidat' est le préfixe d'URL pour ce ViewSet
router.register(r'profil/candidat', CandidatProfileViewSet, basename='candidatprofile')

urlpatterns = [
    # Inclut les URLs générées par le router pour le profil candidat
    path('', include(router.urls)),

    # --- Nouvelles URLs pour les Offres d'Emploi (pour les candidats) ---
    # /api/candidat/offres/
    path(
        'offres/',
        OffreEmploiListView.as_view(),
        name='candidat-offresemploi-list'
    ),
    # /api/candidat/offres/{offre_id}/
    path(
        'offres/<int:pk>/', # Utilise 'pk' pour correspondre au lookup_field par défaut de RetrieveAPIView
        OffreEmploiDetailView.as_view(),
        name='candidat-offresemploi-detail'
    ),

    # --- Nouvelles URLs pour lister et voir les Candidatures d'un candidat ---
     path(
        'applications/',
        CandidatureListCreateView.as_view(),
        name='candidat-applications'
    ),


    # /api/candidat/applications/{candidature_id}/ (GET seulement)
    path(
        'applications/<int:pk>/', # Utilise 'pk' pour correspondre au lookup_field
        CandidatureCandidateDetailView.as_view(),
        name='candidat-application-detail'
    ),
    #path('api/candidat/mon-cv/', MonCVView.as_view(), name='mon_cv'),
]