from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin

# Manager pour créer l'utilisateur proprement
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role='Candidat', **extra_fields):
        if not email:
            raise ValueError('L\'adresse email est obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)  # Django va hasher le mot de passe automatiquement
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('role', 'PME')
        return self.create_user(email, password, **extra_fields)

# Ton modèle utilisateur
class User(AbstractBaseUser,PermissionsMixin):
    ROLE_CHOICES = (
        ('PME', 'PME'),
        ('Candidat', 'Candidat'),
    )

    email = models.EmailField(unique=True, max_length=191)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    objects = UserManager()

    def __str__(self):
        return self.email
