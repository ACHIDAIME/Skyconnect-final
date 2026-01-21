from django.urls import path,include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Pages principales
    path('', views.accueil, name='accueil'),
    path('contact/', views.contact, name='contact'),
    path('qui-sommes-nous/', views.qui_sommes_nous, name='qui_sommes_nous'),
    path('zone-couverture/', views.zone_couverture, name='zone_couverture'),
    path('blog/', views.blog, name='blog'),
    path('mentions-legales/', views.mentions_legales, name='mentions_legales'),
    path('faq/', views.faq, name='faq'),

    # Panier
    path('panier/', views.voir_panier, name='panier'),
    path('panier/ajouter/<int:produit_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/retirer/<int:item_id>/', views.retirer_du_panier, name='retirer_du_panier'),
    path('panier/changer/<int:item_id>/', views.changer_quantite, name='changer_quantite'),
    path('panier/vider/', views.vider_panier, name='vider_panier'),

    # Produits
    path('forfaits/', views.forfaits, name='forfaits'),
    path('equipements/', views.equipements, name='equipements'),
    path('sous-categorie/<int:id>/', views.sous_categorie_detail, name='sous_categorie_detail'),
    path('produit/<int:id>/', views.produit_detail, name='produit_detail'),

    # Souscription
    path('souscription/<int:forfait_id>/', views.souscription_form, name='souscription_form'),
    path('finaliser-souscription/', views.finaliser_souscription, name='finaliser_souscription'),

    # Commande
    path('commande/infos-client/', views.commande_infos_client, name='commande_infos_client'),
    path('commande/confirmation/', views.commande_confirmation, name='commande_confirmation'),
    path('commande/succes/', views.commande_succes, name='commande_succes'),

    # Authentification (Google OAuth uniquement)
    path('sign-out', views.sign_out, name='sign_out'),
    path('auth-receiver', views.auth_receiver, name='auth_receiver'),
    path('tickets/', views.tickets, name='tickets'),
    path('commandes/', views.mes_commandes, name='mes_commandes'),
    path('commande/<int:order_id>/', views.commande_detail, name='commande_detail'),
]