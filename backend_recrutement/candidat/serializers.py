# candidat/serializers.py
from rest_framework import serializers
# Importe le modèle Candidat depuis l'application pme
from pme.models import Candidat, OffreEmploi, Candidature, Entreprise
# Importe le modèle User si tu en as besoin (par exemple, pour afficher l'email)
from authentication.models import User

class CandidatSerializer(serializers.ModelSerializer):
    # Champ en lecture seule pour afficher l'email de l'utilisateur lié
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Candidat
        # 'id' n'est pas inclus car 'user' est la clé primaire
        # 'cv_path' sera inclus car c'est un champ modifiable, mais géré spécifiquement pour l'upload
        fields = ['email', 'nom_complet', 'description', 'cv']
        # L'email est en lecture seule car géré par le compte utilisateur
        read_only_fields = ['email']

    # Note : Pour la gestion de l'upload du fichier dans le champ FileField/ImageField
    # DRF gère automatiquement l'upload si le serializer est utilisé dans un ViewSet/une vue
    # qui traite les données de type 'multipart/form-data'.


    # Tu peux ajouter des validations personnalisées ici si nécessaire
    # def validate_nom_complet(self, value):
    #     if len(value) < 2:
    #         raise serializers.ValidationError("Le nom complet doit contenir au moins 2 caractères.")
    #     return value

    # def validate(self, data):
    #     # Validation au niveau de l'objet
    #     return data
    
class OffreEmploiCandidateSerializer(serializers.ModelSerializer):
    # Champ en lecture seule pour afficher le nom de l'entreprise liée à l'offre
    entreprise_nom = serializers.CharField(source='entreprise.nom_entreprise', read_only=True)

    class Meta:
        model = OffreEmploi
        # Liste des champs que le candidat verra pour une offre
        fields = ['id', 'titre', 'description', 'date_publication', 'est_actif', 'entreprise_nom']
        read_only_fields = ['id', 'date_publication', 'est_actif', 'entreprise_nom']


# --- Serializer pour afficher les Candidatures d'un candidat ---
class CandidatureCandidateSerializer(serializers.ModelSerializer):
    # Informations sur l'offre liée (en lecture seule)
    offre_titre = serializers.CharField(source='offre.titre', read_only=True)
    offre_entreprise = serializers.CharField(source='offre.entreprise.nom_entreprise', read_only=True)
    offre_id = serializers.IntegerField(source='offre.id', read_only=True)


    class Meta:
        model = Candidature
        # Champs que le candidat verra pour ses candidatures
        fields = [
            'id',
            'statut',
            'date_soumission',
            'offre_titre',
            'offre_entreprise',
            'offre_id', # Utile pour créer un lien vers l'offre
            'created_at',
            'updated_at'
        ]
        # Tous les champs sont en lecture seule pour le candidat sur sa candidature (il ne peut modifier que son profil)
        read_only_fields = [
            'id',
            'statut',
            'date_soumission',
            'offre_titre',
            'offre_entreprise',
            'offre_id',
            'created_at',
            'updated_at'
        ]

# --- Serializer pour soumettre une nouvelle Candidature (pour la création) ---
# Celui-ci est plus simple car il n'a besoin que de l'offre_id (le candidat est implicite)
class CandidatureCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidature
        fields = ['offre'] # Le champ 'offre' (ForeignKey vers OffreEmploi) est requis en entrée
        # 'candidat', 'statut', 'date_soumission' seront gérés par la vue (automatiquement)

    # Tu peux ajouter une validation pour vérifier que l'offre existe et est active si nécessaire
    def validate_offre(self, value):
        try:
            # Vérifie si l'offre existe et est active
            offre = OffreEmploi.objects.get(id=value.id, est_actif=True)
            return offre
        except OffreEmploi.DoesNotExist:
            raise serializers.ValidationError("L'offre d'emploi spécifiée n'existe pas ou n'est plus active.")