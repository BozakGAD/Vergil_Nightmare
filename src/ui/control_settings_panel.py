"""Reusable controls settings overlay panel."""

from __future__ import annotations

import pygame

from src.core.control_constants import CONTROL_LABELS, LEFT_SETTINGS_COLUMN, RIGHT_SETTINGS_COLUMN
from src.systems.control_settings import ControlSettings
from src.ui.button import Button


class ControlSettingsPanel:
    """Foreground panel for viewing and rebinding player controls."""

    BORDER_GAP = 150
    BUTTON_WIDTH = 350
    PANEL_COLOR = (33, 42, 64, 200)
    BORDER_COLOR = (255, 255, 255, 255)
    TEXT_COLOR = (240, 240, 245)
    MUTED_TEXT_COLOR = (172, 174, 190)

    def __init__(self, *, screen_size: tuple[int, int], controls: ControlSettings) -> None:
        self.screen_width, self.screen_height = screen_size
        self.controls = controls
        font_path = pygame.font.match_font("dejavusans")
        self.title_font = pygame.font.Font(font_path, 24)
        self.small_font = pygame.font.Font(font_path, 20)
        self.is_open = False
        self.waiting_for_action: str | None = None
        self.buttons: list[Button] = []
        self._rebuild_buttons()

    def open(self) -> None:
        """Open the settings panel and reset pending rebind state."""
        self.is_open = True
        self.waiting_for_action = None
        self._rebuild_buttons()

    def close(self) -> None:
        """Close the settings panel."""
        self.is_open = False
        self.waiting_for_action = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle panel input and return True when the event was consumed."""
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN:
            if self.waiting_for_action is not None:
                self.controls.set_key(self.waiting_for_action, pygame.key.name(event.key))
                self.controls.save()
                self.waiting_for_action = None
                self._rebuild_buttons()
                return True
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True

        for button in self.buttons:
            button.handle_event(event)
        return True

    def draw(self, surface: pygame.Surface, mouse_position: tuple[int, int] | None = None) -> None:
        """Draw the overlay if it is open."""
        if not self.is_open:
            return
        mouse_position = mouse_position or pygame.mouse.get_pos()
        dim_layer = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim_layer.fill((0, 0, 0, 165))
        surface.blit(dim_layer, (0, 0))

        panel_rect = self._panel_rect()
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        local_rect = pygame.Rect(0, 0, panel_rect.width, panel_rect.height)
        pygame.draw.rect(panel_surface, self.PANEL_COLOR, local_rect, border_radius=12)
        pygame.draw.rect(panel_surface, self.BORDER_COLOR, local_rect, width=2, border_radius=12)
        surface.blit(panel_surface, panel_rect.topleft)

        title = self.title_font.render("Настройки управления", True, self.TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(panel_rect.centerx, panel_rect.top + 42)))
        hint = self.small_font.render("Нажмите кнопку действия, затем новую клавишу.", True, self.MUTED_TEXT_COLOR)
        surface.blit(hint, hint.get_rect(center=(panel_rect.centerx, panel_rect.top + 78)))

        left_label = self.small_font.render("Передвижение", True, self.MUTED_TEXT_COLOR)
        right_label = self.small_font.render("Боевые действия и система", True, self.MUTED_TEXT_COLOR)
        surface.blit(left_label, (panel_rect.left + self.BORDER_GAP + 100, panel_rect.top + 106))
        surface.blit(right_label, (panel_rect.right - self.BORDER_GAP - self.BUTTON_WIDTH + 30, panel_rect.top + 106))

        for button in self.buttons:
            if button.action_id is not None:
                button.text = self._button_text(button.action_id)
            button.draw(surface, self.small_font, mouse_position=mouse_position)

    def _rebuild_buttons(self) -> None:
        panel_rect = self._panel_rect()
        row_height = 48
        row_gap = 14
        top = panel_rect.top + 130
        left_x = panel_rect.left + self.BORDER_GAP
        right_x = panel_rect.right - self.BORDER_GAP - self.BUTTON_WIDTH
        buttons: list[Button] = []
        for column_x, actions in ((left_x, LEFT_SETTINGS_COLUMN), (right_x, RIGHT_SETTINGS_COLUMN)):
            for index, action in enumerate(actions):
                button_rect = pygame.Rect(column_x, top + index * (row_height + row_gap), self.BUTTON_WIDTH, row_height)
                buttons.append(
                    Button(
                        rect=button_rect,
                        text=self._button_text(action),
                        on_click=lambda selected_action=action: self._start_rebinding(selected_action),
                        enabled=action != "pause",
                        action_id=action,
                    )
                )
        close_rect = pygame.Rect(panel_rect.centerx - 120, panel_rect.bottom - 74, 240, 50)
        buttons.append(Button(rect=close_rect, text="Закрыть", on_click=self.close))
        self.buttons = buttons

    def _button_text(self, action: str) -> str:
        key_text = self.controls.get(action).upper()
        if action == "pause":
            return f"{CONTROL_LABELS[action]}: {key_text}"
        if self.waiting_for_action == action:
            return f"{CONTROL_LABELS[action]}: нажмите клавишу..."
        return f"{CONTROL_LABELS[action]}: {key_text}"

    def _panel_rect(self) -> pygame.Rect:
        return pygame.Rect(70, 72, self.screen_width - 140, self.screen_height - 124)

    def _start_rebinding(self, action: str) -> None:
        if action == "pause":
            return
        self.waiting_for_action = action
        self._rebuild_buttons()
