from django.db import models
from django.conf import settings

from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser,User
from django.core.validators import URLValidator
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator
from django.core.validators import FileExtensionValidator

import os
from django.core.exceptions import ValidationError
from django.utils import timezone
import os
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('dashboard', 'Tableau de bord'),
        ('publication', 'Publication scientifique'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='publication')

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True
    )


def get_current_year():
    """Fonction utilitaire pour obtenir l'année courante"""
    return timezone.now().year


def validate_file_size(value):
    """Validation de la taille des fichiers (max 5MB)"""
    max_size = 5 * 1024 * 1024  # 5MB
    if value.size > max_size:
        raise ValidationError(
            f"La taille maximale autorisée est {max_size / 1024 / 1024}MB"
        )


def generate_document_path(instance, filename, document_type):
    """Génère un chemin unique pour les documents"""
    ext = os.path.splitext(filename)[1]
    filename = f"{instance.nom}_{instance.prenom}_{document_type}{ext}"
    return os.path.join("documents", document_type, filename)


def photo_path(instance, filename):
    """Chemin pour les photos d'identité"""
    return generate_document_path(instance, filename, "photo")


def bac_path(instance, filename):
    """Chemin pour les scans du bac"""
    return generate_document_path(instance, filename, "bac")


def diplome_path(instance, filename):
    """Chemin pour les diplômes de licence"""
    return generate_document_path(instance, filename, "diplome")


def extrait_path(instance, filename):
    """Chemin pour les extraits de naissance"""
    return generate_document_path(instance, filename, "extrait")


class Inscription(models.Model):
    SEXE_CHOICES = [
        ("M", "Masculin"),
        ("F", "Féminin"),
    ]

    SERIE_BAC_CHOICES = [
        ("A", "Série A"),
        ("C", "Série C"),
        ("D", "Série D"),
        ("E", "Série E"),
        ("F", "Série F"),
        ("G", "Série G"),
    ]

    MENTION_CHOICES = [
        ("TB", "Très Bien"),
        ("B", "Bien"),
        ("AB", "Assez Bien"),
        ("P", "Passable"),
    ]

    VALIDATION_CHOICES = [
        ("E", "En attente"),
        ("V", "Validé"),
        ("R", "Rejeté"),
    ]

    # Informations personnelles
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Référence correcte au modèle User
        on_delete=models.CASCADE,  # Supprime l'inscription si l'utilisateur est supprimé
        verbose_name="Utilisateur",
        related_name='inscription'  # Permet d'accéder à l'inscription via user.inscription
    )
    nom = models.CharField(max_length=100, verbose_name="Nom de famille")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    date_naissance = models.DateField(verbose_name="Date de naissance")
    lieu_naissance = models.CharField(max_length=100, verbose_name="Lieu de naissance")

    # Coordonnées
    email = models.EmailField(unique=True, verbose_name="Adresse email")
    email_confirmation = models.EmailField(verbose_name="Confirmation email")
    telephone = models.CharField(max_length=20, verbose_name="Numéro de téléphone")

    # Identifiants
    cmu = models.CharField(max_length=50, verbose_name="Numéro CMU", unique=True)
    cni = models.CharField(max_length=50, verbose_name="Numéro CNI", unique=True)
   

    # Baccalauréat
    serie_bac = models.CharField(
        max_length=1,
        choices=SERIE_BAC_CHOICES,
        default="A",
        verbose_name="Série du baccalauréat",
    )
    annee_obtentionbac = models.IntegerField(
        verbose_name="Année d'obtention du bac",
        validators=[
            MinValueValidator(1950),
            MaxValueValidator(get_current_year),
        ],
    )
    mention_bac = models.CharField(
        max_length=2, choices=MENTION_CHOICES, verbose_name="Mention au bac"
    )
    numero_bac = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro du bac"
    )
    ecole_diplomebac = models.CharField(
        max_length=255, verbose_name="École d'obtention du bac"
    )

    # Licence
    licence = models.CharField(
        max_length=100, default="Inconnu", verbose_name="Type de licence"
    )
    annee_obtentionlicence = models.IntegerField(
        verbose_name="Année d'obtention de la licence",
        validators=[
            MinValueValidator(1950),
            MaxValueValidator(get_current_year),
        ],
    )

    # Documents
    photo_identite = models.ImageField(
        upload_to=photo_path,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        verbose_name="Photo d'identité",
    )
    bac_scan = models.FileField(
        upload_to=bac_path,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        verbose_name="Diplôme du bac",
    )
    diplome_scan = models.FileField(
        upload_to=diplome_path,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        verbose_name="Diplôme de licence",
    )
    extrait_naissance = models.FileField(
        upload_to=extrait_path,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
        verbose_name="Extrait de naissance",
    )

    # Formation
    formation = models.CharField(max_length=100)
    date_inscription = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=1,
        choices=VALIDATION_CHOICES,
        default="E",
        verbose_name="Statut de l'inscription",
    )

    class Meta:
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"
        ordering = ["-date_inscription"]
        constraints = [
            models.UniqueConstraint(
                fields=["nom", "prenom", "date_naissance"], name="unique_candidate"
            ),
        ]

    def __str__(self):
        return f"{self.nom.upper()} {self.prenom} - {self.formation}"

    def clean(self):
        """Validation globale du modèle"""
        # Vérification des emails
        if self.email != self.email_confirmation:
            raise ValidationError(
                {"email_confirmation": "Les adresses email ne correspondent pas"}
            )

        # Vérification chronologie des diplômes
        if self.annee_obtentionlicence < self.annee_obtentionbac:
            raise ValidationError(
                "L'année d'obtention de la licence ne peut pas être antérieure à celle du bac"
            )

    def save(self, *args, **kwargs):
        """Normalisation des données avant sauvegarde"""
        self.nom = self.nom.upper()
        self.prenom = self.prenom.capitalize()
        self.numero_bac = self.numero_bac.upper()
        super().save(*args, **kwargs)


