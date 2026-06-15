"""Main pygame application object."""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

import pygame

from src.core.control_constants import CONTROL_STORAGE_PATH
from src.core.settings import GameSettings
from src.scenes.game_scene import GameScene
from src.scenes.main_menu_scene import MainMenuScene
from src.systems.control_settings import ControlSettings


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
        """Switch from the menu to the playable arena prototype."""
        self.active_scene = GameScene(
            screen_size=(self.settings.window.width, self.settings.window.height),
            controls=self.controls,
            assets=self.settings.assets,
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
