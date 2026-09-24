"""Values every page needs: the navigation and which host this is."""

import socket

from pidash.core.registry import registry


def pidash(request):
    return {
        "menu": registry.menu(),
        "navbar_panels": registry.panels("navbar"),
        "hostname": socket.gethostname(),
    }
