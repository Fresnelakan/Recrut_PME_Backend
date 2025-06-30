from datetime import timezone
from django.utils.timezone import now, localtime
from django.shortcuts import render, get_object_or_404

from rest_framework import exceptions
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser # Nécessaire pour gérer l'upload de fichiers

from rest_framework.views import APIView # Import de APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, ListCreateAPIView # Import de vues génériques
from rest_framework import mixins # Import des mixins
# Importe le modèle Candidat depuis l'application pme
from pme.models import Candidat, OffreEmploi, Candidature
# Importe le modèle User (utile pour les vérifications de rôle)
from authentication.models import User
# Importe le serializer pour Candidat
from .serializers import CandidatSerializer, OffreEmploiCandidateSerializer, CandidatureCandidateSerializer, CandidatureCreateSerializer
from .permissions import IsCandidat
# Importe les classes d'authentification et de permission JWT/DRF
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated


# Permission personnalisée pour vérifier si l'utilisateur est un Candidat
class IsCandidat(permissions.BasePermission):
    """
    Autorise l'accès seulement si l'utilisateur est authentifié et est un Candidat.
    """
    def has_permission(self, request, view):
        # Vérifie si l'utilisateur est authentifié et a le rôle 'Candidat'
        return request.user and request.user.is_authenticated and request.user.role == 'Candidat'

    # has_object_permission n'est pas strictement nécessaire ici car get_queryset filtre
    # pour ne voir que le profil de l'utilisateur connecté, mais peut être ajouté pour plus de sécurité.
    # def has_object_permission(self, request, view, obj):
    #     # obj est l'instance de Candidat
    #     return obj.user == request.user


# ViewSet pour gérer le profil Candidat (API pour les candidats eux-mêmes)
class CandidatProfileViewSet(viewsets.ModelViewSet):
    serializer_class = CandidatSerializer
    authentication_classes = [JWTAuthentication] # Utilise l'authentification JWT
    permission_classes = [IsAuthenticated, IsCandidat] # L'utilisateur doit être authentifié ET un Candidat

    # Parser pour gérer les données de formulaire et les fichiers uploadés
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Ne retourne QUE le profil Candidat de l'utilisateur connecté
        user = self.request.user
        if user.is_authenticated and user.role == 'Candidat':
            # Le profil Candidat a le même PK que l'utilisateur
            return Candidat.objects.filter(user=user)
        return Candidat.objects.none() # Aucun résultat si pas authentifié ou pas Candidat

    def perform_create(self, serializer):
        # Associe automatiquement le profil Candidat à l'utilisateur connecté
        user = self.request.user
        if user.is_authenticated and user.role == 'Candidat':
            # Assure-toi que l'utilisateur n'a pas déjà de profil Candidat
            if Candidat.objects.filter(user=user).exists():
                 raise permissions.PermissionDenied("Vous avez déjà un profil candidat.")

            # Sauvegarde le serializer, associant l'utilisateur
            # Gère l'upload de fichier si un fichier est inclus dans la requête
            serializer.save(user=user)
        else:
             raise permissions.PermissionDenied("Seuls les utilisateurs Candidat authentifiés peuvent créer un profil.")

    # Les méthodes list, retrieve, update, partial_update, destroy du ModelViewSet
    # fonctionneront en s'appuyant sur get_queryset et perform_create/perform_update.
    # Le filtrage dans get_queryset et l'association dans perform_create garantissent
    # qu'un candidat ne gère que son propre profil.
    # La gestion de l'upload du fichier CV sera automatique grâce à ModelSerializer
    # et MultiPartParser si le champ cv_path est un FileField/ImageField et est inclus
    # dans les données de la requête.

    # Tu peux personnaliser d'autres méthodes si nécessaire (ex: perform_update pour gérer l'upload lors de la mise à jour)
# --- Nouvelles Vues pour les Offres d'Emploi (pour les candidats) ---

# Vue pour lister toutes les offres d'emploi actives (accessibles aux candidats authentifiés)
class OffreEmploiListView(ListAPIView):
    # Utilise le serializer pour candidats pour l'affichage des offres
    serializer_class = OffreEmploiCandidateSerializer
    authentication_classes = [JWTAuthentication]
    # Autoriser seulement les utilisateurs authentifiés à voir la liste (ou IsAuthenticated | IsCandidat si tu veux filtrer par rôle)
    permission_classes = [IsAuthenticated] # Ou [IsAuthenticated, IsCandidat] si seulement les candidats voient cette liste

    def get_queryset(self):
        # Retourne toutes les offres d'emploi qui sont actives
        return OffreEmploi.objects.filter(est_actif=True).order_by('-date_publication').select_related('entreprise') # select_related pour optimiser

