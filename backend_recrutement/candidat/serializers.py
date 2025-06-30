# candidat/serializers.py
from rest_framework import serializers
# Importe le modèle Candidat depuis l'application pme
from pme.models import Candidat, OffreEmploi, Candidature, Entreprise
# Importe le modèle User si tu en as besoin (par exemple, pour afficher l'email)
from authentication.models import User

# candidat/serializers.py
from rest_framework import serializers
from pme.models import Candidat # Assurez-vous que Candidat est importé du bon endroit
from django.conf import settings # Important: Importez settings

class CandidatSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    
    # Utiliser SerializerMethodField pour construire manuellement l'URL du CV
    # de manière à ce qu'elle pointe vers le bon serveur/port média.
    cv = serializers.FileField(required=False, allow_null=True) 

    class Meta:
        model = Candidat
        fields = ['email', 'nom_complet', 'description', 'cv']
        read_only_fields = ['email']

    def get_cv(self, obj):
        # Vérifie si un CV existe et a une URL
        if obj.cv and hasattr(obj.cv, 'url'):
            # Construisez l'URL absolue en utilisant le bon port pour les médias.
            # Supposons que vos médias sont servis par le serveur de développement
            # Django sur http://127.0.0.1:8000
            
            # Méthode 1: Construire l'URL à partir de la requête entrante (plus dynamique)
            # Nécessite de passer request dans le context du serializer (voir ci-dessous)
            request = self.context.get('request')
            if request:
                # La méthode build_absolute_uri est la plus propre, mais elle utilisera
                # le domaine et le port de la *requête actuelle*.
                # Si l'API est sur 8001, elle construira une URL avec 8001.
                # Pour forcer 8000, il faut soit modifier l'hôte dans la requête pour la sérialisation,
                # soit construire l'URL manuellement comme dans la Méthode 2.

                # Si votre frontend (la page HTML) est sur http://127.0.0.1:8000
                # et que vous voulez que le lien CV pointe vers 8000:
                # Il faudrait que la request dans le context ait le bon hôte.
                # Une approche plus directe pour ce cas spécifique (API != Media Server)
                # est de hardcoder le domaine/port du serveur média si c'est fixe.

                # Méthode 2: Construire l'URL en spécifiant explicitement le domaine/port du serveur média
                # C'est la solution la plus simple si http://127.0.0.1:8000 est votre serveur de médias.
                return f"http://127.0.0.1:8000{obj.cv.url}"
                
        return None
    
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
    cv_url = serializers.SerializerMethodField()
    def get_cv_url(self, obj):
        if obj.candidat and obj.candidat.cv:
            return f"http://127.0.0.1:8001{obj.candidat.cv.url}"
        return None

    class Meta:
        model = Candidature
        # Champs que le candidat verra pour ses candidatures
        fields = [
            'id',
            'statut',
            'cv_url',
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
            'cv_url',  # URL du CV, en lecture seule
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