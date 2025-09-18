from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)

from rest_framework.generics import RetrieveAPIView
from .models import TeamMember
from .serializers import TeamMemberSerializer
from django.urls import reverse_lazy
from django.contrib.auth.hashers import make_password
from datetime import datetime
from django.db.models import Prefetch
from django.http import Http404
from .models import Formation, UE, Activite, Inscription, MarquettePedagogique, ProgrammeFormation
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
from django.template.loader import get_template
from django.conf import settings



from io import BytesIO
import re
import json

# Packages tiers
from xhtml2pdf import pisa
from rest_framework.views import APIView
from rest_framework.response import Response

# Locaux
from .models import TeamMember, Partenaire
from .forms import InscriptionForm, CandidatProfileForm
from .utils import send_inscription_email
from .serializers import TeamMemberSerializer
from functools import wraps


# 2. CONSTANTES
CustomUser = get_user_model()

PAGE_CONFIG = {
    "formation": {
        "title": "Nos Formations",
        "template": "formations/formation.html",
        "context_func": lambda request: {
            "formations": Formation.objects.prefetch_related(
                Prefetch("ues", queryset=UE.objects.prefetch_related("ecues"))
            ).all()
        },
    },
    "contact": {
        "title": "Contact",
        "template": "acceuil/contact.html"
    },
    "activite": {
        "title": "Activité",
        "template": "acceuil/activite.html",
        "context_func": lambda request: {
            "activities": Activite.objects.all().order_by('-date')
        },
    },
    "presentation": {
        "title": "Présentation",
        "template": "acceuil/presentation.html",
        "context_func": lambda request: {
            "inscription": (
                Inscription.objects.filter(email=request.user.email).first()
                if request.user.is_authenticated else None
            ),
            "year": datetime.now().year,
        },
    },
    "travaux": {
        "title": "Travaux",
        "template": "acceuil/travaux.html"
    },
    "inscription": {
        "title": "Inscription",
        "template": "formations/inscription.html"
    },
}

def page_view(request, page_name):
    config = PAGE_CONFIG.get(page_name)
    if not config:
        raise Http404("Page introuvable")

    context = {"title": config.get("title", page_name)}

    if "context_func" in config:
        context.update(config["context_func"](request))

    return render(request, config["template"], context)



# 3. DÉCORATEURS PERSONNALISÉS
def role_required(role_name):
    """Décorateur pour restreindre l'accès par rôle."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if request.user.role != role_name:
                return HttpResponseForbidden()
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator




# 4. VUES PUBLIQUES
def home(request):
    """Vue pour la page d'accueil."""
    partenaires = {
        "academiques": Partenaire.objects.filter(category="academique"),
        "institutionnels": Partenaire.objects.filter(category="institutionnel"),
        "prives": Partenaire.objects.filter(category="prive"),
    }
    
    context = {
        "images_and_slogans": [
            ("cascade.jpg", "Découvrez la beauté de la nature"),
            ("baselique.jpg", "L'architecture au cœur de l'histoire"),
            ("man.jpg", "L'esprit humain, une aventure infinie"),
            ("pt.jpg", "Un regard sur les horizons lointains"),
            ("tourisme.jpg", "Explorez le monde, vivez l'expérience"),
        ],
        "team_members": TeamMember.objects.all(),
        "partenaires": Partenaire.objects.all(),
    }
    return render(request, "acceuil/accueil.html", context)
# 4. VUES PUBLIQUES
def activite(request):
    """Liste des activités avec affichage par date décroissante."""
    activities = Activite.objects.all().order_by("-created_at")
    
    return render(request, "acceuil/activite.html", {
        "title": "Activités",
        "activities": activities
    })
    
    
# 5. VUES D'AUTHENTIFICATION
class GenericLoginView(LoginView):
    """Vue de connexion générique avec redirection par rôle."""
    template_name = "acceuil/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.role == "dashboard":
            return reverse("dashboard")
        if user.role == "publication":
            return reverse("gestion_publications")
        return super().get_success_url()

def admin_login_page(request):
    """Connexion spécifique pour les administrateurs."""
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )
        if user is not None and user.is_staff:
            login(request, user)
            return redirect(request.POST.get("next", "dashboard"))
        return redirect(f"{reverse('home')}?admin_login_error=true")
    

def custom_logout_view(request):
    """Déconnexion générique."""
    logout(request)
    return redirect("home")

def candidat_logout(request):
    """Déconnexion spécifique candidat."""
    logout(request)
    return redirect("home")

def admin_logout(request):
    """Déconnexion spécifique admin."""
    logout(request)
    return redirect("home")




