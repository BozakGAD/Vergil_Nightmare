from __future__ import annotations

from src.systems.wave_manager import WaveManager, load_wave_settings


def test_wave_settings_load_from_json():
    settings = load_wave_settings()

    assert settings.max_waves == 10
    assert settings.enemy_costs["heavy_enemy"] == 4
    assert settings.base_budget == 3
    assert settings.budget_growth == 2
    assert settings.spawn_order[0] == "heavy_enemy"
    assert settings.inter_wave_delay == 1.5
    assert settings.spawn_offscreen_distance == 160


def test_wave_manager_generates_budget_based_waves():
    manager = WaveManager.from_file()

    first_wave = manager.next_wave(1280)
    second_wave = manager.next_wave(1280)

    assert [spawn.enemy_id for spawn in first_wave] == ["fast_enemy", "slow_enemy"]
    assert [spawn.enemy_id for spawn in second_wave] == ["heavy_enemy", "slow_enemy"]
    assert all(spawn.side in {"left", "right"} for spawn in first_wave + second_wave)
    assert all(spawn.x < 0 or spawn.x > 1280 for spawn in first_wave + second_wave)
