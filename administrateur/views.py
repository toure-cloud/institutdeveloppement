# administrateur/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core import serializers
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db.models import Q

import json
import csv
import os
import logging
from datetime import timedelta
from io import BytesIO

# Importations pour l'envoi d'emails avec pièces jointes
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

# Importations pour la génération de PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# Importations des modèles et formulaires
from developpement.models import Inscription, Activite, ImageActivite, ConvocationExamen
from developpement.forms import DocumentForm
from .forms import ActiviteForm
from django.conf import settings
from django.contrib.auth import get_user_model

from django.contrib.auth.models import User as CustomUser


logger = logging.getLogger(__name__)

# Fonctions utilitaires
def is_administrateur(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_authenticated and user.is_staff

# Vues d'authentification
def admin_login_page(request):
    """Page de login spécifique pour les administrateurs"""
    # Si l'utilisateur est déjà connecté et est staff, rediriger vers le dashboard
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)

            # Récupérer l'URL de redirection
            next_url = request.POST.get("next", request.GET.get("next", ""))

            # Corriger les URLs contenant /admin/dashboard/
            if next_url and "/admin/dashboard/" in next_url:
                next_url = next_url.replace(
                    "/admin/dashboard/", "/administrateur/dashboard/"
                )

            # Vérifier que l'URL est sûre et non vide
            if next_url and is_safe_url(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            # Redirection par défaut
            return redirect("administrateur:dashboard")
        else:
            messages.error(
                request, "Accès réservé aux administrateurs. Vérifiez vos identifiants."
            )

    return render(request, "administrateur/admin_login.html")
# administrateur/views.py

# Utilisez get_user_model() pour obtenir le modèle utilisateur personnalisé
User = get_user_model()


def creer_compte_admin(request):
    """Vue pour créer un compte administrateur avec le modèle User personnalisé"""
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        is_superuser = request.POST.get("is_superuser") == "on"

        # Validation des données
        if not all([username, email, password1, password2]):
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect("administrateur:admin_login_page")

        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect("administrateur:admin_login_page")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
            return redirect("administrateur:admin_login_page")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return redirect("administrateur:admin_login_page")

        # Création de l'utilisateur avec le modèle personnalisé
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                is_staff=True,
                is_superuser=is_superuser,
            )

            # Connecter automatiquement l'utilisateur
            user = authenticate(request, username=username, password=password1)
            if user:
                login(request, user)
                messages.success(
                    request,
                    f"Compte administrateur créé avec succès ! Bienvenue {username}.",
                )
                return redirect("dashboard")
            else:
                messages.success(
                    request, "Compte créé avec succès. Veuillez vous connecter."
                )
                return redirect("administrateur:admin_login_page")

        except Exception as e:
            messages.error(request, f"Erreur lors de la création du compte: {str(e)}")
            return redirect("administrateur:admin_login_page")

    # Si méthode GET, rediriger vers la page de login
    return redirect("administrateur:admin_login_page")


