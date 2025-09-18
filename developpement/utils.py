# utils.py
from django.core.mail import send_mail
from django.conf import settings
import os
from io import BytesIO
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMessage
from xhtml2pdf import pisa

def send_eligibility_notification(auteur):
    # Envoi de l'email de notification
    subject = "Éligibilité aux Publications Scientifiques"
    message = f"Bonjour {auteur.nom},\n\nVotre éligibilité pour publier sur notre plateforme a été confirmée."
    recipient_list = [auteur.user.email]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)


# 🔁 Convertir les URL de médias en chemins absolus (obligatoire pour les images)
def link_callback(uri, rel):
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        return uri
    if not os.path.isfile(path):
        raise Exception(f'Media URI must exist: {path}')
    return path

# ✅ Fonction pour générer le PDF
def generate_pdf(inscription):
    template = get_template('formations/inscription_pdf.html')
    html = template.render({'inscription': inscription})
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('utf-8')), result, link_callback=link_callback)

    if not pdf.err:
        return BytesIO(result.getvalue())  # retourne les données du PDF
    return None

# ✅ Fonction pour envoyer le mail avec le PDF
def send_inscription_email(inscription, pdf_bytes):
    subject = f"Confirmation d'inscription à la formation {inscription.formation}"
    message = (
        f"Bonjour {inscription.prenom},\n\n"
        f"Votre inscription à la formation « {inscription.formation} » a bien été reçue.\n"
        f"En pièce jointe, vous trouverez votre fiche d'inscription.\n\n"
        f"Cordialement,\nL’équipe UGACACI"
    )

    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [inscription.email],
        reply_to=[inscription.email_confirmation]
    )

    email.attach(
        f"{inscription.nom}_{inscription.prenom}_inscription.pdf",
        pdf_bytes.getvalue(),
        'application/pdf'
    )

    email.send(fail_silently=False)
