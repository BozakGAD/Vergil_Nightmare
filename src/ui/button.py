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
        background_color: tuple[int, int, int, int] = (38, 64, 94, 170),
        hover_color: tuple[int, int, int, int] = (52, 88, 129, 220),
        disabled_color: tuple[int, int, int, int] = (38, 64, 94, 90),
        text_color: tuple[int, int, int] = (245, 245, 245),
    ) -> None:
        """Render the button with transparency support."""
        if not self.enabled:
            fill_color = disabled_color
        elif self.rect.collidepoint(mouse_position):
            fill_color = hover_color
        else:
            fill_color = background_color

        button_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        local_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)

        pygame.draw.rect(button_surface, fill_color, local_rect, border_radius=7)
        pygame.draw.rect(button_surface, (255, 255, 255, 180), local_rect, width=2, border_radius=7)

        label = font.render(self.text, True, text_color)
        label_rect = label.get_rect(center=local_rect.center)
        button_surface.blit(label, label_rect)

        surface.blit(button_surface, self.rect.topleft)