# Vues du tableau de bord et gestion des inscriptions
@login_required(login_url="admin_login_page")
@user_passes_test(is_administrateur, login_url="admin_login_page")
def dashboard(request):
    """Vue du tableau de bord administrateur"""
    try:
        inscriptions = Inscription.objects.all()

        # Statistiques
        total_inscriptions = inscriptions.count() or 0
        inscriptions_valides = inscriptions.filter(statut="V").count() or 0
        inscriptions_attente = inscriptions.filter(statut="E").count() or 0
        inscriptions_rejetees = inscriptions.filter(statut="R").count() or 0

        # Inscriptions récentes (7 derniers jours)
        date_limite = timezone.now() - timedelta(days=7)
        inscriptions_recentes = inscriptions.filter(date_inscription__gte=date_limite).count() or 0

        # Répartition par formation
        formations_stats = []
        formations_existantes = list(set([
            inscrit.formation for inscrit in inscriptions 
            if inscrit.formation and inscrit.formation.strip()
        ]))

        for formation_nom in formations_existantes:
            count = inscriptions.filter(formation=formation_nom).count() or 0
            if count > 0:
                formations_stats.append({
                    "nom": formation_nom,
                    "count": count,
                    "pourcentage": (count / total_inscriptions * 100) if total_inscriptions > 0 else 0,
                })

        # Dernières inscriptions
        dernieres_inscriptions = inscriptions.order_by("-date_inscription")[:10]

        context = {
            "total_inscriptions": total_inscriptions,
            "inscriptions_valides": inscriptions_valides,
            "inscriptions_attente": inscriptions_attente,
            "inscriptions_rejetees": inscriptions_rejetees,
            "inscriptions_recentes": inscriptions_recentes,
            "formations_stats": formations_stats,
            "dernieres_inscriptions": dernieres_inscriptions,
            "taux_validation": (inscriptions_valides / total_inscriptions * 100) if total_inscriptions > 0 else 0,
        }

        return render(request, "administrateur/dashboard.html", context)

    except Exception as e:
        context = {
            "total_inscriptions": 0,
            "inscriptions_valides": 0,
            "inscriptions_attente": 0,
            "inscriptions_rejetees": 0,
            "inscriptions_recentes": 0,
            "formations_stats": [],
            "dernieres_inscriptions": [],
            "taux_validation": 0,
        }
        return render(request, "administrateur/dashboard.html", context)

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def liste_inscrits(request):
    """Vue pour afficher la liste des inscrits avec support AngularJS"""
    inscriptions = Inscription.objects.all()

    # Compter les différents statuts
    total_inscriptions = inscriptions.count()
    inscriptions_valides = inscriptions.filter(statut="V")
    inscriptions_attente = inscriptions.filter(statut="E")
    inscriptions_rejetees = inscriptions.filter(statut="R")

    # Extraire les formations uniques pour le filtre
    formations_uniques = list(set([
        inscrit.formation for inscrit in inscriptions 
        if inscrit.formation and inscrit.formation.strip()
    ]))

    # Préparer les données pour le template
    inscriptions_data = []
    for inscrit in inscriptions:
        inscriptions_data.append({
            "id": inscrit.id,
            "nom": inscrit.nom,
            "prenom": inscrit.prenom,
            "email": inscrit.email,
            "telephone": inscrit.telephone or "Non renseigné",
            "formation": inscrit.formation or "Non spécifiée",
            "statut": inscrit.get_statut_display(),
            "photo_identite": inscrit.photo_identite.url if inscrit.photo_identite else "",
            "bac_scan": inscrit.bac_scan.url if inscrit.bac_scan else "",
            "diplome_scan": inscrit.diplome_scan.url if inscrit.diplome_scan else "",
            "extrait_naissance": inscrit.extrait_naissance.url if inscrit.extrait_naissance else "",
            "cmu": inscrit.cmu or "Non renseigné",
            "cni": inscrit.cni or "Non renseigné",
            "selected": False,
        })

    context = {
        "inscriptions": inscriptions,
        "total_inscriptions": total_inscriptions,
        "inscriptions_valides": inscriptions_valides.count(),
        "inscriptions_attente": inscriptions_attente.count(),
        "inscriptions_rejetees": inscriptions_rejetees.count(),
        "inscriptions_json": json.dumps(inscriptions_data),
        "formations": sorted(formations_uniques),
    }

    return render(request, "administrateur/liste_inscrits.html", context)

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def inscrit_details(request, pk):
    """Retourne les détails d'un inscrit en JSON pour le modal"""
    inscrit = get_object_or_404(Inscription, pk=pk)
    
    data = {
        'id': inscrit.id,
        'nom': inscrit.nom,
        'prenom': inscrit.prenom,
        'email': inscrit.email,
        'telephone': inscrit.telephone,
        'sexe': inscrit.get_sexe_display(),
        'date_naissance': inscrit.date_naissance.strftime('%d/%m/%Y') if inscrit.date_naissance else "Non renseignée",
        'lieu_naissance': inscrit.lieu_naissance or "Non renseigné",
        'formation': inscrit.formation,
        'statut': inscrit.statut,
        'statut_display': inscrit.get_statut_display(),
        'statut_class': 'bg-success' if inscrit.statut == 'V' else 'bg-warning' if inscrit.statut == 'E' else 'bg-danger',
        'date_inscription': inscrit.date_inscription.strftime('%d/%m/%Y à %H:%M') if inscrit.date_inscription else "Non renseignée",
        'cmu': inscrit.cmu,
        'cni': inscrit.cni,
        'photo_identite': inscrit.photo_identite.url if inscrit.photo_identite else None,
        'bac_scan': inscrit.bac_scan.url if inscrit.bac_scan else None,
        'diplome_scan': inscrit.diplome_scan.url if inscrit.diplome_scan else None,
        'extrait_naissance': inscrit.extrait_naissance.url if inscrit.extrait_naissance else None,
    }
    
    return JsonResponse(data)

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def valider_inscrit(request, pk):
    """Valider une inscription"""
    inscrit = get_object_or_404(Inscription, pk=pk)
    
    if inscrit.statut == 'E':  # Seulement si en attente
        inscrit.statut = 'V'
        inscrit.save()
        messages.success(request, f"Inscription de {inscrit.nom} {inscrit.prenom} validée avec succès!")
    else:
        messages.warning(request, "Cette inscription ne peut pas être validée.")
    
    return redirect('liste_inscrits')

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def rejeter_inscrit(request, pk):
    """Rejeter une inscription"""
    inscrit = get_object_or_404(Inscription, pk=pk)
    
    if inscrit.statut == 'E':  # Seulement si en attente
        inscrit.statut = 'R'
        inscrit.save()
        messages.success(request, f"Inscription de {inscrit.nom} {inscrit.prenom} rejetée.")
    else:
        messages.warning(request, "Cette inscription ne peut pas être rejetée.")
    
    return redirect('liste_inscrits')

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def supprimer_inscrit(request, pk):
    """Supprimer définitivement une inscription"""
    inscrit = get_object_or_404(Inscription, pk=pk)
    
    if request.method == 'POST':
        nom_complet = f"{inscrit.nom} {inscrit.prenom}"
        inscrit.delete()
        messages.success(request, f"Inscription de {nom_complet} supprimée définitivement.")
        return redirect('liste_inscrits')
    
    # Si GET, afficher une confirmation
    return render(request, 'administrateur/confirmation_suppression.html', {'inscrit': inscrit})

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def exporter_inscrits(request):
    """Exporter les inscrits en CSV"""
    inscriptions = Inscription.objects.all().order_by('-date_inscription')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inscriptions_{}.csv"'.format(
        timezone.now().strftime('%Y%m%d_%H%M%S')
    )
    
    writer = csv.writer(response, delimiter=';')
    
    # En-têtes
    writer.writerow([
        'Nom', 'Prénom', 'Email', 'Téléphone', 'Formation', 
        'Date Inscription', 'Statut', 'CMU', 'CNI'
    ])
    
    # Données
    for inscrit in inscriptions:
        writer.writerow([
            inscrit.nom,
            inscrit.prenom,
            inscrit.email,
            inscrit.telephone or '',
            inscrit.formation or '',
            inscrit.date_inscription.strftime('%d/%m/%Y %H:%M') if inscrit.date_inscription else '',
            inscrit.get_statut_display(),
            inscrit.cmu or '',
            inscrit.cni or '',
        ])
    
    return response

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def envoyer_email_inscrit(request, pk):
    """Envoyer un email à un inscrit"""
    if request.method == 'POST':
        inscrit = get_object_or_404(Inscription, pk=pk)
        sujet = request.POST.get('sujet')
        message = request.POST.get('message')
        
        # Ici vous intégrerez votre système d'envoi d'email
        # Exemple avec console pour le développement
        print(f"Email à envoyer à: {inscrit.email}")
        print(f"Sujet: {sujet}")
        print(f"Message: {message}")
        
        messages.success(request, f"Email envoyé à {inscrit.email}")
        return redirect('liste_inscrits')
    
    return redirect('liste_inscrits')

