"""Main menu scene with a foreground controls settings panel."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pygame

from src.core.control_constants import (
    CONTROL_LABELS,
    LEFT_SETTINGS_COLUMN,
    RIGHT_SETTINGS_COLUMN,
)
from src.core.settings import AssetSettings
from src.systems.control_settings import ControlSettings
from src.ui.button import Button


class MainMenuScene:
    """First window shown to the player after launching the game."""

    BACKGROUND_COLOR = (13, 15, 27)
    PANEL_COLOR = (28, 30, 44)
    ACCENT_COLOR = (138, 34, 47)
    TEXT_COLOR = (240, 240, 245)
    MUTED_TEXT_COLOR = (172, 174, 190)
    PLACEHOLDER_BORDER_COLOR = (102, 54, 72)

    def __init__(
        self,
        screen_size: tuple[int, int],
        controls: ControlSettings,
        assets: AssetSettings,
        start_game: Callable[[], None],
        quit_game: Callable[[], None],
    ) -> None:
        self.screen_width, self.screen_height = screen_size
        self.controls = controls
        self.assets = assets
        self.start_game = start_game
        self.quit_game = quit_game
        font_path = pygame.font.match_font("dejavusans")
        self.subtitle_font = pygame.font.Font(font_path, 24)
        self.button_font = pygame.font.Font(font_path, 26)
        self.small_font = pygame.font.Font(font_path, 20)
        self.settings_open = False
        self.waiting_for_action: str | None = None
        self.background_image = self._load_scaled_image(
            self.assets.main_menu_background,
            (self.screen_width, self.screen_height),
        )
        self.title_placeholder_image = self._load_scaled_image(self.assets.title_placeholder_image, (560, 145))
        self.menu_buttons = self._create_menu_buttons()
        self.settings_buttons: list[Button] = []
        self._rebuild_settings_buttons()

    def _load_scaled_image(self, image_path: str | None, size: tuple[int, int]) -> pygame.Surface | None:
        """Load and scale an optional image asset if the configured file exists."""
        if not image_path:
            return None
        path = Path(image_path)
        if not path.exists():
            return None
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(image, size)

    def _create_menu_buttons(self) -> list[Button]:
        button_width = 330
        button_height = 62
        start_y = 315
        gap = 24
        left = (self.screen_width - button_width) // 2
        labels_and_actions: tuple[tuple[str, Callable[[], None]], ...] = (
            ("Начать игру", self.start_game),
            ("Настройки", self._open_settings),
            ("Выход", self.quit_game),
        )
        return [
            Button(
                rect=pygame.Rect(left, start_y + index * (button_height + gap), button_width, button_height),
                text=label,
                on_click=action,
            )
            for index, (label, action) in enumerate(labels_and_actions)
        ]

    def _rebuild_settings_buttons(self) -> None:
        panel_rect = self._settings_panel_rect()
        column_width = 450
        row_height = 48
        row_gap = 14
        top = panel_rect.top + 130
        left_x = panel_rect.left + 65
        right_x = panel_rect.right - column_width - 65
        buttons: list[Button] = []

        for column_x, actions in ((left_x, LEFT_SETTINGS_COLUMN), (right_x, RIGHT_SETTINGS_COLUMN)):
            for index, action in enumerate(actions):
                button_rect = pygame.Rect(
                    column_x,
                    top + index * (row_height + row_gap),
                    column_width,
                    row_height,
                )
                buttons.append(
                    Button(
                        rect=button_rect,
                        text=self._settings_button_text(action),
                        on_click=lambda selected_action=action: self._start_rebinding(selected_action),
                        enabled=action != "pause",
                        action_id=action,
                    )
                )

        close_rect = pygame.Rect(panel_rect.centerx - 120, panel_rect.bottom - 74, 240, 50)
        buttons.append(Button(rect=close_rect, text="Закрыть", on_click=self._close_settings))
        self.settings_buttons = buttons

    def _settings_button_text(self, action: str) -> str:
        key_text = self.controls.get(action).upper()
        if action == "pause":
            return f"{CONTROL_LABELS[action]}: {key_text}"
        if self.waiting_for_action == action:
            return f"{CONTROL_LABELS[action]}: нажмите клавишу..."
        return f"{CONTROL_LABELS[action]}: {key_text}"

    def _settings_panel_rect(self) -> pygame.Rect:
        return pygame.Rect(70, 72, self.screen_width - 140, self.screen_height - 124)

    def _open_settings(self) -> None:
        self.settings_open = True
        self.waiting_for_action = None
        self._rebuild_settings_buttons()

    def _close_settings(self) -> None:
        self.settings_open = False
        self.waiting_for_action = None

    def _start_rebinding(self, action: str) -> None:
        if action == "pause":
            return
        self.waiting_for_action = action
        self._rebuild_settings_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle menu and settings input."""
        if event.type == pygame.KEYDOWN:
            if self.waiting_for_action is not None:
                self.controls.set_key(self.waiting_for_action, pygame.key.name(event.key))
                self.controls.save()
                self.waiting_for_action = None
                self._rebuild_settings_buttons()
                return
            if event.key == pygame.K_ESCAPE and self.settings_open:
                self._close_settings()
                return

        if self.settings_open:
            for button in self.settings_buttons:
                button.handle_event(event)
            return

        for button in self.menu_buttons:
            button.handle_event(event)

    def update(self, _dt: float) -> None:
        """Update the menu scene."""

    def draw(self, surface: pygame.Surface) -> None:
        """Draw menu and optional foreground settings panel."""
        mouse_position = pygame.mouse.get_pos()
        surface.fill(self.BACKGROUND_COLOR)
        self._draw_background(surface)
        self._draw_title_placeholder(surface)

        for button in self.menu_buttons:
            button.draw(surface, self.button_font, mouse_position=mouse_position)

        if self.settings_open:
            self._draw_settings_overlay(surface, mouse_position)

    def _draw_background(self, surface: pygame.Surface) -> None:
        """Draw a configured menu background or leave a plain fallback color."""
        if self.background_image is not None:
            surface.blit(self.background_image, (0, 0))

    def _draw_title_placeholder(self, surface: pygame.Surface) -> None:
        """Reserve a visible area for the future pixel-art title image."""
        placeholder_rect = pygame.Rect(0, 0, 560, 145)
        placeholder_rect.center = (self.screen_width // 2, 155)
        if self.title_placeholder_image is not None:
            surface.blit(self.title_placeholder_image, placeholder_rect)
            return

        placeholder = pygame.Surface(placeholder_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(placeholder, (0, 0, 0, 70), placeholder.get_rect(), border_radius=12)
        pygame.draw.rect(placeholder, self.PLACEHOLDER_BORDER_COLOR, placeholder.get_rect(), width=2, border_radius=12)
        label = self.small_font.render("Заглушка под пиксельное изображение названия", True, self.MUTED_TEXT_COLOR)
        placeholder.blit(label, label.get_rect(center=placeholder.get_rect().center))
        surface.blit(placeholder, placeholder_rect)

    def _draw_settings_overlay(self, surface: pygame.Surface, mouse_position: tuple[int, int]) -> None:
        dim_layer = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim_layer.fill((0, 0, 0, 165))
        surface.blit(dim_layer, (0, 0))

        panel_rect = self._settings_panel_rect()
        pygame.draw.rect(surface, self.PANEL_COLOR, panel_rect, border_radius=18)
        pygame.draw.rect(surface, self.ACCENT_COLOR, panel_rect, width=3, border_radius=18)

        title = self.subtitle_font.render("Настройки управления", True, self.TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(panel_rect.centerx, panel_rect.top + 42)))

        hint_text = "Нажмите кнопку действия, затем новую клавишу."
        hint = self.small_font.render(hint_text, True, self.MUTED_TEXT_COLOR)
        surface.blit(hint, hint.get_rect(center=(panel_rect.centerx, panel_rect.top + 78)))

        left_label = self.small_font.render("Передвижение", True, self.MUTED_TEXT_COLOR)
        right_label = self.small_font.render("Боевые действия и система", True, self.MUTED_TEXT_COLOR)
        surface.blit(left_label, (panel_rect.left + 70, panel_rect.top + 106))
        surface.blit(right_label, (panel_rect.centerx + 35, panel_rect.top + 106))

        for button in self.settings_buttons:
            if button.action_id is not None:
                button.text = self._settings_button_text(button.action_id)
            button.draw(surface, self.small_font, mouse_position=mouse_position)
