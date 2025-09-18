from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

def role_required(role):
    """Vérifie si l'utilisateur appartient à un groupe spécifique ou est superutilisateur."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            print(f"Utilisateur : {request.user}")  # Debugging
            print(f"Authentifié : {request.user.is_authenticated}")  # Vérification
            print(f"Superutilisateur : {request.user.is_superuser}")  # Vérification superuser
            print(f"Groupes : {list(request.user.groups.values_list('name', flat=True))}")  # Liste des groupes

            if not request.user.is_authenticated:
                return redirect('login')  # Redirige vers la page de connexion
            
            # Autoriser les superutilisateurs
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if not request.user.groups.filter(name=role).exists():
                return HttpResponseForbidden("Accès refusé. Vous n'avez pas les droits nécessaires.")  # 403 Forbidden

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
