from __future__ import annotations

from src.core.gameplay_config import GameplayConfig
from src.systems.combo_system import ComboSystem


def test_combo_timeout_banks_score_and_clears_hits():
    combo = ComboSystem(GameplayConfig.from_files().combo)

    for _ in range(5):
        combo.register_hit()
    combo.update(combo.settings.timeout + 0.1)

    assert combo.current_hits == 0
    assert combo.total_score == 5
    assert combo.final_style_rank() == "E"


def test_player_damage_resets_unranked_combo_without_score():
    combo = ComboSystem(GameplayConfig.from_files().combo)

    for _ in range(4):
        combo.register_hit()
    combo.register_player_damage()

    assert combo.current_hits == 0
    assert combo.total_score == 4


def test_player_damage_banks_ranked_combo_score():
    combo = ComboSystem(GameplayConfig.from_files().combo)

    for _ in range(5):
        combo.register_hit()
    combo.register_player_damage()

    assert combo.current_hits == 0
    assert combo.total_score == 5
    assert combo.final_style_rank() == "E"


def test_inactive_taunt_multiplier_does_not_change_score():
    combo = ComboSystem(GameplayConfig.from_files().combo)

    for _ in range(6):
        combo.register_hit()
    combo.reset_combo()

    assert combo.total_score == 7.5


def test_combo_timeout_can_pause_and_resume_for_taunt():
    combo = ComboSystem(GameplayConfig.from_files().combo)

    for _ in range(5):
        combo.register_hit()
    combo.update(combo.settings.timeout - 0.1)
    combo.pause_timeout()
    combo.update(10.0)

    assert combo.current_hits == 5
    assert combo.time_since_hit == combo.settings.timeout - 0.1

    combo.resume_timeout()
    combo.update(0.2)

    assert combo.current_hits == 0
    assert combo.total_score == 5
