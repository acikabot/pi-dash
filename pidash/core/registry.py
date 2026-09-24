"""What the modules add to the dashboard.

Modules never import each other. They register what they contribute here in their
``ready()``, and the navigation, the overview and the action buttons are assembled from
whatever is installed — so switching a module off removes its pages and its traces.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MenuItem:
    key: str
    label: str
    url_name: str
    icon: str = "circle"
    order: int = 100


@dataclass(frozen=True)
class ServiceAction:
    """A button shown on a service's card, contributed by a module."""

    key: str
    label: str
    url_name: str  # reversed with the service id
    icon: str = "play"
    style: str = "outline-secondary"
    order: int = 100
    #: Only shown when this returns True for the service.
    applies_to: Callable[[Any], bool] = lambda service: True


@dataclass(frozen=True)
class Panel:
    order: int
    template: str
    context: Callable | None = None


class Registry:
    def __init__(self) -> None:
        self._menu: list[MenuItem] = []
        self._actions: list[ServiceAction] = []
        self._panels: dict[str, list] = {}

    # -- navigation ----------------------------------------------------------------
    def add_menu_item(self, item: MenuItem) -> None:
        self._menu = [m for m in self._menu if m.key != item.key]
        self._menu.append(item)

    def menu(self) -> list[MenuItem]:
        return sorted(self._menu, key=lambda m: (m.order, m.label))

    # -- buttons on a service card -------------------------------------------------
    def add_service_action(self, action: ServiceAction) -> None:
        self._actions = [a for a in self._actions if a.key != action.key]
        self._actions.append(action)

    def service_actions(self, service) -> list[ServiceAction]:
        return sorted(
            (a for a in self._actions if a.applies_to(service)),
            key=lambda a: (a.order, a.label),
        )

    # -- panels other modules drop into a page -------------------------------------
    def add_panel(
        self, slot: str, template: str, order: int = 100, context: Callable | None = None
    ) -> None:
        """Put a template into someone else's page.

        ``context`` is an optional callable taking the request and returning what the
        template needs, so a panel arrives with its data and the host page stays ignorant
        of what it shows.
        """
        self._panels.setdefault(slot, []).append(Panel(order, template, context))

    def panels(self, slot: str) -> list[Panel]:
        return sorted(self._panels.get(slot, []), key=lambda panel: panel.order)

    def panel_context(self, slot: str, request) -> dict:
        """Everything the panels in this slot need, merged."""
        data: dict[str, Any] = {}
        for panel in self.panels(slot):
            if panel.context is not None:
                data.update(panel.context(request))
        return data

    def reset(self) -> None:  # used by the tests
        self.__init__()


#: The single registry instance the whole dashboard uses.
registry = Registry()
