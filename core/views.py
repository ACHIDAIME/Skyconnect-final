from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db import models
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.urls import reverse
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt

import os

from .forms import MessageContactForm, InfosClientForm
from .models import (
    Actualite, QuickBlock, Faq, Forfait, Produit, Panier, PanierItem,
    Categorie, SousCategorie, ZoneCouverture, Commune, Agence,
    DemandeSouscription, Order, OrderItem, Logo, WifiTicketType, WifiTicket
)

from google.oauth2 import id_token
from google.auth.transport import requests

# ===== AUTHENTIFICATION - GOOGLE OAUTH UNIQUEMENT =====


@csrf_exempt
def auth_receiver(request):
    """
    Google calls this URL after the user has signed in with their Google account.
    Creates or updates the user in Django and logs them in automatically.
    """
    print('Google OAuth: Receiving token from Google Sign-In...')
    token = request.POST['credential']
    
    client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    if not client_id:
        print("ERROR: GOOGLE_OAUTH_CLIENT_ID not found in environment variables")
        return HttpResponse(status=500)

    try:
        user_data = id_token.verify_oauth2_token(
            token, requests.Request(), client_id
        )
    except ValueError as e:
        print(f"ERROR: Token verification failed: {e}")
        return HttpResponse(status=403)

    # Extraire les informations de l'utilisateur Google
    email = user_data.get('email')
    name = user_data.get('name', '')
    first_name = user_data.get('given_name', '')
    last_name = user_data.get('family_name', '')

    if not email:
        print("ERROR: No email in user_data")
        return HttpResponse(status=400)

    # Chercher ou créer l'utilisateur Django
    user = User.objects.filter(email=email).first()
    if not user:
        # Créer un nouvel utilisateur à partir des données Google
        user = User.objects.create_user(
            username=email.split('@')[0] + str(User.objects.count() + 1),
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        user.set_unusable_password()
        user.save()
        print(f"✓ New user created: {user.username}")
    else:
        print(f"✓ Existing user logged in: {user.username}")

    # Authentifier l'utilisateur dans Django
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    # Stocker les données Google dans la session
    request.session['user_data'] = user_data

    # Rediriger vers la page d'accueil
    return redirect('accueil')


def sign_out(request):
    """Logout the user and clear session data."""
    from django.contrib.auth import logout
    logout(request)
    if 'user_data' in request.session:
        del request.session['user_data']
    return redirect('account_login')


def accueil(request):
    # Nettoyer le flag de session si présent
    if 'just_logged_in' in request.session:
        del request.session['just_logged_in']

    quick_blocks = QuickBlock.objects.all().order_by('ordre')
    latest_news = Actualite.objects.order_by('-date_pub')[:6]
    bons_plans_forfaits = Forfait.objects.filter(is_bon_plan=True)[:3]
    bons_plans_equipements = Produit.objects.filter(is_bon_plan=True, quantite__gt=0)[:3] 
    regions = ZoneCouverture.objects.all()
    communes = Commune.objects.all()
    return render(request, 'core/accueil.html', {
        'quick_blocks': quick_blocks,
        'latest_news': latest_news,
        'bons_plans_forfaits': bons_plans_forfaits,
        'bons_plans_equipements': bons_plans_equipements,
        "regions": regions,
        "communes": communes,
    })

def blog(request):
    actualites = Actualite.objects.all().order_by('-date_pub')
    return render(request, 'core/blog.html', {'actualites': actualites})

def zone_couverture(request):
    from .models import ZoneCouverture
    zones = ZoneCouverture.objects.prefetch_related('communes').all()
    return render(request, 'core/zone_couverture.html', {'zones': zones})

def contact(request):
    if request.method == 'POST':
        form = MessageContactForm(request.POST)
        if form.is_valid():
            message = form.save()
            # Envoi d’un email à l’admin
            send_mail(
                subject=f"Nouveau message de contact : {message.sujet}",
                message=f"Nom : {message.nom}\nEmail : {message.email}\nMessage :\n{message.message}",
                from_email=None,
                recipient_list=['noc@skyconnect-sa.com'],  # Mets ici l’email à notifier
                fail_silently=False,
            )
            messages.success(request, "Votre message a bien été envoyé !")
            return redirect('contact')
    else:
        form = MessageContactForm()
    return render(request, 'core/contact.html', {'form': form})

def qui_sommes_nous(request):
    return render(request, 'core/qui_sommes_nous.html')

def mentions_legales(request):
    return render(request, 'core/mentions_legales.html')

def faq(request):
    faqs = Faq.objects.prefetch_related('steps__images').order_by('ordre')
    return render(request, 'core/faq.html', {'faqs': faqs})


@login_required
def ajouter_au_panier(request, produit_id):
    """
    Ajoute une quantité au panier de l'utilisateur.
    Accepte q en querystring (GET) ou POST.
    Valide et clamp la quantité entre 1 et produit.quantite.
    Retourne {'success': True, 'panier_count': <int>} ou {'success': False, 'error': ...}
    """
    produit = get_object_or_404(Produit, pk=produit_id)

    # Récupère la quantité demandée (GET ?q= ou POST 'q')
    q = request.GET.get('q') or request.POST.get('q') or '1'
    try:
        q = int(q)
    except (ValueError, TypeError):
        q = 1
    if q < 1:
        q = 1

    if produit.quantite <= 0:
        return JsonResponse({'success': False, 'error': "Produit indisponible."}, status=400)

    q = min(q, produit.quantite)

    panier, _ = Panier.objects.get_or_create(user=request.user)
    panier_item, created = PanierItem.objects.get_or_create(panier=panier, produit=produit, defaults={'quantite': q})
    if not created:
        # additionne en respectant le stock max
        new_qty = min(produit.quantite, panier_item.quantite + q)
        panier_item.quantite = new_qty
        panier_item.save(update_fields=['quantite'])

    # Compte total d'articles (somme des quantités)
    total_q = PanierItem.objects.filter(panier=panier).aggregate(total=Sum('quantite'))['total'] or 0

    return JsonResponse({'success': True, 'panier_count': int(total_q)})

@login_required
def retirer_du_panier(request, item_id):
    PanierItem.objects.filter(id=item_id, panier__user=request.user).delete()
    return redirect('panier')

@login_required
def changer_quantite(request, item_id):
    item = get_object_or_404(PanierItem, id=item_id, panier__user=request.user)
    produit = item.produit
    if request.method == "POST":
        quantite = int(request.POST.get("quantite", 1))
        if quantite > produit.quantite:
            quantite = produit.quantite
        if quantite > 0:
            item.quantite = quantite
            item.save()
        else:
            item.delete()
    return redirect('panier')

@login_required
def vider_panier(request):
    panier, _ = Panier.objects.get_or_create(user=request.user)
    panier.items.all().delete()
    return redirect('panier')

@login_required
def voir_panier(request):
    panier, created = Panier.objects.get_or_create(user=request.user)
    items = []
    for item in panier.items.all():
        items.append({
            'id': item.id,
            'produit': item.produit,
            'quantite': item.quantite,
            'total_ligne': item.produit.prix_ttc * item.quantite,
        })
    total = sum(i['total_ligne'] for i in items)
    return render(request, 'core/panier.html', {'items': items, 'total': total, 'panier': panier})

@login_required
def mes_commandes(request):
    """Affiche l'historique des commandes de l'utilisateur."""
    commandes = Order.objects.filter(
        models.Q(client=request.user) | 
        (models.Q(client__isnull=True) & models.Q(email=request.user.email))
    ).order_by('-date_commande')
    return render(request, 'core/mes_commandes.html', {'commandes': commandes})

def forfaits(request):
    forfaits = Forfait.objects.all()
    regions = ZoneCouverture.objects.all()  # On récupère toutes les régions
    communes = Commune.objects.all()
    return render(request, "core/forfaits.html", {
        "forfaits": forfaits,
        "regions": regions,
        "communes": communes,
    })
# Exemple dans views.py
def equipements(request):
    categories = Categorie.objects.prefetch_related('sous_categories__produits').all()
    return render(request, 'core/equipements.html', {'categories': categories})

def sous_categorie_detail(request, id):
    sous_categorie = SousCategorie.objects.prefetch_related('produits').get(id=id)
    produits = sous_categorie.produits.all()
    return render(request, 'core/sous_categorie_detail.html', {
        'sous_categorie': sous_categorie,
        'produits': produits,
    })

def menu_categories(request):
    equipement_categories = Categorie.objects.filter(nom__iexact="Équipement").first()
    accessoire_categories = Categorie.objects.filter(nom__iexact="Accessoire").first()
    return {
        'equipement_categories': equipement_categories.sous_categories.all() if equipement_categories else [],
        'accessoire_categories': accessoire_categories.sous_categories.all() if accessoire_categories else [],
    }

def produit_detail(request, id):
    produit = Produit.objects.get(id=id)
    # Traitement des caractéristiques
    caracteristiques = []
    if produit.caracteristiques:
        for ligne in produit.caracteristiques.splitlines():
            if ':' in ligne:
                nom, valeur = ligne.split(':', 1)
                caracteristiques.append((nom.strip(), valeur.strip()))
            else:
                caracteristiques.append((ligne.strip(), ''))
    return render(request, 'core/produit_detail.html', {
        'produit': produit,
        'caracteristiques': caracteristiques,
    })


from django.shortcuts import render, redirect
from .models import Forfait, ZoneCouverture, Commune

from django.shortcuts import render, redirect
from .models import Forfait, ZoneCouverture, Commune

def souscription_form(request, forfait_id):
    forfait = get_object_or_404(Forfait, id=forfait_id)
    if request.method == "POST":
        # accepte region OR region_id pour compatibilité
        region_id = request.POST.get("region") or request.POST.get("region_id")
        commune_id = request.POST.get("commune") or request.POST.get("commune_id")
        zone = ZoneCouverture.objects.filter(id=region_id).first() if region_id else None
        commune = Commune.objects.filter(id=commune_id, zone_id=region_id).first() if commune_id else None
        # Afficher "zone non couverte" uniquement pour FO
        if (not zone or not commune) and forfait.type == "FO":
            autres_forfaits = Forfait.objects.filter(type="FH")
            return render(request, "core/souscription_non_couverte.html", {
                "autres_forfaits": autres_forfaits,
                "forfait": forfait,
            })
        if zone and commune:
            # rendre le formulaire avec les context utiles (regions/communes si nécessaires)
            regions = ZoneCouverture.objects.all()
            communes = Commune.objects.all()
            return render(request, "core/souscription_form.html", {
                "forfait": forfait,
                "zone": zone,
                "commune": commune,
                "regions": regions,
                "communes": communes,
            })
      # GET
    regions = ZoneCouverture.objects.all()
    communes = Commune.objects.all()
    return render(request, "core/souscription_form.html", {
        "forfait": forfait,
        "regions": regions,
        "communes": communes,
    })
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import DemandeSouscription
from django.core.mail import send_mail

# ...existing code...
def finaliser_souscription(request):
    if request.method != "POST":
        return redirect("forfaits")

    forfait_id = (request.POST.get("forfait_id") or "").strip()
    region_id = (request.POST.get("region_id") or request.POST.get("region") or "").strip()
    commune_id = (request.POST.get("commune_id") or request.POST.get("commune") or "").strip()
    nom = (request.POST.get("nom") or "").strip()
    telephone = (request.POST.get("telephone") or "").strip()
    email = (request.POST.get("email") or "").strip()

    erreurs = []

    # Vérifications basiques
    if not all([forfait_id, region_id, commune_id, nom, telephone]):
        erreurs.append("Tous les champs obligatoires doivent être remplis.")

    if forfait_id and not forfait_id.isdigit():
        erreurs.append("Identifiant de forfait invalide.")
    if region_id and not region_id.isdigit():
        erreurs.append("Identifiant de région invalide.")
    if commune_id and not commune_id.isdigit():
        erreurs.append("Identifiant de commune invalide.")

    if erreurs:
        regions = ZoneCouverture.objects.all()
        communes = Commune.objects.all()
        forfait = Forfait.objects.filter(id=int(forfait_id)).first() if forfait_id.isdigit() else None
        return render(request, "core/souscription_form.html", {
            "erreurs": erreurs,
            "forfait": forfait,
            "regions": regions,
            "communes": communes,
        })

    # Récupération sécurisée des objets
    try:
        forfait = Forfait.objects.get(id=int(forfait_id))
    except (Forfait.DoesNotExist, ValueError):
        erreurs.append("Forfait introuvable.")

    try:
        zone = ZoneCouverture.objects.get(id=int(region_id))
    except (ZoneCouverture.DoesNotExist, ValueError):
        erreurs.append("Zone introuvable.")

    try:
        commune = Commune.objects.get(id=int(commune_id), zone_id=int(region_id))
    except (Commune.DoesNotExist, ValueError):
        erreurs.append("Commune introuvable pour la région sélectionnée.")

    if erreurs:
        regions = ZoneCouverture.objects.all()
        communes = Commune.objects.all()
        return render(request, "core/souscription_form.html", {
            "erreurs": erreurs,
            "forfait": forfait if 'forfait' in locals() else None,
            "regions": regions,
            "communes": communes,
        })

    # Validation téléphone et email
    pattern = r'^(61|62|65|66)[0-9]{7}$'
    if not re.match(pattern, telephone):
        erreurs.append("Numéro de téléphone guinéen invalide.")
    if email:
        try:
            validate_email(email)
        except ValidationError:
            erreurs.append("Adresse email invalide.")

    if erreurs:
        return render(request, "core/souscription_form.html", {
            "erreurs": erreurs,
            "forfait": forfait,
            "zone": zone,
            "commune": commune,
        })

    # Enregistrement
    demande = DemandeSouscription.objects.create(
        nom=nom,
        telephone=telephone,
        email=email,
        forfait=forfait,
        zone=zone,
        commune=commune,
    )

    send_mail(
        subject=f"Nouvelle souscription : {forfait.nom}",
        message=f"Nom : {nom}\nTéléphone : {telephone}\nEmail : {email}\nForfait : {forfait.nom}\nRégion : {zone.region}\nCommune : {commune.nom}",
        from_email=None,
        recipient_list=os.environ['EMAIL_COMMERCIAL'],
        fail_silently=False,
    )

    return render(request, "core/souscription_confirmation.html", {
        "nom": nom,
        "forfait": forfait,
    })

# ...existing code...
from django.utils.crypto import get_random_string

@login_required
def commande_infos_client(request):
    panier, _ = Panier.objects.get_or_create(user=request.user)
    items = PanierItem.objects.filter(panier=panier)
    total = sum(item.produit.prix_ttc * item.quantite for item in items)

    regions = ZoneCouverture.objects.all()
    communes = Commune.objects.all()

    if request.method == "POST":
        form = InfosClientForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # récupérer region et commune sélectionnées
            region_id = request.POST.get('region_id')
            commune_id = request.POST.get('commune_id')
            region_obj = None
            commune_obj = None
            # si livraison, region+commune requis
            if data.get('choix_retrait') == 'livraison':
                if not region_id:
                    form.add_error(None, "Veuillez sélectionner la ville (région).")
                if not commune_id:
                    form.add_error(None, "Veuillez sélectionner la commune.")
            # valider existence en base si fournis
            if region_id:
                try:
                    region_obj = ZoneCouverture.objects.get(id=int(region_id))
                except (ZoneCouverture.DoesNotExist, ValueError):
                    form.add_error(None, "Ville invalide.")
            if commune_id:
                try:
                    commune_obj = Commune.objects.get(id=int(commune_id))
                except (Commune.DoesNotExist, ValueError):
                    form.add_error(None, "Commune invalide.")

            if not form.errors:
                # stocker infos + libellés région/commune
                data['region_id'] = region_obj.id if region_obj else None
                data['region'] = region_obj.region if region_obj else None
                data['commune_id'] = commune_obj.id if commune_obj else None
                data['commune'] = commune_obj.nom if commune_obj else None
                # adresse détaillée déjà dans data['adresse']
                request.session['commande_infos'] = data
                return redirect('commande_confirmation')
    else:
        form = InfosClientForm()

    return render(request, "core/commande_infos_client.html", {
        "form": form,
        "items": items,
        "total": total,
        "regions": regions,
        "communes": communes,
    })

from django.db import transaction
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.utils import timezone

@login_required
def commande_confirmation(request):
    # Récupération du panier et vérification
    panier, _ = Panier.objects.get_or_create(user=request.user)
    items = PanierItem.objects.filter(panier=panier)
    total = sum(item.produit.prix_ttc * item.quantite for item in items)
    infos = request.session.get('commande_infos')
    
    if not infos:
        return redirect('commande_infos_client')

    erreurs = []
    agences = Agence.objects.all() if infos.get('choix_retrait') == 'agence' else None

    if request.method == "POST":
        try:
            with transaction.atomic():
                # Génération référence
                date_str = timezone.now().strftime('%Y%m%d')
                count = Order.objects.filter(
                    date_commande__date=timezone.now().date()
                ).count() + 1
                reference = f"CMD-{date_str}-{count:04d}"

                # Création commande
                order = Order.objects.create(
                    reference=reference,
                    client=request.user if request.user.is_authenticated else None,
                    nom=infos['nom'],
                    email=request.user.email if request.user.is_authenticated else infos['email'],
                    telephone=infos['telephone'],
                    mode_reception=infos['choix_retrait'],
                    agence_id=request.POST.get('agence_id'),
                    adresse_livraison=infos.get('adresse'),
                    commune_id=infos.get('commune_id'),
                    montant_total=total,
                    statut='en_attente'  # Statut initial
                )

                # Création items sans toucher au stock
                for item in items:
                    OrderItem.objects.create(
                        commande=order,
                        produit=item.produit,
                        quantite=item.quantite,
                        prix_unitaire=item.produit.prix_ttc,
                        total_ligne=item.produit.prix_ttc * item.quantite
                    )

                # Emails
                context = {
                    'order': order,
                    'items': order.items.all(),
                    'infos': infos,
                }
                
                if order.mode_reception == 'agence':
                    envoyer_email_avec_logo(
                        request=request,
                        sujet=f'Confirmation de votre commande {order.reference}',
                        template_html='emails/commande_retrait_agence.html',
                        template_txt='emails/commande_retrait_agence.txt',
                        context=context,
                        destinataire=order.email
                    )
                else:
                    envoyer_email_avec_logo(
                        request=request,
                        sujet=f'Confirmation de votre commande {order.reference}',
                        template_html='emails/commande_livraison.html',
                        template_txt='emails/commande_livraison.txt',
                        context=context,
                        destinataire=order.email
                    )

                # Vider panier
                panier.items.all().delete()
                if 'commande_infos' in request.session:
                    del request.session['commande_infos']

                request.session['derniere_commande'] = {
                    'reference': order.reference,
                    'total': float(order.montant_total),
                    'mode': order.mode_reception,
                    'agence_nom': order.agence.nom if order.agence else None,
                }

                return redirect('commande_succes')

        except Exception as e:
            print(f"Erreur : {str(e)}")
            erreurs.append(f"Erreur : {str(e)}")
            return render(request, "core/commande_confirmation.html", {
                "infos": infos,
                "items": items,
                "total": total,
                "agences": agences,
                "erreurs": erreurs,
            })

    return render(request, "core/commande_confirmation.html", {
        "infos": infos,
        "items": items,
        "total": total,
        "agences": agences,
        "erreurs": erreurs,
    })
def commande_succes(request):
    # Ici tu peux afficher le reçu, les instructions, etc.
    return render(request, "core/commande_succes.html")

@login_required
def commande_detail(request, order_id):
    """Affiche les détails d'une commande."""
    commande = get_object_or_404(Order, id=order_id, client=request.user)
    items = OrderItem.objects.filter(commande=commande)
    return render(request, 'core/commande_detail.html', {
        'commande': commande,
        'items': items,
    })

@login_required
def changer_statut_commande(request, order_id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
        
    order = get_object_or_404(Order, id=order_id)
    nouveau_statut = request.POST.get('statut')
    
    if nouveau_statut not in [x[0] for x in Order.STATUT_CHOICES]:
        return JsonResponse({'error': 'Statut invalide'}, status=400)
        
    try:
        old_statut = order.statut
        order.statut = nouveau_statut
        order.save()
        
        message = f"Statut changé de {old_statut} à {nouveau_statut}"
        if nouveau_statut in ('confirme', 'en_preparation', 'pret'):
            message += " (stock débité)"
        elif nouveau_statut == 'annule':
            message += " (stock restauré)"
            
        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from email.mime.image import MIMEImage
from django.conf import settings
import os
from .models import Logo  # Assurez-vous que c'est le bon modèle

from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
from django.conf import settings
import os

def envoyer_email_avec_logo(request, sujet, template_html, template_txt, context, destinataire):
    # Récupérer le dernier logo
    logo = Logo.objects.last()
    
    # Créer le message
    msg = EmailMultiAlternatives(
        subject=sujet,
        body=render_to_string(template_txt, context),
        from_email=None,
        to=[destinataire]
    )
    
    # Si un logo existe, l'intégrer dans l'email
    if logo and logo.image:
        # Lire le fichier image
        image_path = logo.image.path
        with open(image_path, 'rb') as f:
            logo_data = f.read()
        
        # Créer l'image attachée avec un Content-ID
        logo_img = MIMEImage(logo_data)
        logo_img.add_header('Content-ID', '<logo>')
        msg.attach(logo_img)
        
        # Ajouter l'URL CID au contexte
        context['logo_cid'] = 'cid:logo'
    
    # Ajouter la version HTML
    html_content = render_to_string(template_html, context)
    msg.attach_alternative(html_content, "text/html")
    
    # Envoyer
    msg.send()


def tickets(request):
    """Page d'achat de tickets WiFi hotspot.

    Affiche les différents types de tickets disponibles (1h, 2h, etc.)
    et permet aux utilisateurs d'acheter des tickets.
    """
    from .models import WifiTicketType

    # Récupérer tous les types de tickets actifs
    ticket_types = WifiTicketType.objects.filter(is_active=True)

    context = {
        'ticket_types': ticket_types,
    }

    return render(request, 'core/tickets.html', context)