from django.shortcuts import render, get_object_or_404

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from .models import Entreprise, OffreEmploi, Candidature, Candidat
from .serializers import EntrepriseSerializer, OffreEmploiSerializer, CandidatureSerializer
from authentication.models import User
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins

class EntrepriseViewSet(viewsets.ModelViewSet):
    
    serializer_class = EntrepriseSerializer
    authentication_classes = [JWTAuthentication]  # Ajout spécifique JWT
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']  # Autoriser seulement GET, PUT, PATCH

    def get_queryset(self):
        # Ne retourne que l'entreprise de l'utilisateur connecté
        if self.request.user.is_authenticated and self.request.user.role == 'PME':
            return Entreprise.objects.filter(user=self.request.user)
        return Entreprise.objects.none() # Aucun résultat si pas authentifié ou pas PME

    def perform_create(self, serializer):
        # Associe automatiquement l'utilisateur connecté
        if self.request.user.is_authenticated and self.request.user.role == 'PME':
             serializer.save(user=self.request.user)
        else:
             # Gérer l'erreur si un non-PME tente de créer un profil entreprise
             raise permissions.PermissionDenied("Seuls les utilisateurs PME peuvent créer un profil entreprise.")

    def create(self, request, *args, **kwargs):
        # Empêche la création si l'utilisateur a déjà un profil entreprise
        if self.request.user.is_authenticated and self.request.user.role == 'PME':
            if Entreprise.objects.filter(user=request.user).exists():
                return Response(
                    {"detail": "Vous avez déjà un profil entreprise."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Si l'utilisateur est PME et n'a pas de profil, on appelle la méthode create du mixin
            return super().create(request, *args, **kwargs)
        else:
             # Si l'utilisateur n'est pas authentifié ou pas PME, refuser la création
             raise permissions.PermissionDenied("Seuls les utilisateurs PME authentifiés peuvent créer un profil entreprise.")


class OffreEmploiViewSet(viewsets.ModelViewSet):
    queryset = OffreEmploi.objects.all() # Queryset de base
    serializer_class = OffreEmploiSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated] # S'assurer que l'utilisateur est authentifié

    def get_queryset(self):
        # Afficher seulement les offres de l'entreprise de l'utilisateur connecté
        # S'assurer que l'utilisateur est une PME et a un profil entreprise
        user = self.request.user
        if user.is_authenticated and user.role == 'PME':
            try:
                entreprise = Entreprise.objects.get(user=user)
                return OffreEmploi.objects.filter(entreprise=entreprise).order_by('-date_publication')
            except Entreprise.DoesNotExist:
                # Si l'utilisateur PME n'a pas encore de profil entreprise, il n'a pas d'offres
                return OffreEmploi.objects.none()
        return OffreEmploi.objects.none() # Aucun résultat si pas authentifié ou pas PME

    def perform_create(self, serializer):
        # Associer automatiquement la nouvelle offre à l'entreprise de l'utilisateur connecté
        user = self.request.user
        if user.is_authenticated and user.role == 'PME':
            try:
                entreprise = Entreprise.objects.get(user=user)
                serializer.save(entreprise=entreprise)
            except Entreprise.DoesNotExist:
                 # Ne devrait pas arriver si la permission est bien gérée, mais sécurité
                 raise permissions.PermissionDenied("Vous devez avoir un profil entreprise pour créer une offre.")
        else:
             raise permissions.PermissionDenied("Seuls les utilisateurs PME authentifiés peuvent créer une offre.")

    # Les méthodes create, retrieve, update, partial_update, destroy par défaut du ModelViewSet
    # fonctionneront en s'appuyant sur get_queryset et perform_create/perform_update (si besoin).
    # La permission IsAuthenticated s'assure que seul un utilisateur connecté peut faire ces actions.
    # Le filtrage dans get_queryset et l'association dans perform_create/update garantissent
    # qu'ils ne gèrent que leurs propres offres.
    
# Permission personnalisée pour vérifier si l'utilisateur est une PME et possède l'offre
class IsPMEAndOfferOwner(permissions.BasePermission):
    """
    Autorise l'accès seulement si l'utilisateur est authentifié, est une PME,
    et que l'offre associée à la candidature appartient à son entreprise.
    """
    def has_permission(self, request, view):
        # Vérifie si l'utilisateur est authentifié et est une PME
        return request.user and request.user.is_authenticated and request.user.role == 'PME'

    def has_object_permission(self, request, view, obj):
        # Vérifie si l'offre liée à la candidature appartient à l'entreprise de l'utilisateur
        user = request.user
        if user.is_authenticated and user.role == 'PME':
            try:
                entreprise = Entreprise.objects.get(user=user)
                # obj est l'instance de Candidature
                return obj.offre.entreprise == entreprise
            except Entreprise.DoesNotExist:
                return False
        return False


# Vue pour lister les candidatures d'une offre spécifique (pour le propriétaire PME de l'offre)
class CandidatureListByOffreView(ListAPIView):
    serializer_class = CandidatureSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsPMEAndOfferOwner] # Utilise notre permission personnalisée

    def get_queryset(self):
        # Récupère l'ID de l'offre depuis les paramètres d'URL
        offre_id = self.kwargs['offre_id']
        # Récupère l'offre, en s'assurant qu'elle appartient bien à l'entreprise de l'utilisateur connecté
        user = self.request.user
        if user.is_authenticated and user.role == 'PME':
            try:
                entreprise = Entreprise.objects.get(user=user)
                offre = get_object_or_404(OffreEmploi, id=offre_id, entreprise=entreprise)
                # Retourne les candidatures pour cette offre spécifique
                return Candidature.objects.filter(offre=offre).select_related('candidat__user', 'offre') # select_related pour optimiser
            except Entreprise.DoesNotExist:
                # Si l'utilisateur PME n'a pas de profil entreprise, ou si l'offre n'appartient pas
                raise permissions.PermissionDenied("Vous n'avez pas la permission d'accéder à ces candidatures.")
        # Si l'utilisateur n'est pas authentifié ou pas PME
        raise permissions.PermissionDenied("Authentification requise et rôle PME.")


# Vue pour récupérer les détails et mettre à jour le statut d'une candidature spécifique
# On utilise RetrieveModelMixin et UpdateModelMixin
class CandidatureDetailUpdateStatusView(RetrieveAPIView, UpdateAPIView):
    queryset = Candidature.objects.all() # Queryset de base (sera filtré par has_object_permission)
    serializer_class = CandidatureSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsPMEAndOfferOwner] # Utilise notre permission personnalisée
    lookup_field = 'pk' # Utilise l'ID de la candidature pour la recherche (par défaut)

    # On ne permet de mettre à jour que le champ 'statut' via cette vue
    def update(self, request, *args, **kwargs):
        # Récupère l'instance de la candidature
        instance = self.get_object()
        # Crée le serializer avec les données de la requête et l'instance
        # partial=True permet la mise à jour partielle (seulement le statut)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Vérifie que seul le champ 'statut' est en train d'être modifié (optionnel mais bonne pratique)
        if 'statut' in serializer.validated_data and len(serializer.validated_data) == 1:
             self.perform_update(serializer)
             return Response(serializer.data)
        else:
             # Refuser la requête si d'autres champs sont envoyés
             return Response(
                 {"detail": "Seul le statut de la candidature peut être mis à jour."},
                 status=status.HTTP_400_BAD_REQUEST
             )

    # La méthode retrieve (GET) est héritée de RetrieveAPIView
    # La méthode partial_update (PATCH) est héritée de UpdateAPIView
    # La méthode perform_update est héritée et sauvegardera le serializer
