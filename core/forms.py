from django import forms
from .models import MessageContact


class MessageContactForm(forms.ModelForm):
    class Meta:
        model = MessageContact
        fields = ['nom', 'email', 'sujet', 'message']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemple.com'}),
            'sujet': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sujet'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Votre message', 'rows': 4}),
        }
from django import forms
from django.core.exceptions import ValidationError
import re

class InfosClientForm(forms.Form):
    nom = forms.CharField(label="Nom complet", max_length=100)
    telephone = forms.CharField(label="Téléphone", max_length=9)
    email = forms.EmailField(label="Email", required=False)
    adresse = forms.CharField(label="Adresse de livraison", widget=forms.Textarea, required=True)  # REQUIRED
    choix_retrait = forms.ChoiceField(
        label="Mode de retrait",
        choices=[('livraison', 'Livraison à domicile'), ('agence', 'Retrait en agence')],
        widget=forms.RadioSelect
    )

    def clean_telephone(self):
        tel = self.cleaned_data.get('telephone', '').strip()
        if not re.match(r'^(61|62|65|66)[0-9]{7}$', tel):
            raise ValidationError("Veuillez saisir un numéro valide")
        return tel

    def clean_adresse(self):
        adresse = self.cleaned_data.get('adresse', '').strip()
        if not adresse:
            raise ValidationError("L'adresse est obligatoire pour la livraison.")
        return adresse