"""Reusable pygame button widget."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame


@dataclass(slots=True)
class Button:
    """Simple rectangular button with hover and click handling."""

    rect: pygame.Rect
    text: str
    on_click: Callable[[], None]
    enabled: bool = True
    action_id: str | None = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Call the click callback when the button is pressed."""
        if not self.enabled or event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if self.rect.collidepoint(event.pos):
            self.on_click()

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        *,
        mouse_position: tuple[int, int],
        background_color: tuple[int, int, int] = (52, 55, 75),
        hover_color: tuple[int, int, int] = (85, 89, 122),
        disabled_color: tuple[int, int, int] = (42, 42, 48),
        text_color: tuple[int, int, int] = (245, 245, 245),
    ) -> None:
        """Render the button."""
        if not self.enabled:
            fill_color = disabled_color
        elif self.rect.collidepoint(mouse_position):
            fill_color = hover_color
        else:
            fill_color = background_color

        pygame.draw.rect(surface, fill_color, self.rect, border_radius=12)
        pygame.draw.rect(surface, (160, 160, 190), self.rect, width=2, border_radius=12)

        label = font.render(self.text, True, text_color)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)
