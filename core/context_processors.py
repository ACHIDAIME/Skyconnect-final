from django.db import models
from .models import Logo,Categorie
def logo_context(request):
    logo = Logo.objects.first()
    return {'logo': logo}

def menu_categories(request):
    equipement = Categorie.objects.filter(nom__iexact="Equipement").first()
    accessoire = Categorie.objects.filter(nom__iexact="Accessoire").first()
    return {
        'equipement_categories': equipement.sous_categories.all() if equipement else [],
        'accessoire_categories': accessoire.sous_categories.all() if accessoire else [],
    }
from .models import Panier, PanierItem

def panier_count(request):
    if request.user.is_authenticated:
        panier, created = Panier.objects.get_or_create(user=request.user)
        count = PanierItem.objects.filter(panier=panier).aggregate(total=models.Sum('quantite'))['total'] or 0
        return {'panier_count': count}
    return {'panier_count': 0}