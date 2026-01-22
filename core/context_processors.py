from django.db import models
from .models import Logo, Categorie, Panier, PanierItem

def logo_context(request):
    """Retourne le logo actif ou None si aucun logo"""
    try:
        logo = Logo.objects.filter(actif=True).first() or Logo.objects.first()
        return {'logo': logo}
    except Exception as e:
        print(f"Error in logo_context: {e}")
        return {'logo': None}

def menu_categories(request):
    """Retourne les catégories d'équipement et d'accessoire avec leurs sous-catégories"""
    try:
        equipement = Categorie.objects.filter(nom__iexact="Equipement").prefetch_related('sous_categories').first()
        accessoire = Categorie.objects.filter(nom__iexact="Accessoire").prefetch_related('sous_categories').first()
        return {
            'equipement_categories': list(equipement.sous_categories.all()) if equipement else [],
            'accessoire_categories': list(accessoire.sous_categories.all()) if accessoire else [],
        }
    except Exception as e:
        print(f"Error in menu_categories: {e}")
        return {
            'equipement_categories': [],
            'accessoire_categories': [],
        }

def panier_count(request):
    """Retourne le nombre d'articles dans le panier de l'utilisateur"""
    try:
        if request.user.is_authenticated:
            panier, created = Panier.objects.get_or_create(user=request.user)
            count = PanierItem.objects.filter(panier=panier).aggregate(total=models.Sum('quantite'))['total'] or 0
            return {'panier_count': count}
    except Exception as e:
        print(f"Error in panier_count: {e}")
    
    return {'panier_count': 0}