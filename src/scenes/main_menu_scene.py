"""Main menu scene with a foreground controls settings panel."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path

import pygame

from src.core.settings import AssetSettings
from src.systems.control_settings import ControlSettings
from src.ui.button import Button
from src.ui.control_settings_panel import ControlSettingsPanel


class MainMenuScene:
    """First window shown to the player after launching the game."""

    BACKGROUND_COLOR = (13, 15, 27)
    BORDER_COLOR = (255, 255, 255, 255)
    MUTED_TEXT_COLOR = (172, 174, 190)

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
        self.button_font = pygame.font.Font(font_path, 28)
        self.small_font = pygame.font.Font(font_path, 20)
        self.background_image = self._load_scaled_image(
            self.assets.main_menu_background,
            (self.screen_width, self.screen_height),
        )
        self.title_placeholder_image = self._load_scaled_image(self.assets.title_placeholder_image, (560, 145))
        self.settings_panel = ControlSettingsPanel(screen_size=screen_size, controls=self.controls)
        self.menu_buttons = self._create_menu_buttons()
        self.saved_style_rank = self._load_saved_style_rank()

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
        button_width = 290
        button_height = 62
        start_y = (self.screen_height-button_height) // 1.7
        gap = 24
        left = (self.screen_width - button_width) // 7
        labels_and_actions: tuple[tuple[str, Callable[[], None]], ...] = (
            ("Начать игру", self.start_game),
            ("Настройки", self.settings_panel.open),
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

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle menu and settings input."""
        if self.settings_panel.handle_event(event):
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
        self._draw_saved_style_rank(surface)

        for button in self.menu_buttons:
            button.draw(surface, self.button_font, mouse_position=mouse_position)

        self.settings_panel.draw(surface, mouse_position)

    def _load_saved_style_rank(self) -> str | None:
        path = Path("saves/style_rank.json")
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        rank = data.get("rank")
        return str(rank) if rank else None

    def _draw_saved_style_rank(self, surface: pygame.Surface) -> None:
        if self.saved_style_rank is None:
            return
        rect = pygame.Rect(self.screen_width - 190, 24, 160, 88)
        pygame.draw.rect(surface, (0, 0, 0, 110), rect, border_radius=10)
        pygame.draw.rect(surface, self.BORDER_COLOR, rect, width=2, border_radius=10)
        label = self.small_font.render(f"Saved style: {self.saved_style_rank}", True, self.MUTED_TEXT_COLOR)
        surface.blit(label, label.get_rect(center=rect.center))

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
        pygame.draw.rect(placeholder, self.BORDER_COLOR, placeholder.get_rect(), width=2, border_radius=12)
        label = self.small_font.render("Заглушка под пиксельное изображение названия", True, self.MUTED_TEXT_COLOR)
        placeholder.blit(label, label.get_rect(center=placeholder.get_rect().center))
        surface.blit(placeholder, placeholder_rect)