class Partenaire(models.Model):
    CATEGORY_CHOICES = (
        ('academique', 'Académique'),
        ('institutionnel', 'Institutionnel'),
        ('prive', 'Privé'),
    )

    nom = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='partenaires/')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='academique')
    description = models.TextField(blank=True, help_text="Description courte pour le tooltip")
    website = models.URLField(blank=True, validators=[URLValidator()])
    
    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Partenaire"
        verbose_name_plural = "Partenaires"
        ordering = ['category', 'nom']

class Expertise(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Classe Font Awesome ex: fa-globe")

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    class Category(models.TextChoices):
        RESEARCH = 'recherche', _('Recherche')
        TEACHING = 'enseignement', _('Enseignement')
        ADMINISTRATION = 'admin', _('Administration')
    
    # Informations de base
    first_name = models.CharField(
        _('Prénom'), 
        max_length=100,
        validators=[MinLengthValidator(2)]
    )
    last_name = models.CharField(
        _('Nom'), 
        max_length=100,
        validators=[MinLengthValidator(2)]
    )
    slug = models.SlugField(
        _('Slug'), 
        max_length=255, 
        unique=True, 
        blank=True
    )
    
    # Métadonnées
    title = models.CharField(
        _('Titre professionnel'), 
        max_length=150,
        blank=True
    )
    bio = models.TextField(
        _('Biographie'), 
        blank=True,
        help_text=_("Description détaillée du membre")
    )
    
    # Media
    photo = models.ImageField(
        _('Photo'), 
        upload_to='team/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text=_("Format recommandé : 600x600 pixels")
    )
    
    # Catégorisation
    category = models.CharField(
        _('Catégorie'), 
        max_length=20, 
        choices=Category.choices, 
        default=Category.RESEARCH
    )
    expertises = models.ManyToManyField(
        'Expertise',
        verbose_name=_('Expertises'),
        blank=True,
        related_name='team_members'
    )
    
    # Réseaux sociaux
    linkedin_url = models.URLField(
        _('Profil LinkedIn'), 
        blank=True,
        validators=[URLValidator()]
    )
    researchgate_url = models.URLField(
        _('Profil ResearchGate'), 
        blank=True,
        validators=[URLValidator()]
    )
    
    # Ordre d'affichage
    display_order = models.PositiveIntegerField(
        _("Ordre d'affichage"), 
        default=0
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Membre d'équipe")
        verbose_name_plural = _("Membres d'équipe")
        ordering = ['display_order', 'last_name', 'first_name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.get_category_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.first_name}-{self.last_name}")
            unique_slug = base_slug
            num = 1
            while TeamMember.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def active_social_links(self):
        return {
            'linkedin': self.linkedin_url if self.linkedin_url else None,
            'researchgate': self.researchgate_url if self.researchgate_url else None
        }

class Activite(models.Model):
    CATEGORIES = [
        ("nature", "Nature et Environnement"),
        ("culture", "Culture et Patrimoine"),
        ("aventure", "Aventure et Exploration"),
        ("education", "Éducation et Recherche"),
        ("loisir", "Loisirs et Détente"),
    ]

    ICONES = {
        "nature": "leaf",
        "culture": "landmark",
        "aventure": "hiking",
        "education": "book-open",
        "loisir": "smile",
    }

    title = models.CharField("Titre", max_length=200)
    short_description = models.TextField("Description courte")
    category = models.CharField("Catégorie", max_length=20, choices=CATEGORIES)
    date = models.DateField("Date prévue", null=True, blank=True)
    image = models.ImageField("Image", upload_to="activites/", null=True, blank=True)

    def __str__(self):
        return self.title

    def get_icon(self):
        return self.ICONES.get(self.category, "circle")

    def get_absolute_url(self):
        # À adapter selon ta config d'URL
        return reverse("activite_detail", args=[str(self.id)])



class PageConfig(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    template = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

class Formation(models.Model):
    nom = models.CharField(max_length=255)
    duree = models.IntegerField(help_text="Durée en heures")
    cout = models.DecimalField(max_digits=10, decimal_places=2)
    ues = models.ManyToManyField('UE', related_name='formations')

    def __str__(self):
        return self.nom

class UE(models.Model):
    nom = models.CharField(max_length=255)
    code = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nom} ({self.code})"

class ECUE(models.Model):
    nom = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    ue = models.ForeignKey(UE, on_delete=models.CASCADE, related_name='ecues')

    def __str__(self):
        return f"{self.nom} ({self.code})"
