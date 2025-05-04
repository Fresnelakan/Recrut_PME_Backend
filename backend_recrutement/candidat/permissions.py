# candidat/permissions.py
from rest_framework import permissions

class IsCandidat(permissions.BasePermission):
    """
    Autorise l'accès seulement si l'utilisateur est authentifié et est un Candidat.
    """
    def has_permission(self, request, view):
        # Vérifie si l'utilisateur est authentifié et a le rôle 'Candidat'
        return request.user and request.user.is_authenticated and request.user.role == 'Candidat'

    # has_object_permission n'est pas strictement nécessaire ici mais peut être ajouté
    # si tu veux vérifier la permission au niveau de l'objet dans certaines vues
    # (comme CandidatureCandidateDetailView, où nous l'avons géré dans get_object).
    # def has_object_permission(self, request, view, obj):
    #     # Exemple : vérifier si l'objet (ex: Candidature) appartient bien au candidat
    #     # Cette logique dépendra de l'objet en question (obj)
    #     # return obj.candidat.user == request.user # Exemple pour une Candidature
    #     return True # Par défaut, permission au niveau objet autorisée si has_permission est vrai