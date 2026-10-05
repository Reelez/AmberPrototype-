import logging
import threading

from django.conf import settings
from django.db import connection

from notificaciones.utils import send_web_push_notification

logger = logging.getLogger(__name__)


def _dispatch(titulo, mensaje, url):
    try:
        return send_web_push_notification(titulo, mensaje, url)
    except Exception:
        logger.exception("Web Push broadcast failed")


def _dispatch_in_thread(titulo, mensaje, url):
    try:
        _dispatch(titulo, mensaje, url)
    finally:
        # Each thread opens its own DB connection; release it when the thread ends.
        connection.close()


def enviar_web_push(titulo, mensaje, url):
    """Broadcast a Web Push message.

    By default the dispatch runs in a daemon thread so the HTTP request is not
    blocked (RF5). With settings.WEBPUSH_ASYNC = False it runs synchronously
    and returns the summary dict (used in tests).
    """
    if getattr(settings, "WEBPUSH_ASYNC", True):
        threading.Thread(
            target=_dispatch_in_thread, args=(titulo, mensaje, url), daemon=True
        ).start()
        return None
    return _dispatch(titulo, mensaje, url)
