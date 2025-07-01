from django.db import models
from django.utils import timezone
from authentication.models import User



class Entreprise(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='entreprise_profile',
        limit_choices_to={'role': 'PME'}
    )
    nom_entreprise = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    logo = models.ImageField(
        upload_to='logos/',
        null=True,
        blank=True,
        verbose_name="Logo de l'entreprise"
    )

    def __str__(self):
        return self.nom_entreprise

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"


class Candidat(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='candidat_profile',
        limit_choices_to={'role': 'Candidat'},
    )
    
    nom_complet = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    cv = models.FileField(
        upload_to='cvs/',
        null=True,
        blank=True,
        verbose_name="CV du candidat",
        help_text="Format PDF recommandé")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom_complet

    class Meta:
        verbose_name = "Candidat"
        verbose_name_plural = "Candidats"


class OffreEmploi(models.Model):
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name='offres'
    )
    titre = models.CharField(max_length=255)
    description = models.TextField()
    date_publication = models.DateTimeField(default=timezone.now)
    est_actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.titre} - {self.entreprise.nom_entreprise}"

    class Meta:
        verbose_name = "Offre d'emploi"
        verbose_name_plural = "Offres d'emploi"
        ordering = ['-date_publication']


class Candidature(models.Model):
    STATUT_CHOICES = [
        ('en attente', 'En attente'),
        ('acceptée', 'Acceptée'),
        ('refusée', 'Refusée'),
    ]

    candidat = models.ForeignKey(
        Candidat,
        on_delete=models.CASCADE,
        related_name='candidatures'
    )
    offre = models.ForeignKey(
        OffreEmploi,
        on_delete=models.CASCADE,
        related_name='candidatures'
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en attente'
    )
    date_soumission = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    score_pertinence = models.FloatField(
        null=True,
        blank=True,
        help_text="Score de pertinence du CV par rapport à l'offre (0 à 100)"
    )

    
    def __str__(self):
        return f"{self.candidat.nom_complet} - {self.offre.titre}"

    class Meta:
        verbose_name = "Candidature"
        verbose_name_plural = "Candidatures"
        unique_together = ('candidat', 'offre')  # Un candidat ne peut postuler qu'une fois par offre
        ordering = ['-date_soumission']


class AvisEmploye(models.Model):
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name='avis_employes'
    )
    avis = models.TextField()
    date_publication = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Avis sur {self.entreprise.nom_entreprise}"

    class Meta:
        verbose_name = "Avis employé"
        verbose_name_plural = "Avis employés"
        ordering = ['-date_publication']


class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages_envoyes'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages_recus'
    )
    candidature = models.ForeignKey(
        Candidature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages'
    )
    contenu = models.TextField()
    date_envoi = models.DateTimeField(default=timezone.now)
    est_lu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"De {self.sender.email} à {self.receiver.email}"

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['-date_envoi']