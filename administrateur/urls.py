from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Dashboard et authentification
    path("dashboard/", views.dashboard, name="admin_dashboard"),
    path("admin/login/", views.admin_login_page, name="admin_login_page"),
    path("admin/creer-compte/", views.creer_compte_admin, name="creer_compte_admin"),
    # Gestion des inscriptions
    path("inscrits/", views.liste_inscrits, name="liste_inscrits"),
    path("inscrits/<int:pk>/details/", views.inscrit_details, name="inscrit_details"),
    path("inscrits/<int:pk>/valider/", views.valider_inscrit, name="valider_inscrit"),
    path("inscrits/<int:pk>/rejeter/", views.rejeter_inscrit, name="rejeter_inscrit"),
    path(
        "inscrits/<int:pk>/supprimer/",
        views.supprimer_inscrit,
        name="supprimer_inscrit",
    ),
    path("inscrits/exporter/", views.exporter_inscrits, name="exporter_inscrits"),
    path(
        "inscrits/<int:pk>/envoyer-email/",
        views.envoyer_email_inscrit,
        name="envoyer_email_inscrit",
    ),
    # Actions groupées
    path("valider-selection/", views.valider_selection, name="valider_selection"),
    path("supprimer-selection/", views.supprimer_selection, name="supprimer_selection"),
    # Emails
    path("envoyer-mail/", views.envoyer_mail, name="envoyer_mail"),
    path("test-email/", views.test_email_config, name="test_email"),
    # Gestion des activités
    path("activites/gestion/", views.gestion_activites, name="gestion_activites"),
    path(
        "administrateur/activites/ajouter/",
        views.ajouter_activite,
        name="ajouter_activite",
    ),
    path(
        "administrateur/activites/modifier/<int:activite_id>/",
        views.modifier_activite,
        name="modifier_activite",
    ),
    path("activites/", views.liste_activites, name="liste_activites"),
    path(
        "administrateur/activites/supprimer/<int:activite_id>/",
        views.supprimer_activite,
        name="supprimer_activite",
    ),
    path(
        "image/supprimer/<int:image_id>/",
        views.supprimer_image_activite,
        name="supprimer_image_activite",
    ),
    path(
        "administrateur/activites/detail/<int:activite_id>/",
        views.detail_activite,
        name="detail_activite",
    ),
    path("creer-compte-admin/", views.creer_compte_admin, name="creer_compte_admin"),
    path("generer-convocation/", views.generer_convocation, name="generer_convocation"),
    path("modifier-document/", views.modifier_document, name="modifier_document"),
    path("gerer-documents/", views.gerer_documents, name="gerer_documents"),
    
        path('admin/dashboard/', RedirectView.as_view(url='/administrateur/dashboard/', permanent=True)),
    path('admin/login/', RedirectView.as_view(url='/administrateur/login/', permanent=True)),
    path('admin/activites/', RedirectView.as_view(url='/administrateur/activites/', permanent=True)),
    path('admin/inscriptions/', RedirectView.as_view(url='/administrateur/inscriptions/', permanent=True)),
    path('admin/', RedirectView.as_view(url='/administrateur/dashboard/', permanent=True)),
]


