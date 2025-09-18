from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import HttpResponseRedirect

urlpatterns = [
    # URL d'administration Django originale (gardée pour l'admin de base)
    path("admin/", admin.site.urls),
    path("", include("developpement.urls")),
    # Redirection explicite de /admin/dashboard/ vers /administrateur/dashboard/
    path(
        "admin/dashboard/",
        lambda request: HttpResponseRedirect("/administrateur/dashboard/"),
    ),
    path("admin/administrateur/", include("administrateur.urls")),
    # Redirection de l'ancien admin root vers le login administrateur
    path("admin/", lambda request: HttpResponseRedirect("/administrateur/login/")),
    # Vos URLs personnalisées pour l'administration
    path("administrateur/", include("administrateur.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
