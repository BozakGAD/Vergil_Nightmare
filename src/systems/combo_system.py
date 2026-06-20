"""Combo and final style score tracking."""

from __future__ import annotations

from src.core.gameplay_config import ComboRankSettings, ComboSettings, StyleRankSettings


class ComboSystem:
    """Track session combo hits, timeout resets, and accumulated style score."""

    def __init__(self, settings: ComboSettings) -> None:
        self.settings = settings
        self.current_hits = 0
        self.total_score = 0.0
        self.time_since_hit = 0.0
        self.has_active_combo = False

    def register_hit(self) -> None:
        """Increase combo by one hit and refresh timeout."""
        self.current_hits += 1
        self.time_since_hit = 0.0
        self.has_active_combo = True

    def register_player_damage(self) -> None:
        """Player damage immediately banks and clears the active combo."""
        self.reset_combo()

    def update(self, dt: float) -> None:
        """Reset stale combos after the configured timeout."""
        if not self.has_active_combo:
            return
        self.time_since_hit += dt
        if self.time_since_hit > self.settings.timeout:
            self.reset_combo()

    def reset_combo(self) -> None:
        """Bank current combo into style score and clear it."""
        if self.current_hits > 0:
            rank = self.current_combo_rank_setting()
            multiplier = rank.score_multiplier if rank is not None else 0.0
            self.total_score += self.current_hits * multiplier
        self.current_hits = 0
        self.time_since_hit = 0.0
        self.has_active_combo = False

    def current_combo_rank(self) -> str | None:
        """Return display rank for current hit count, or None before rank E."""
        rank = self.current_combo_rank_setting()
        return rank.rank if rank is not None else None

    def final_style_rank(self) -> str | None:
        """Return final style rank from accumulated score."""
        result: StyleRankSettings | None = None
        for rank in self.settings.style_score_ranks:
            if self.total_score >= rank.min_score:
                result = rank
        return result.rank if result is not None else None

    def current_combo_rank_setting(self) -> ComboRankSettings | None:
        result: ComboRankSettings | None = None
        for rank in self.settings.ranks:
            if self.current_hits >= rank.min_hits:
                result = rank
        return result
