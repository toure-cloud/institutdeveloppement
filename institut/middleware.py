# institut/middleware.py
class SubdomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extraire le sous-domaine
        host = request.get_host().split(":")[0]
        subdomain = host.split(".")[0]

        # Définir l'URLconf approprié basé sur le sous-domaine
        from django.conf import settings

        if subdomain in settings.SUBDOMAIN_URLCONFS:
            request.urlconf = settings.SUBDOMAIN_URLCONFS[subdomain]
        else:
            request.urlconf = settings.SUBDOMAIN_URLCONFS[None]

        response = self.get_response(request)
        return response
