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
        self.taunt_multiplier_active = False
        self.is_timeout_paused = False

    def register_hit(self) -> None:
        """Increase combo by one hit and refresh timeout."""
        self.current_hits += 1
        self.time_since_hit = 0.0
        self.has_active_combo = True

    def register_player_damage(self) -> None:
        """Player damage breaks the active combo after banking earned score."""
        self.reset_combo(bank_score=True)

    def update(self, dt: float) -> None:
        """Reset stale combos after the configured timeout."""
        if not self.has_active_combo or self.is_timeout_paused:
            return
        self.time_since_hit += dt
        if self.time_since_hit > self.settings.timeout:
            self.reset_combo()

    def reset_combo(self, *, bank_score: bool = True) -> None:
        """Bank or clear current combo into style score and reset temporary boosts."""
        if bank_score and self.current_hits > 0:
            rank = self.current_combo_rank_setting()
            combo_multiplier = rank.score_multiplier if rank is not None else 0.0
            taunt_multiplier = self.settings.taunt_score_multiplier if self.taunt_multiplier_active else 1.0
            self.total_score += self.current_hits * combo_multiplier * taunt_multiplier
        self.current_hits = 0
        self.time_since_hit = 0.0
        self.has_active_combo = False
        self.taunt_multiplier_active = False
        self.is_timeout_paused = False

    def pause_timeout(self) -> None:
        """Freeze active combo timeout countdown, e.g. while a taunt animation plays."""
        if self.has_active_combo:
            self.is_timeout_paused = True

    def resume_timeout(self) -> None:
        """Resume active combo timeout countdown after a protected animation ends."""
        self.is_timeout_paused = False

    def activate_taunt_multiplier(self) -> None:
        """Boost score for the current combo until the combo is banked/reset."""
        self.taunt_multiplier_active = True

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