# Vérification si l'utilisateur est bien un candidat
def is_candidat(user):
    """Vérifie si l'utilisateur est un candidat (authentifié et non staff)"""
    return user.is_authenticated and not user.is_staff


# --- Page de connexion candidat ---
def candidat_login_page(request):
    # Rediriger les utilisateurs déjà authentifiés
    if request.user.is_authenticated and is_candidat(request.user):
        return redirect("espace_candidat")
    
    if request.method == 'POST':
        email = request.POST.get('email')  # Champ correspondant à l'email
        password = request.POST.get('password')
        
    
        try:
            # Si vous avez un champ email dans votre modèle User
            user_model = get_user_model()
            user = user_model.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except Exception:
            user = None
        
        if user is not None:
            if is_candidat(user):
                login(request, user)
                next_url = request.GET.get('next', 'espace_candidat')
                return redirect(next_url)
            else:
                messages.error(request, "Accès réservé aux candidats")
        else:
            # Message d'erreur générique pour éviter de divulguer des informations
            messages.error(request, "Identifiants incorrects ou compte inexistant")
    
    return render(request, 'candidat/candidat_login.html')


# --- Espace candidat ---
@login_required(login_url='candidat_login_page')  
@user_passes_test(is_candidat, login_url='candidat_login_page')
def espace_candidat(request):
    """Espace personnel du candidat."""
    try:
        # Utilisation de l'email de l'utilisateur connecté
        inscription = Inscription.objects.get(email=request.user.email)
        formation = Formation.objects.filter(nom=inscription.formation).first()

        # Calcul du pourcentage de complétion du dossier
        documents = {
            'photo': bool(inscription.photo_identite),
            'bac': bool(inscription.bac_scan),
            'diplome': bool(inscription.diplome_scan),
            'extrait': bool(inscription.extrait_naissance),
        }
        completion = sum(documents.values()) / len(documents) * 100 if documents else 0

        context = {
            'inscription': inscription,
            'formation': formation,
            'documents': documents,
            'completion': completion,
            'user': request.user
        }
        return render(request, 'candidat/espace_candidat.html', context)

    except Inscription.DoesNotExist:
        # Loguer l'erreur pour debugging mais afficher un message générique à l'utilisateur
        if settings.DEBUG:
            messages.error(request, f"Aucune inscription trouvée pour l'email: {request.user.email}")
        else:
            messages.error(request, "Aucune inscription trouvée pour votre compte. Contactez l'administration.")
        return redirect('home')
    except Exception as e:
        # Gestion générique des autres erreurs
        if settings.DEBUG:
            messages.error(request, f"Une erreur s'est produite: {str(e)}")
        else:
            messages.error(request, "Une erreur s'est produite lors du chargement de votre espace.")
        return redirect('home')
    
@login_required
def modifier_profil(request):
    """Modification du profil candidat."""
    try:
        inscription = Inscription.objects.get(email=request.user.email)
        
        if request.method == 'POST':
            form = CandidatProfileForm(request.POST, instance=inscription)
            if form.is_valid():
                form.save()
                messages.success(request, "Profil mis à jour avec succès")
                return redirect('espace_candidat')
        else:
            form = CandidatProfileForm(instance=inscription)
            
        return render(request, 'candidat/modifier_profil.html', {'form': form})
        
    except Inscription.DoesNotExist:
        messages.error(request, "Aucune inscription trouvée")
        return redirect('home')



@login_required
def password_change(request):
    """Modification du mot de passe."""
    try:
        inscription = Inscription.objects.get(email=request.user.email)
        
        if request.method == 'POST':
            form = CandidatProfileForm(request.POST, instance=inscription)
            if form.is_valid():
                form.save()
                messages.success(request, "Profil mis à jour avec succès")
                return redirect('espace_candidat')
        else:
            form = CandidatProfileForm(instance=inscription)
            
        return render(request, 'candidat/modifier_profil.html', {'form': form})
        
    except Inscription.DoesNotExist:
        messages.error(request, "Aucune inscription trouvée")
        return redirect('home')



@login_required
def gerer_documents(request):
    """Gestion des documents du candidat."""
    try:
        inscription = Inscription.objects.get(email=request.user.email)
        
        if request.method == 'POST':
            for doc_type in ['photo_identite', 'bac_scan', 'diplome_scan', 'extrait_naissance']:
                if doc_type in request.FILES:
                    setattr(inscription, doc_type, request.FILES[doc_type])
            inscription.save()
            messages.success(request, "Documents mis à jour avec succès")
            return redirect('gerer_documents')
            
        return render(request, 'candidat/gerer_documents.html', {'inscription': inscription})
        
    except Inscription.DoesNotExist:
        messages.error(request, "Aucune inscription trouvée")
        return redirect('home')

