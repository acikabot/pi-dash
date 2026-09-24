"""Push a short message to ntfy, the same way the updater does."""

from __future__ import annotations

import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


def send(title: str, message: str, *, priority: str = "default", tags: str = "") -> bool:
    """True when it went out. A dashboard that can't notify still works, so never raise."""
    url = settings.PIDASH_NTFY_URL
    if not url:
        return False
    request = urllib.request.Request(url, data=message.encode("utf-8"), method="POST")
    request.add_header("Title", title)
    request.add_header("Priority", priority)
    if tags:
        request.add_header("Tags", tags)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 - fixed config
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        logger.warning("Could not reach ntfy: %s", error)
        return False
