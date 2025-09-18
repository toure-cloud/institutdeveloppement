from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .views import (
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView
)
urlpatterns = [
    # === Pages publiques ===
    path("", views.home, name="home"),
    path("formation/", views.page_view, {"page_name": "formation"}, name="formation"),
    path("contact/", views.page_view, {"page_name": "contact"}, name="contact"),
    path("activites/", views.activite, name="activite"),
    path("activites/<int:id>/", views.activite_detail, name="activite_detail"),
    path(
        "presentation/",
        views.page_view,
        {"page_name": "presentation"},
        name="presentation",
    ),
    path("travaux/", views.page_view, {"page_name": "travaux"}, name="travaux"),
    path(
        "inscription/",
        views.page_view,
        {"page_name": "inscription"},
        name="inscription",
    ),
    path("programme-formation/", views.details_programme, name="details_programme"),
    path("maquette-pedagogique/", views.details_maquette, name="details_maquette"),
    # === Authentification générique ===
    path("accounts/login/", views.GenericLoginView.as_view(), name="login"),
    path("accounts/logout/", views.custom_logout_view, name="logout"),
    path("password-reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    # === Espace Candidat ===
    path("candidat/login/", views.candidat_login_page, name="candidat_login_page"),
    path("candidat/logout/", views.candidat_logout, name="candidat_logout"),
    path(
        "candidat/inscription/<str:formation_type>/",
        views.inscription_formation,
        name="inscription_formation",
    ),
    path("candidat/espace/", views.espace_candidat, name="espace_candidat"),
    path("candidat/modifier-profil/", views.modifier_profil, name="modifier_profil"),
    path(
        "candidat/modifier-motdepasse/", views.password_change, name="password_change"
    ),
    path("candidat/documents/", views.gerer_documents, name="gerer_documents"),
    path(
        "candidat/details-formation/", views.details_formation, name="details_formation"
    ),
    # === Espace Admin ===
    path("admin/login/", views.admin_login_page, name="admin_login_page"),
    path("admin/logout/", views.admin_logout, name="admin_logout"),
    path("admin/dashboard/", views.dashboard, name="dashboard"),
    # === API ===
    path(
        "api/",
        include(
            [
                path(
                    "team-members/<slug:slug>/",
                    views.TeamMemberAPIView.as_view(),
                    name="team-member-detail",
                ),
            ]
        ),
    ),
]

# Gestion des fichiers médias en mode debug
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