@login_required
def details_formation(request):
    """Détails de la formation du candidat."""
    try:
        inscription = Inscription.objects.get(email=request.user.email)
        formation = Formation.objects.filter(nom=inscription.formation).first()
        
        if not formation:
            messages.error(request, "Formation non trouvée")
            return redirect('espace_candidat')
            
        return render(request, 'candidat/details_formation.html', {
            'formation': formation,
            'inscription': inscription
        })
        
    except Inscription.DoesNotExist:
        messages.error(request, "Aucune inscription trouvée")
        return redirect('home')


# 7. VUES FORMATIONS
import logging
logger = logging.getLogger(__name__)

def inscription_formation(request, formation_type):
    """Processus complet d'inscription à une formation."""
    current_year = timezone.now().year
    context = {
        'formation_type': formation_type,
        'current_year': current_year,
        'form_data': request.POST if request.method == "POST" else None,
        'sexe_choices': Inscription.SEXE_CHOICES,
        'serie_bac_choices': Inscription.SERIE_BAC_CHOICES,
        'mention_choices': Inscription.MENTION_CHOICES,
    }

    if request.method != "POST":
        return render(request, "formations/inscription.html", context)

    # Validation des données
    data = request.POST
    files = request.FILES

    # Validation email
    if data.get("email") != data.get("email_confirmation"):
        messages.error(request, "Les adresses email ne correspondent pas")
        return render(request, "formations/inscription.html", context)

    # Validation fichiers
    required_files = {
        'photo_identite': "Photo d'identité",
        'bac_scan': "Diplôme du bac",
        'diplome_scan': "Diplôme de licence", 
        'extrait_naissance': "Extrait de naissance"
    }
    
    missing_files = [name for field, name in required_files.items() if field not in files]
    if missing_files:
        messages.error(request, f"Fichiers obligatoires manquants: {', '.join(missing_files)}")
        return render(request, "formations/inscription.html", context)

    try:
        # Conversion et validation des dates
        date_naissance = datetime.strptime(data.get("date_naissance", ""), "%Y-%m-%d").date()
        annee_bac = int(data.get("annee_obtentionbac", 0))
        annee_licence = int(data.get("annee_obtentionlicence", 0))
        
        if annee_bac > current_year or annee_licence > current_year:
            raise ValueError("L'année ne peut pas être dans le futur")
        if annee_licence < annee_bac:
            raise ValueError("La licence ne peut pas être antérieure au bac")

        if not re.match(r'^\+?[\d\s]{10,15}$', data.get("telephone", "")):
            raise ValueError("Numéro de téléphone invalide")

        # Génération du username
        nom = data.get("nom", "").lower()
        prenom = data.get("prenom", "").lower()[:3]
        username_base = f"{nom}_{prenom}"
        username = username_base
        counter = 1
        
        while CustomUser.objects.filter(username=username).exists():
            username = f"{username_base}_{counter}"
            counter += 1

        with transaction.atomic():
            # Création de l'utilisateur en premier
            user = CustomUser.objects.create_user(
                username=username,
                email=data.get("email").lower(),
                password=data.get("password"),
                first_name=data.get("prenom", "").capitalize(),
                last_name=data.get("nom", "").upper()
            )
            
            # Création de l'inscription
            inscription = Inscription(
                user=user,
                nom=data.get("nom", "").upper(),
                prenom=data.get("prenom", "").capitalize(),
                sexe=data.get("sexe"),
                date_naissance=date_naissance,
                lieu_naissance=data.get("lieu_naissance"),
                email=data.get("email").lower(),
                email_confirmation=data.get("email_confirmation").lower(),
                telephone=data.get("telephone"),
                cmu=data.get("cmu"),
                cni=data.get("cni"),
                serie_bac=data.get("serie_bac", "A"),
                annee_obtentionbac=annee_bac,
                mention_bac=data.get("mention_bac"),
                numero_bac=data.get("numero_bac", "").upper(),
                ecole_diplomebac=data.get("ecole_diplomebac"),
                licence=data.get("licence", "Inconnu"),
                annee_obtentionlicence=annee_licence,
                formation=formation_type,
                photo_identite=files['photo_identite'],
                bac_scan=files['bac_scan'],
                diplome_scan=files['diplome_scan'],
                extrait_naissance=files['extrait_naissance'],
            )
            
            inscription.full_clean()
            inscription.save()

            # Connexion automatique
            user = authenticate(request, username=username, password=data.get("password"))
            if user:
                login(request, user)
                messages.success(request, "Inscription réussie et compte créé!")
                return redirect('espace_candidat')

    except ValidationError as e:
        for field, errors in e.message_dict.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    except ValueError as e:
        messages.error(request, f"Erreur de validation: {str(e)}")
    except Exception as e:
        logger.error(f"Erreur inscription: {str(e)}", exc_info=True)
        messages.error(request, "Une erreur technique est survenue. Veuillez réessayer.")

    return render(request, "formations/inscription.html", context)