# Vue pour voir les détails d'une offre d'emploi spécifique (accessibles aux candidats authentifiés)
class OffreEmploiDetailView(RetrieveAPIView):
    # Utilise le serializer pour candidats pour l'affichage des offres
    serializer_class = OffreEmploiCandidateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated] # Ou [IsAuthenticated, IsCandidat]
    queryset = OffreEmploi.objects.filter(est_actif=True) # Ne permet de voir que les offres actives
    lookup_field = 'pk' # Cherche par l'ID de l'offre (par défaut)

# --- Nouvelle Vue pour soumettre une Candidature ---

# Vue pour créer une nouvelle candidature (pour les candidats authentifiés)
class CandidatureListCreateView(ListCreateAPIView):
    """
    Vue combinée pour:
    - Lister les candidatures d'un candidat (GET)
    - Créer une nouvelle candidature (POST)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsCandidat]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CandidatureCreateSerializer
        return CandidatureCandidateSerializer

    def get_queryset(self):
        """Retourne seulement les candidatures de l'utilisateur Candidat connecté"""
        user = self.request.user
        offre_id = self.request.query_params.get('offre', None)
        
        try:
            candidat_profile = Candidat.objects.get(user=user)
            queryset = Candidature.objects.filter(candidat=candidat_profile)
            
            # Filtre supplémentaire si un ID d'offre est spécifié
            if offre_id:
                queryset = queryset.filter(offre_id=offre_id)
                
            return queryset.order_by('-date_soumission').select_related('offre__entreprise')
        except Candidat.DoesNotExist:
            return Candidature.objects.none()

    def perform_create(self, serializer):
        """Gère la création d'une candidature avec les bonnes associations"""
        user = self.request.user
        offre_id = serializer.validated_data['offre'].id
        
        # Vérifie si une candidature existe déjà pour cette offre
        if Candidature.objects.filter(
            candidat__user=user,
            offre_id=offre_id
        ).exists():
            raise exceptions.ValidationError(
                "Vous avez déjà postulé à cette offre."
            )

        try:
            candidat_profile = Candidat.objects.get(user=user)
            serializer.save(
                candidat=candidat_profile,
                statut='en attente',
                date_soumission=localtime()
            )
        except Candidat.DoesNotExist:
            raise exceptions.PermissionDenied(
                "Vous devez avoir un profil candidat pour postuler à une offre."
            )
# Vue pour voir le détail d'une candidature spécifique du point de vue du candidat
class CandidatureCandidateDetailView(RetrieveAPIView):
    queryset = Candidature.objects.all() # Queryset de base (sera filtré par la permission)
    serializer_class = CandidatureCandidateSerializer
    authentication_classes = [JWTAuthentication]
    # Utilise la permission IsPMEAndOfferOwner pour s'assurer que le candidat voit sa propre candidature ?
    # Non, il faut une permission qui vérifie que la candidature appartient au candidat connecté.
    # Créons une nouvelle permission ou ajustons IsCandidat.
    # Simplifions : le get_queryset de la vue ListAPIView pour les candidats assure déjà le filtrage par candidat.
    # Pour Retrieve, on peut surcharger get_queryset ou get_object.
    # Utilisons une permission simple : vérifier que l'utilisateur est candidat, et que la candidature lui appartient.
    permission_classes = [IsAuthenticated, IsCandidat] # On utilisera has_object_permission si on le surcharge

    # Alternativement, on peut surcharger get_object pour s'assurer que seul le candidat propriétaire accède
    def get_object(self):
        queryset = self.get_queryset() # Utilise le queryset de base (toutes les candidatures)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}

        # Récupère l'objet Candidature par son ID
        obj = get_object_or_404(queryset, **filter_kwargs)

        # Vérifie que l'objet appartient bien au candidat authentifié
        user = self.request.user
        if user.is_authenticated and user.role == 'Candidat':
            try:
                candidat_profile = Candidat.objects.get(user=user)
                if obj.candidat != candidat_profile:
                    raise permissions.PermissionDenied("Vous n'avez pas la permission d'accéder à cette candidature.")
            except Candidat.DoesNotExist:
                 raise permissions.PermissionDenied("Vous devez avoir un profil candidat pour accéder à cette candidature.")
        else:
             raise permissions.PermissionDenied("Authentification requise et rôle Candidat.")

        # S'assure que la permission a été vérifiée (même si get_object le fait déjà implicitement via has_object_permission si définie)
        self.check_object_permissions(self.request, obj)
        return obj

    # Ici, pas besoin de perform_create ou update car c'est une vue de lecture/détail.
