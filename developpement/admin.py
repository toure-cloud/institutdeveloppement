from django.contrib import admin
from .models import  TeamMember,Partenaire,Activite
from .models import Expertise
from django.utils.html import format_html
from .models import Inscription
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import Formation, UE, ECUE


class ECUEInline(admin.TabularInline):
    model = ECUE
    extra = 1  # Nombre de lignes vides à afficher par défaut


class UEAdmin(admin.ModelAdmin):
    list_display = ("nom", "code")
    search_fields = ("nom", "code")
    inlines = [ECUEInline]


class FormationAdmin(admin.ModelAdmin):
    list_display = ("nom", "duree", "cout")
    search_fields = ("nom",)
    filter_horizontal = ("ues",)  # Pour une meilleure sélection ManyToMany


admin.site.register(Formation, FormationAdmin)
admin.site.register(UE, UEAdmin)
admin.site.register(ECUE)




@admin.register(Expertise)
class ExpertiseAdmin(admin.ModelAdmin):
    search_fields = ['name']

@admin.register(Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'category', 'website')
    list_filter = ('category',)
    search_fields = ('nom', 'description')


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    # Configuration de l'affichage de la liste
    list_display = (
        'photo_thumbnail',
        'full_name',
        'get_category_display',
        'expertises_list',
        'social_links',
        'created_at'
    )
    list_display_links = ('full_name',)
    list_filter = (
        'category',
        ('expertises', admin.RelatedOnlyFieldListFilter),
        'created_at'
    )
    date_hierarchy = 'created_at'
    filter_horizontal = ('expertises',)
    search_fields = (
        'first_name',
        'last_name',
        'title',
        'expertises__name'
    )
    ordering = ('-created_at',)
    list_per_page = 25
    save_on_top = True

    # Configuration du formulaire d'édition
    fieldsets = (
        (_('Informations personnelles'), {
            'fields': (
                'first_name',
                'last_name',
                'slug',
                'title',
                'bio'
            )
        }),
        (_('Médias'), {
            'fields': ('photo',)
        }),
        (_('Catégorisation'), {
            'fields': (
                'category',
                'expertises',
                'display_order'
            )
        }),
        (_('Réseaux sociaux'), {
            'fields': (
                'linkedin_url',
                'researchgate_url'
            )
        }),
        (_('Métadonnées'), {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'social_links'
    )

    prepopulated_fields = {'slug': ('first_name', 'last_name')}
    autocomplete_fields = ('expertises',)

    # Méthodes personnalisées
    @admin.display(description=_('Photo'))
    def photo_thumbnail(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;">',
                obj.photo.url
            )
        return '-'
    
    @admin.display(description=_('Nom complet'))
    def full_name(self, obj):
        return obj.full_name
    
    @admin.display(description=_('Expertises'))
    def expertises_list(self, obj):
        return ", ".join([e.name for e in obj.expertises.all()])
    
    @admin.display(description=_('Liens sociaux'))
    def social_links(self, obj):
        links = []
        if obj.linkedin_url:
            links.append(
                f'<a href="{obj.linkedin_url}" target="_blank">LinkedIn</a>'
            )
        if obj.researchgate_url:
            links.append(
                f'<a href="{obj.researchgate_url}" target="_blank">ResearchGate</a>'
            )
        return format_html(' | '.join(links)) if links else '-'

    # Optimisations des performances
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('expertises')

    # Actions personnalisées
    actions = ['make_featured', 'export_as_json']
    
    @admin.action(description=_("Marquer comme vedette"))
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
    
    # Configuration de la vue détail
    def view_on_site(self, obj):
        return reverse('team-member-detail', kwargs={'slug': obj.slug})



@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date')
    list_filter = ('category', 'date')
    search_fields = ('title', 'short_description')
    readonly_fields = ('image_preview',)

    fieldsets = (
        (None, {
            'fields': ('title', 'short_description', 'category', 'date', 'image')
        }),
        ('Aperçu', {
            'fields': ('image_preview',),
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 150px; max-width: 300px;" />'
        return "Pas d'image"
    image_preview.allow_tags = True
    image_preview.short_description = 'Aperçu de l’image'


class InscriptionAdmin(admin.ModelAdmin):
    exclude = ('user',)
    list_display = ('nom', 'prenom', 'email', 'formation', 'statut', 'date_inscription')
    list_filter = ('statut', 'formation', 'sexe')
    search_fields = ('nom', 'prenom', 'email', 'cni', 'cmu')
    readonly_fields = ('date_inscription',)
    fieldsets = (
        ('Informations Personnelles', {
            'fields': ('nom', 'prenom', 'sexe', 'date_naissance', 'lieu_naissance')
        }),
        ('Coordonnées', {
            'fields': ('email', 'email_confirmation', 'telephone')
        }),
        ('Identifiants', {
            'fields': ('cmu', 'cni')
        }),
        ('Baccalauréat', {
            'fields': ('serie_bac', 'annee_obtentionbac', 'mention_bac', 'numero_bac', 'ecole_diplomebac')
        }),
        ('Licence', {
            'fields': ('licence', 'annee_obtentionlicence')
        }),
        ('Documents', {
            'fields': ('photo_identite', 'bac_scan', 'diplome_scan', 'extrait_naissance')
        }),
        ('Statut', {
            'fields': ('formation', 'statut', 'date_inscription')
        }),
    )
    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user  # Assigne automatiquement l'utilisateur courant
        super().save_model(request, obj, form, change)

admin.site.register(Inscription, InscriptionAdmin)
