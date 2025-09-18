# administrateur/utils.py
from urllib.parse import urlparse
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse


def is_safe_url(url, allowed_hosts=None):
    """
    Return True if the url is a safe redirection (i.e. it doesn't point to
    a different host).
    """
    if not url:
        return False

    if allowed_hosts is None:
        allowed_hosts = set()

    # Ajouter le host actuel aux hôtes autorisés
    allowed_hosts.add(settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "")

    try:
        url_info = urlparse(url)
        # Vérifier que le schéma est http ou https
        if url_info.scheme not in ("http", "https"):
            return False
        # Vérifier que l'hôte est autorisé
        if url_info.netloc and url_info.netloc not in allowed_hosts:
            return False
        return True
    except ValueError:
        return False
