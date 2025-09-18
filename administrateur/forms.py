# developpement/forms.py
from django import forms
from developpement.models import  Activite


class ActiviteForm(forms.ModelForm):
    class Meta:
        model = Activite
        fields = ["title", "description", "category", "date", "location"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Titre de l'activité"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Description détaillée de l'activité...",
                }
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Lieu de l'activité"}
            ),
        }
        labels = {
            "title": "Titre",
            "description": "Description",
            "category": "Catégorie",
            "date": "Date prévue",
            "location": "Lieu",
        }



class DocumentForm(forms.Form):
    DOCUMENT_TYPES = [
        ("photo_identite", "Photo d'identité"),
        ("bac_scan", "Diplôme du Bac"),
        ("diplome_scan", "Diplôme de Licence"),
        ("extrait_naissance", "Extrait de naissance"),
    ]

    document_type = forms.ChoiceField(choices=DOCUMENT_TYPES, label="Type de document")

    document_file = forms.FileField(label="Fichier")
