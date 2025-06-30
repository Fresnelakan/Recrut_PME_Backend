from rest_framework import serializers
from .models import Entreprise, OffreEmploi, Candidat, Candidature
from authentication.models import User

class EntrepriseSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Entreprise
        fields = ['email', 'nom_entreprise', 'description', 'logo']
        read_only_fields = ['email']
        extra_kwargs = {
            'logo': {'required': False}, 'allow_null': True
        }

    def validate(self, data):
        # Validation personnalisée si nécessaire
        return data

class OffreEmploiSerializer(serializers.ModelSerializer):
    # On pourrait ajouter des champs en lecture seule pour afficher des infos liées,
    # comme le nom de l'entreprise, mais pour l'instant, les champs du modèle suffisent.

    class Meta:
        model = OffreEmploi
        fields = ['id', 'titre', 'description', 'date_publication', 'est_actif', 'created_at', 'updated_at']
        read_only_fields = ['id', 'date_publication', 'created_at', 'updated_at']
        # Note : 'entreprise' n'est pas dans les champs car il sera géré par la vue (automatiquement associé à l'entreprise de l'utilisateur connecté)

class CandidatureSerializer(serializers.ModelSerializer):
    # Champs en lecture seule pour afficher des infos sur l'offre et le candidat
    offre_titre = serializers.CharField(source='offre.titre', read_only=True)
    candidat_nom_complet = serializers.CharField(source='candidat.nom_complet', read_only=True)
    # On peut aussi ajouter l'email du candidat via la relation Candidat -> User
    candidat_email = serializers.EmailField(source='candidat.user.email', read_only=True)
    cv_url = serializers.SerializerMethodField()

    class Meta:
        model = Candidature
        # Champs que l'on veut exposer
        fields = [
            'id',
            'offre', # On inclut l'offre_id en écriture si besoin (pour créer), mais ici ce sera surtout lu
            'candidat', # On inclut le candidat_id si besoin, mais ici ce sera surtout lu
            'statut',
            'date_soumission',
            'offre_titre', # Champ en lecture seule ajouté
            'candidat_nom_complet', # Champ en lecture seule ajouté
            'candidat_email', # Champ en lecture seule ajouté
            'cv_url',
            'created_at',
            'updated_at'
        ]
        # Champs qui ne peuvent pas être modifiés via le serializer (sauf le statut peut-être)
        read_only_fields = [
            'id',
            'offre', # L'offre ne change pas une fois la candidature créée
            'candidat', # Le candidat ne change pas
            'date_soumission',
            'offre_titre',
            'candidat_nom_complet',
            'candidat_email',
            'cv_url',
            'created_at',
            'updated_at'
        ]

    def get_cv_url(self, obj):
        if obj.candidat.cv:
            return f"http://127.0.0.1:8001{obj.candidat.cv.url}"
        return None


