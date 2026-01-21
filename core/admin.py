from django.contrib import admin, messages
# Register your models here.
from .models import MessageContact, Slider, Actualite, Logo, ActualiteImage, QuickBlock, Faq, FaqStep, FaqStepImage, FaqSection, Forfait, Produit, ZoneCouverture, Commune, Categorie, SousCategorie, Agence, Order, OrderItem, WifiTicketType, WifiTicket

from django import forms
from django.core.exceptions import ValidationError
import re

from django.contrib import admin
from .models import Order, OrderItem
from .views import envoyer_email_avec_logo  # Ajout de l'import


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['produit', 'prix_unitaire', 'quantite', 'total_ligne']
    extra = 0

from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['reference', 'client', 'nom', 'montant_total', 'statut', 'mode_reception', 'date_commande']
    list_filter = ['statut', 'mode_reception', 'date_commande']
    search_fields = ['reference', 'nom', 'email']
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        if change and 'statut' in form.changed_data:
            old_status = Order.objects.get(pk=obj.pk).statut
            try:
                super().save_model(request, obj, form, change)
            except ValueError as e:
                # En cas de stock insuffisant : annuler la commande et notifier le client
                obj.statut = 'annule'
                obj.save(update_fields=['statut'])
                
                # Envoyer l'email au client
                context = {
                    'order': obj,
                    'raison': str(e)
                }
                
                try:
                    envoyer_email_avec_logo(
                        request=request,
                        sujet=f'Commande {obj.reference} annulée - Stock insuffisant',
                        template_html='emails/commande_annulation_stock.html',
                        template_txt='emails/commande_annulation_stock.txt',
                        context=context,
                        destinataire=obj.email
                    )
                    self.message_user(
                        request, 
                        f"Commande {obj.reference} annulée automatiquement (stock insuffisant). Le client a été notifié.", 
                        level=messages.WARNING
                    )
                except Exception as mail_error:
                    self.message_user(
                        request, 
                        f"Commande annulée mais erreur d'envoi email : {mail_error}", 
                        level=messages.ERROR
                    )
                return
        else:
            super().save_model(request, obj, form, change)

@admin.action(description="Confirmer les commandes sélectionnées")
def action_confirm_orders(modeladmin, request, queryset):
    for order in queryset:
        try:
            old_status = order.statut
            order.statut = 'confirme'
            order.save()
            messages.success(request, f"Commande {order.reference} confirmée.")
        except ValueError as e:
            order.statut = old_status
            order.save(update_fields=['statut'])
            messages.error(request, f"Erreur confirmation {order.reference} : {e}")
            # Restauration de l'ancien statut
@admin.action(description="Annuler les commandes sélectionnées (restaure le stock si nécessaire)")
def action_cancel_orders(modeladmin, request, queryset):
    for order in queryset:
        order.statut = 'annule'
        try:
            order.save()
            messages.success(request, f"Commande {order.reference} annulée.")
        except Exception as e:
            messages.error(request, f"Erreur annulation {order.reference} : {e}")


class InfosClientForm(forms.Form):
    nom = forms.CharField(label="Nom complet", max_length=100)
    telephone = forms.CharField(label="Téléphone", max_length=9)
    email = forms.EmailField(label="Email", required=False)
    adresse = forms.CharField(label="Adresse de livraison", widget=forms.Textarea, required=True)
    choix_retrait = forms.ChoiceField(
        label="Mode de retrait",
        choices=[('livraison', 'Livraison à domicile'), ('agence', 'Retrait en agence')],
        widget=forms.RadioSelect
    )

    def clean_telephone(self):
        tel = self.cleaned_data.get('telephone', '').strip()
        # on attend 9 chiffres (sans +224), et préfixes valides en Guinée (61,62,65,66)
        if not re.match(r'^(61|62|65|66)[0-9]{7}$', tel):
            raise ValidationError("Veuillez saisir un numéro valide")
        return tel

class ActualiteImageInline(admin.TabularInline):
    model = ActualiteImage
    extra = 3  # nombre de formulaires vides affichés par défaut
    fields = ['image', 'alt']
    # Tu peux aussi ajouter 'image' dans readonly_fields si besoin

@admin.register(Actualite)
class ActualiteAdmin(admin.ModelAdmin):
    inlines = [ActualiteImageInline]
    list_display = ('titre', 'date_pub')
    search_fields = ('titre',)


class FaqStepImageInline(admin.TabularInline):
    model = FaqStepImage
    extra = 1

class FaqStepInline(admin.StackedInline):
    model = FaqStep
    extra = 1

class FaqInline(admin.StackedInline):
    model = Faq
    extra = 1

@admin.register(FaqSection)
class FaqSectionAdmin(admin.ModelAdmin):
    inlines = [FaqInline]

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'sous_categorie', 'prix', 'quantite')
    list_filter = ('sous_categorie',)
    search_fields = ('nom',)

# Admin simple pour SousCategorie
@admin.register(SousCategorie)
class SousCategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie')
    list_filter = ('categorie',)
    search_fields = ('nom',)


# Admin simple pour Categorie
@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

admin.site.register(MessageContact)
admin.site.register(Slider)
admin.site.register(Logo)
admin.site.register(ZoneCouverture)
admin.site.register(Commune)
admin.site.register(QuickBlock)
admin.site.register(Forfait)
admin.site.register(Agence)


# Admin pour les tickets WiFi
@admin.register(WifiTicketType)
class WifiTicketTypeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'duree_heures', 'prix', 'is_active')
    list_filter = ('is_active', 'duree_heures')
    search_fields = ('nom',)
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('nom', 'description')
        }),
        ('Configuration', {
            'fields': ('duree_heures', 'prix', 'is_active')
        }),
    )


@admin.register(WifiTicket)
class WifiTicketAdmin(admin.ModelAdmin):
    list_display = ('identifiant', 'ticket_type', 'date_creation', 'date_expiration', 'is_expired')
    list_filter = ('ticket_type', 'date_creation', 'date_expiration')
    search_fields = ('identifiant', 'mot_de_passe')
    readonly_fields = ('identifiant', 'mot_de_passe', 'date_creation', 'date_expiration', 'is_expired')
    
    fieldsets = (
        ('Identifiants', {
            'fields': ('identifiant', 'mot_de_passe'),
            'description': 'Les identifiants sont générés automatiquement'
        }),
        ('Configuration', {
            'fields': ('ticket_type',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_expiration'),
            'classes': ('collapse',)
        }),
    )
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.short_description = "Expiré ?"
    is_expired.boolean = True
