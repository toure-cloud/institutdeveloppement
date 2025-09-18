from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model  # Utilisation de get_user_model
from .models import Inscription
User = get_user_model()  # Récupère le modèle personnalisé CustomUser



class CandidatProfileForm(forms.ModelForm):
    class Meta:
        model = Inscription
        fields = [
            'telephone', 'cmu', 'cni', 
            'lieu_naissance', 'ecole_diplomebac', 'licence'
        ]
        widgets = {
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'cmu': forms.TextInput(attrs={'class': 'form-control'}),
            'cni': forms.TextInput(attrs={'class': 'form-control'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'ecole_diplomebac': forms.TextInput(attrs={'class': 'form-control'}),
            'licence': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'cmu': 'Numéro CMU',
            'cni': 'Numéro CNI',
            'ecole_diplomebac': 'École d''obtention du bac',
            'licence': 'Type de licence',
        }




class MultipleImageUploadForm(forms.Form):
    images = forms.FileField(
        widget=forms.FileInput(attrs={'multiple': False}),  # Utilisez FileInput pour gérer plusieurs fichiers
        required=False  # Les images sont optionnelles
    )

    def clean_images(self):
        images = self.files.getlist('images')  # Récupère toutes les images envoyées
        for image in images:
            if not image.content_type.startswith('image/'):
                raise forms.ValidationError("Tous les fichiers doivent être des images.")
        return images
    


class InscriptionForm(forms.ModelForm):
    class Meta:
        model = Inscription
        exclude = ['formation']

from django import forms


class DocumentForm(forms.Form):
    DOCUMENT_TYPES = [
        ("photo_identite", "Photo d'identité"),
        ("bac_scan", "Diplôme du Bac"),
        ("diplome_scan", "Diplôme de Licence"),
        ("extrait_naissance", "Extrait de naissance"),
    ]

    document_type = forms.ChoiceField(choices=DOCUMENT_TYPES, label="Type de document")

    document_file = forms.FileField(label="Fichier")
