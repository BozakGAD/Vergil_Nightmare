from __future__ import annotations

from src.core.gameplay_config import GameplayConfig
from src.systems.combo_system import ComboSystem


def test_combo_timeout_banks_score_and_clears_hits():
    combo = ComboSystem(GameplayConfig.from_files().combo)

    for _ in range(5):
        combo.register_hit()
    combo.update(5.1)

    assert combo.current_hits == 0
    assert combo.total_score == 5
    assert combo.final_style_rank() == "E"


def test_player_damage_resets_unranked_combo_without_score():
    combo = ComboSystem(GameplayConfig.from_files().combo)

    for _ in range(4):
        combo.register_hit()
    combo.register_player_damage()

    assert combo.current_hits == 0
    assert combo.total_score == 0