# 8. VUES GESTIONNAIRE
@staff_member_required
def dashboard(request):
    """Tableau de bord administrateur."""
    inscriptions = list(Inscription.objects.all().values(
        'id', 'nom', 'prenom', 'email', 'telephone', 
        'formation', 'cmu', 'cni', 'photo'
    ))

    for inscrit in inscriptions:
        if inscrit['photo']:
            inscrit['photo'] = f"/media/{inscrit['photo']}"

    context = {
        "inscriptions_json": mark_safe(json.dumps(inscriptions, default=str)),
        "total_inscriptions": Inscription.objects.count(),
        "inscriptions_mois": Inscription.objects.filter(
            date_inscription__month=timezone.now().month
        ).count(),
    }
    return render(request, "gestionnaire/dashboard.html", context)

@csrf_exempt
@login_required
def envoyer_email_automatique(request):
    """Envoi d'emails groupés."""
    if request.method == "POST":
        inscrits = Inscription.objects.all()
        emails = [inscrit.email for inscrit in inscrits if inscrit.email]

        if not emails:
            return JsonResponse({"message": "Aucun email trouvé."}, status=400)

        try:
            send_mail(
                "Informations Importantes",
                "Bonjour, ceci est un message automatique pour vous tenir informé.",
                settings.DEFAULT_FROM_EMAIL,
                emails,
                fail_silently=False,
            )
            return JsonResponse({"message": "Emails envoyés avec succès !"})
        except Exception as e:
            return JsonResponse({"message": f"Erreur serveur : {str(e)}"}, status=500)

    return JsonResponse({"message": "Méthode non autorisée"}, status=405)

@csrf_exempt
def supprimer_inscrit(request):
    """Suppression d'un inscrit via AJAX."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            inscrit_id = data.get("id")
            inscrit = get_object_or_404(Inscription, id=inscrit_id)
            inscrit.delete()
            return JsonResponse({"message": "Inscription supprimée avec succès !"}, status=200)
        except Exception as e:
            return JsonResponse({"message": f"Erreur : {str(e)}"}, status=500)


# 9. VUES API

class TeamMemberAPIView(RetrieveAPIView):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    lookup_field = 'slug'



class TeamMemberDetailView(RetrieveAPIView):
    serializer_class = TeamMemberSerializer
    
    def get_object(self):
        slug = self.kwargs.get('slug')
        return get_object_or_404(TeamMember, slug=slug)

# 10. UTILITAIRES
def generate_pdf(inscription):
    """Génère un PDF à partir d'une inscription."""
    template = get_template('formations/inscription_pdf.html')
    html = template.render({'inscription': inscription})
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('utf-8')), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse("Erreur lors de la génération du PDF", status=500)


@login_required
@require_POST
@csrf_exempt
def upload_document(request):
    ALLOWED_TYPES = {
        'bac': ['application/pdf', 'image/jpeg', 'image/png'],
        'diplome': ['application/pdf', 'image/jpeg', 'image/png'],
        'extrait': ['application/pdf', 'image/jpeg', 'image/png'],
        'photo': ['image/jpeg', 'image/png']
    }
    MAX_SIZE = 5 * 1024 * 1024  # 5MB

    try:
        inscription = Inscription.objects.get(email=request.user.email)
        document_type = request.POST.get('document_type')
        document_file = request.FILES.get('document')

        # Validations
        if not document_type or document_type not in ALLOWED_TYPES:
            raise ValidationError("Type de document invalide")
        
        if not document_file:
            raise ValidationError("Aucun fichier fourni")
            
        if document_file.size > MAX_SIZE:
            raise ValidationError(f"Fichier trop volumineux (max {MAX_SIZE/1024/1024}MB)")
            
        if document_file.content_type not in ALLOWED_TYPES[document_type]:
            raise ValidationError("Type de fichier non autorisé")

        # Sauvegarde
        if document_type == 'bac':
            inscription.bac_scan = document_file
        elif document_type == 'diplome':
            inscription.diplome_scan = document_file
        elif document_type == 'extrait':
            inscription.extrait_naissance = document_file
        elif document_type == 'photo':
            inscription.photo_identite = document_file

        inscription.save()
        
        return JsonResponse({
            "status": "success",
            "message": "Document téléchargé avec succès",
            "document_url": getattr(inscription, document_type).url
        })

    except Inscription.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Aucune inscription trouvée"}, 
            status=404
        )
    except ValidationError as e:
        return JsonResponse(
            {"status": "error", "message": str(e)}, 
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Erreur serveur: {str(e)}"}, 
            status=500
        )

