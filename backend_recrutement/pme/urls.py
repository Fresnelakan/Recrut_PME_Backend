from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EntrepriseViewSet, OffreEmploiViewSet, CandidatureListByOffreView, CandidatureDetailUpdateStatusView, CandidatureCreateView, ScoreCandidaturesView

router = DefaultRouter()
# Enregistre le ViewSet pour le profil entreprise
router.register(r'profil/entreprise', EntrepriseViewSet, basename='entreprise')
# Enregistre le ViewSet pour les offres d'emploi
router.register(r'offres', OffreEmploiViewSet, basename='offresemploi')

urlpatterns = [
    # Inclut les URLs générées par le router (profils entreprise et offres)
    path('', include(router.urls)),

    # --- Nouvelles URLs pour les Candidatures (côté PME) ---

    # URL pour lister les candidatures pour une offre spécifique (syntaxe imbriquée)
    # /api/pme/offres/{offre_id}/candidatures/
    path(
        'offres/<int:offre_id>/candidatures/',
        CandidatureListByOffreView.as_view(),
        name='offre-candidatures-list'
    ),

    # URL pour voir le détail ou mettre à jour le statut d'une candidature spécifique
    # /api/pme/candidatures/{candidature_id}/
    path(
        'candidatures/<int:pk>/', # Utilise 'pk' car c'est le lookup_field par défaut ou que nous avons défini
        CandidatureDetailUpdateStatusView.as_view(),
        name='candidature-detail-update-status'
    ),
    path('candidat/applications/', CandidatureCreateView.as_view(), name='candidature_create'),
    # Tu pourrais ajouter d'autres URLs si nécessaire (ex: supprimer candidature - bien que la PME puisse le faire via la vue detail/update si tu ajoutes 'delete')

]

urlpatterns += [
    path(
        'offres/<int:offre_id>/score_candidatures/',
        ScoreCandidaturesView.as_view(),
        name='score-candidatures'
    ),
]