# Vues pour l'envoi d'emails
@require_POST
@csrf_exempt
def valider_selection(request):
    """Valider une sélection d'inscrits"""
    try:
        inscrits_ids = json.loads(request.POST.get("inscrits_ids", "[]"))
        inscriptions = Inscription.objects.filter(id__in=inscrits_ids)
        count = inscriptions.update(statut="V")

        # Envoyer des emails de confirmation
        for inscrit in inscriptions:
            sujet = "Votre inscription a été validée"
            message_html = render_to_string(
                "emails/inscription_validee.html", {"inscrit": inscrit}
            )
            message_texte = strip_tags(message_html)

            send_mail(
                sujet,
                message_texte,
                settings.DEFAULT_FROM_EMAIL,
                [inscrit.email],
                html_message=message_html,
                fail_silently=True,
            )

        return JsonResponse(
            {
                "success": True,
                "count": count,
                "message": f"{count} inscrits validés avec succès",
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

@require_POST
@csrf_exempt
def supprimer_selection(request):
    """Supprimer une sélection d'inscrits"""
    try:
        inscrits_ids = json.loads(request.POST.get("inscrits_ids", "[]"))
        inscriptions = Inscription.objects.filter(id__in=inscrits_ids)

        # Sauvegarder les emails pour les notifications
        emails = [inscrit.email for inscrit in inscriptions]

        # Supprimer les inscrits
        count = inscriptions.count()
        inscriptions.delete()

        # Envoyer des emails de notification
        sujet = "Votre inscription a été supprimée"
        message = "Votre inscription à notre formation a été supprimée. Pour plus d'informations, veuillez nous contacter."

        for email in emails:
            send_mail(
                sujet, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True
            )

        return JsonResponse(
            {
                "success": True,
                "count": count,
                "message": f"{count} inscrits supprimés avec succès",
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

@require_POST
@csrf_exempt
def envoyer_mail(request):
    """Envoyer un email à une sélection d'inscrits avec gestion des pièces jointes"""
    try:
        emails = json.loads(request.POST.get("emails", "[]"))
        sujet = request.POST.get("sujet", "").strip()
        message = request.POST.get("message", "").strip()
        include_attachment = request.POST.get("includeAttachment") == "true"

        if not emails:
            return JsonResponse(
                {"success": False, "error": "Aucun destinataire spécifié"}
            )

        if not sujet:
            return JsonResponse({"success": False, "error": "Le sujet est requis"})

        if not message:
            return JsonResponse({"success": False, "error": "Le message est requis"})

        message_html = render_to_string(
            "administrateur/email_template.html",
            {
                "sujet": sujet,
                "message": message,
                "date_envoi": timezone.now().strftime("%d/%m/%Y à %H:%M"),
                "site_name": getattr(settings, "SITE_NAME", "Institut de Formation"),
                "site_url": getattr(settings, "SITE_URL", "http://127.0.0.1:8000"),
                "unsubscribe_url": f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/desabonnement/",
            },
        )

        message_texte = strip_tags(message)

        # Configuration SMTP
        email_host = getattr(settings, "EMAIL_HOST", "smtp.gmail.com")
        email_port = getattr(settings, "EMAIL_PORT", 587)
        email_username = getattr(settings, "EMAIL_HOST_USER", "")
        email_password = getattr(settings, "EMAIL_HOST_PASSWORD", "")

        # Créer le message MIME
        msg = MIMEMultipart()
        msg["Subject"] = sujet
        msg["From"] = getattr(settings, "DEFAULT_FROM_EMAIL", email_username)
        msg["To"] = ", ".join(emails)
        msg["Bcc"] = ", ".join(emails)  # Envoyer en Bcc pour préserver la confidentialité

        # Ajouter les parties texte et HTML
        msg.attach(MIMEText(message_texte, "plain"))
        msg.attach(MIMEText(message_html, "html"))

        # Gestion des pièces jointes
        if include_attachment and request.FILES.get("piece_jointe"):
            piece_jointe = request.FILES["piece_jointe"]
            attachment = MIMEApplication(piece_jointe.read())
            attachment.add_header(
                "Content-Disposition", "attachment", filename=piece_jointe.name
            )
            msg.attach(attachment)

        # Envoyer l'email via SMTP
        try:
            server = smtplib.SMTP(email_host, email_port)
            server.starttls()
            server.login(email_username, email_password)
            server.send_message(msg)
            server.quit()

            # Logger l'envoi
            logger.info(
                f"Email envoyé à {len(emails)} destinataires: {', '.join(emails)}"
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Email envoyé avec succès à {len(emails)} destinataire(s)",
                    "count": len(emails),
                }
            )

        except smtplib.SMTPException as e:
            logger.error(f"Erreur SMTP: {str(e)}")
            return JsonResponse(
                {"success": False, "error": f"Erreur d'envoi SMTP: {str(e)}"}
            )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Format de données invalide"})
    except Exception as e:
        logger.error(f"Erreur générale dans envoyer_mail: {str(e)}")
        return JsonResponse(
            {"success": False, "error": f"Erreur lors de l'envoi: {str(e)}"}
        )

def test_email_config(request):
    """Vue pour tester la configuration email"""
    try:
        # Test d'envoi simple
        send_mail(
            "Test de configuration email",
            "Ceci est un email de test depuis Django.",
            settings.DEFAULT_FROM_EMAIL,
            ["votre.email@test.com"],  # Remplacez par votre email
            fail_silently=False,
        )
        return JsonResponse(
            {"success": True, "message": "Email de test envoyé avec succès"}
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

# Vues pour la gestion des activités
@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def gestion_activites(request):
    activites = Activite.objects.all().order_by('-date')
    return render(request, 'administrateur/activite.html', {'activites': activites})

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def ajouter_activite(request):
    if request.method == 'POST':
        form = ActiviteForm(request.POST)
        if form.is_valid():
            activite = form.save(commit=False)
            activite.created_by = request.user
            activite.save()
            
            # Gestion des images multiples
            images = request.FILES.getlist('images')
            for image in images:
                # Vérifier la taille du fichier (max 5MB)
                if image.size > 5 * 1024 * 1024:
                    messages.warning(request, f"L'image {image.name} est trop volumineuse (max 5MB).")
                    continue
                
                # Vérifier le type de fichier
                allowed_types = ['image/jpeg', 'image/png', 'image/gif']
                if image.content_type not in allowed_types:
                    messages.warning(request, f"Le format {image.content_type} n'est pas supporté.")
                    continue
                
                # Créer l'instance ImageActivite
                ImageActivite.objects.create(
                    activite=activite,
                    image=image,
                    uploaded_by=request.user
                )
            
            messages.success(request, "L'activité a été ajoutée avec succès !")
            return redirect('liste_activites')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ActiviteForm()
    
    return render(request, 'administrateur/ajouter_activite.html', {'form': form})

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def liste_activites(request):
    activites = Activite.objects.all().order_by('-created_at')
    return render(request, 'administrateur/liste_activite.html', {'activites': activites})

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def detail_activite(request, activite_id):
    activite = get_object_or_404(Activite, id=activite_id)
    return render(request, 'administrateur/detail_activite.html', {'activite': activite})

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def modifier_activite(request, activite_id):
    activite = get_object_or_404(Activite, id=activite_id)
    if request.method == 'POST':
        form = ActiviteForm(request.POST, instance=activite)
        if form.is_valid():
            form.save()
            messages.success(request, "L'activité a été modifiée avec succès !")
            return redirect('liste_activites')
    else:
        form = ActiviteForm(instance=activite)
    return render(request, 'administrateur/modifier_activite.html', {'form': form, 'activite': activite})

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
def supprimer_activite(request, activite_id):
    activite = get_object_or_404(Activite, id=activite_id)
    if request.method == 'POST':
        activite.delete()
        messages.success(request, "L'activité a été supprimée avec succès !")
        return redirect('liste_activites')
    return render(request, 'administrateur/confirmer_suppression.html', {'activite': activite})

@login_required
@user_passes_test(is_administrateur, login_url='admin_login_page')
@require_POST
def supprimer_image_activite(request, image_id):
    """Vue pour supprimer une image d'une activité"""
    image = get_object_or_404(ImageActivite, id=image_id)
    activite_id = image.activite.id
    image.delete()

    messages.success(request, "L'image a été supprimée avec succès!")
    return redirect("modifier_activite", activite_id=activite_id)

# Vues pour la gestion des documents et convocations
@login_required
def generer_convocation(request):
    try:
        inscription = Inscription.objects.get(user=request.user)
    except Inscription.DoesNotExist:
        messages.error(request, "Aucune inscription trouvée.")
        return redirect('espace_candidat')
    
    try:
        convocation_exam = ConvocationExamen.objects.get(formation=inscription.formation)
    except ConvocationExamen.DoesNotExist:
        messages.error(request, "Aucune convocation disponible pour votre formation.")
        return redirect('espace_candidat')
    
    # Création du PDF en mémoire
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centered
    )
    
    normal_style = styles['BodyText']
    bold_style = ParagraphStyle(
        'BoldText',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold'
    )
    
    # Contenu du PDF
    elements.append(Paragraph("CONVOCATION AU CONCOURS D'ENTRÉE", title_style))
    elements.append(Spacer(1, 20))
    
    # Informations du candidat
    candidate_info = [
        ["Nom:", inscription.nom.upper()],
        ["Prénom:", inscription.prenom],
        ["Date de naissance:", inscription.date_naissance.strftime("%d/%m/%Y") if inscription.date_naissance else "Non renseignée"],
        ["Lieu de naissance:", inscription.lieu_naissance or "Non renseigné"],
        ["Numéro CNI:", inscription.cni or "Non renseigné"],
        ["Formation:", inscription.formation.upper()],
    ]
    
    candidate_table = Table(candidate_info, colWidths=[60*mm, 100*mm])
    candidate_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(candidate_table)
    elements.append(Spacer(1, 20))
    
    # Informations de l'examen
    elements.append(Paragraph("INFORMATIONS SUR L'EXAMEN", bold_style))
    elements.append(Spacer(1, 10))
    
    exam_info = [
        ["Date:", convocation_exam.date_examen.strftime("%d/%m/%Y")],
        ["Heure:", convocation_exam.heure_examen],
        ["Lieu:", convocation_exam.lieu_examen],
        ["Salle:", convocation_exam.salle or "À préciser"],
    ]
    
    exam_table = Table(exam_info, colWidths=[30*mm, 130*mm])
    exam_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(exam_table)
    elements.append(Spacer(1, 20))
    
    # Instructions
    elements.append(Paragraph("CONSIGNES IMPORTANTES", bold_style))
    elements.append(Spacer(1, 10))
    
    instructions = [
        "• Se présenter 30 minutes avant l'heure de l'examen",
        "• Se munir de cette convocation et d'une pièce d'identité officielle",
        "• Les téléphones portables et tout appareil électronique sont interdits",
        "• Aucun document n'est autorisé sauf mention contraire",
        "• Tout retardataire ne sera pas admis en salle d'examen"
    ]
    
    for instruction in instructions:
        elements.append(Paragraph(instruction, normal_style))
        elements.append(Spacer(1, 5))
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Bonne chance pour votre examen !", normal_style))
    
    # Génération du PDF
    doc.build(elements)
    
    # Préparation de la réponse
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="convocation_{inscription.nom}_{inscription.prenom}.pdf"'
    
    return response

@login_required
def modifier_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document_type = form.cleaned_data['document_type']
            document_file = request.FILES['document_file']
            
            try:
                inscription = Inscription.objects.get(user=request.user)
                
                # Mise à jour du document selon le type
                if document_type == 'photo_identite':
                    # Validation supplémentaire pour la photo
                    if not document_file.content_type.startswith('image/'):
                        messages.error(request, "Le fichier doit être une image.")
                        return redirect('espace_candidat')
                    inscription.photo_identite = document_file
                
                elif document_type == 'bac_scan':
                    inscription.bac_scan = document_file
                
                elif document_type == 'diplome_scan':
                    inscription.diplome_scan = document_file
                
                elif document_type == 'extrait_naissance':
                    inscription.extrait_naissance = document_file
                
                inscription.save()
                messages.success(request, "Document mis à jour avec succès.")
                
            except Inscription.DoesNotExist:
                messages.error(request, "Aucune inscription trouvée.")
            
            return redirect('espace_candidat')
    
    return redirect('espace_candidat')

@login_required
def gerer_documents(request):
    try:
        inscription = Inscription.objects.get(user=request.user)
    except Inscription.DoesNotExist:
        messages.error(request, "Aucune inscription trouvée.")
        return redirect('espace_candidat')
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document_type = form.cleaned_data['document_type']
            document_file = request.FILES['document_file']
            
            # Mise à jour du document selon le type
            if document_type == 'photo_identite':
                inscription.photo_identite = document_file
            elif document_type == 'bac_scan':
                inscription.bac_scan = document_file
            elif document_type == 'diplome_scan':
                inscription.diplome_scan = document_file
            elif document_type == 'extrait_naissance':
                inscription.extrait_naissance = document_file
            
            inscription.save()
            messages.success(request, "Document mis à jour avec succès.")
            return redirect('gerer_documents')
    else:
        form = DocumentForm()
    
    context = {
        'inscription': inscription,
        'form': form,
    }
    
    return render(request, 'administrateur/gerer_documents.html', context)




def is_safe_url(url, allowed_hosts=None):
    """
    Return True if the url is a safe redirection (i.e. it doesn't point to
    a different host).
    """
    if not url:
        return False
        
    if allowed_hosts is None:
        allowed_hosts = set()
    
    # Utiliser la fonction moderne de Django
    return url_has_allowed_host_and_scheme(url, allowed_hosts=allowed_hosts)
