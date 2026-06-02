"""Main pygame application object."""

from __future__ import annotations

import ctypes
import sys
from collections.abc import Callable
from pathlib import Path

import pygame

from src.core.control_constants import CONTROL_STORAGE_PATH
from src.core.settings import GameSettings
from src.scenes.main_menu_scene import MainMenuScene
from src.systems.control_settings import ControlSettings


class PlaceholderGameScene:
    """Temporary scene shown after pressing 'Start game'."""

    BACKGROUND_COLOR = (10, 12, 20)
    TEXT_COLOR = (240, 240, 245)
    MUTED_TEXT_COLOR = (170, 174, 190)

    def __init__(self, screen_size: tuple[int, int], return_to_menu: Callable[[], None]) -> None:
        self.screen_width, self.screen_height = screen_size
        self.return_to_menu = return_to_menu
        font_path = pygame.font.match_font("dejavusans")
        self.title_font = pygame.font.Font(font_path, 38)
        self.text_font = pygame.font.Font(font_path, 23)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.return_to_menu()

    def update(self, _dt: float) -> None:
        """Update placeholder scene."""

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(self.BACKGROUND_COLOR)
        title = self.title_font.render("Игровая сцена будет реализована следующим этапом", True, self.TEXT_COLOR)
        title_rect = title.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 28))
        surface.blit(title, title_rect)
        hint = self.text_font.render("Нажмите Escape, чтобы вернуться в главное меню", True, self.MUTED_TEXT_COLOR)
        hint_rect = hint.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 28))
        surface.blit(hint, hint_rect)


class Game:
    """Owns pygame initialization, the active scene and the main loop."""

    def __init__(self, settings_path: str = "data/settings.json") -> None:
        pygame.init()
        self.settings = GameSettings.from_file(settings_path)
        self._apply_taskbar_app_id(self.settings.window.taskbar_app_id)
        self.screen = pygame.display.set_mode((self.settings.window.width, self.settings.window.height))
        pygame.display.set_caption(self.settings.window.title)
        self._apply_window_icon(self.settings.window.icon_path)
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.controls = ControlSettings(CONTROL_STORAGE_PATH)
        self.controls.load()
        self.active_scene = self._create_main_menu_scene()

    def _apply_taskbar_app_id(self, app_id: str | None) -> None:
        """Set a custom Windows taskbar application id when supported."""
        if sys.platform != "win32" or not app_id:
            return
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    def _apply_window_icon(self, icon_path: str | None) -> None:
        """Set the window icon if an icon asset is present."""
        if not icon_path:
            return
        path = Path(icon_path)
        if not path.exists():
            return
        icon = pygame.image.load(path).convert_alpha()
        pygame.display.set_icon(icon)

    def _create_main_menu_scene(self) -> MainMenuScene:
        return MainMenuScene(
            screen_size=(self.settings.window.width, self.settings.window.height),
            controls=self.controls,
            assets=self.settings.assets,
            start_game=self.start_game,
            quit_game=self.stop,
        )

    def start_game(self) -> None:
        """Switch from the menu to a temporary gameplay placeholder."""
        self.active_scene = PlaceholderGameScene(
            screen_size=(self.settings.window.width, self.settings.window.height),
            return_to_menu=self.return_to_menu,
        )

    def return_to_menu(self) -> None:
        """Return to the main menu."""
        self.active_scene = self._create_main_menu_scene()

    def stop(self) -> None:
        """Request application shutdown."""
        self.is_running = False

    def run(self) -> None:
        """Run the pygame event loop."""
        while self.is_running:
            dt = self.clock.tick(self.settings.window.fps) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop()
                else:
                    self.active_scene.handle_event(event)

            self.active_scene.update(dt)
            self.active_scene.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