@login_required
@require_POST
@csrf_exempt
def update_profile(request):
    """
    Vue avancée pour mettre à jour le profil avec validation
    """
    try:
        inscription = Inscription.objects.get(email=request.user.email)
        
        # Liste des champs autorisés à être modifiés
        allowed_fields = {
            'telephone': {
                'pattern': r'^\+?[\d\s]{10,15}$',
                'error': 'Numéro de téléphone invalide'
            },
            'cmu': {},
            'cni': {},
            # Ajoutez d'autres champs modifiables ici
        }
        
        updates = {}
        errors = {}
        
        # Validation des champs
        for field, config in allowed_fields.items():
            if field in request.POST:
                value = request.POST[field].strip()
                
                # Validation par regex si spécifié
                if 'pattern' in config:
                    if not re.match(config['pattern'], value):
                        errors[field] = config.get('error', 'Format invalide')
                        continue
                
                updates[field] = value
        
        if errors:
            return JsonResponse({
                "status": "error",
                "message": "Erreurs de validation",
                "errors": errors
            }, status=400)
        
        # Application des modifications
        for field, value in updates.items():
            setattr(inscription, field, value)
        
        inscription.save()
        return JsonResponse({
            "status": "success",
            "message": "Profil mis à jour avec succès",
            "updated_fields": list(updates.keys())
        })
        
    except Inscription.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Aucune inscription trouvée"}, 
            status=404
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Erreur serveur: {str(e)}"}, 
            status=500
        )



class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    html_email_template_name = 'registration/password_reset_email.html'
    
    def form_valid(self, form):
        # Logique supplémentaire avant envoi (optionnel)
        response = super().form_valid(form)
        # Logique supplémentaire après envoi (optionnel)
        return response

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


# development/views.py
@login_required(login_url='candidat_login_page')  
@user_passes_test(is_candidat, login_url='candidat_login_page')
def details_programme(request):
    """Détails complets du programme de formation."""
    try:
        inscription = Inscription.objects.get(email=request.user.email)
        formation = Formation.objects.filter(nom=inscription.formation).first()
        programme = ProgrammeFormation.objects.filter(formation=formation).first() if formation else None
        
        context = {
            'inscription': inscription,
            'formation': formation,
            'programme': programme,
        }
        return render(request, 'candidat/details_programme.html', context)
        
    except Inscription.DoesNotExist:
        messages.error(request, "Aucune inscription trouvée")
        return redirect('espace_candidat')

@login_required(login_url='candidat_login_page')  
@user_passes_test(is_candidat, login_url='candidat_login_page')
def details_maquette(request):
    """Détails complets de la maquette pédagogique."""
    try:
        inscription = Inscription.objects.get(email=request.user.email)
        formation = Formation.objects.filter(nom=inscription.formation).first()
        maquette = MarquettePedagogique.objects.filter(formation=formation).first() if formation else None
        
        context = {
            'inscription': inscription,
            'formation': formation,
            'maquette': maquette,
        }
        return render(request, 'candidat/details_maquette.html', context)
        
    except Inscription.DoesNotExist:
        messages.error(request, "Aucune inscription trouvée")
        return redirect('espace_candidat')

from django.db.models import Q

def activite_detail(request, id):
    """Détail d'une activité avec navigation précédente/suivante."""
    activity = get_object_or_404(Activite.objects.select_related(), id=id)

    # Gestion des dates None - solution robuste
    if activity.date is not None:
        # Si la date existe, filtrer par date
        previous_activity = (
            Activite.objects
            .filter(date__lt=activity.date)
            .order_by('-date')
            .first()
        )
        next_activity = (
            Activite.objects
            .filter(date__gt=activity.date)
            .order_by('date')
            .first()
        )
    else:
        # Si pas de date, utiliser l'ID pour la navigation
        previous_activity = (
            Activite.objects
            .filter(id__lt=activity.id)
            .order_by('-id')
            .first()
        )
        next_activity = (
            Activite.objects
            .filter(id__gt=activity.id)
            .order_by('id')
            .first()
        )

    return render(request, 'acceuil/activity_detail.html', {
        'activity': activity,
        'prev_activity': previous_activity,
        'next_activity': next_activity,
    })
