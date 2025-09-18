import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class RedirectDebugMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if 300 <= response.status_code < 400:
            logger.debug(f"Redirection detected: {request.path} -> {response.url}")
        return response
