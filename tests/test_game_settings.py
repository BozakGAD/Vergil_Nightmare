from __future__ import annotations

import json

from src.core.settings import GameSettings


def test_game_settings_loads_window_branding_and_assets(tmp_path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "window": {
                    "width": 800,
                    "height": 450,
                    "fps": 60,
                    "title": "Test Game",
                    "icon_path": "assets/icons/app_icon.png",
                    "taskbar_app_id": "test.game",
                },
                "assets": {
                    "main_menu_background": "assets/backgrounds/main_menu_background/main_menu_background.png",
                    "game_background": "assets/backgrounds/game_background/game_background.png",
                },
            }
        ),
        encoding="utf-8",
    )

    settings = GameSettings.from_file(settings_path)

    assert settings.window.title == "Test Game"
    assert settings.window.icon_path == "assets/icons/app_icon.png"
    assert settings.window.taskbar_app_id == "test.game"
    assert settings.assets.main_menu_background == "assets/backgrounds/main_menu_background/main_menu_background.png"
    assert settings.assets.game_background == "assets/backgrounds/game_background/game_background.png"
