"""Tests for scheduler module — pure functions for spaced repetition."""
import pytest
from app.scheduler import _mastery_to_rating, _schedule_simple


class TestMasteryToRating:
    def test_very_high_mastery(self):
        assert _mastery_to_rating(0.95) == 5
        assert _mastery_to_rating(1.0) == 5

    def test_high_mastery(self):
        assert _mastery_to_rating(0.80) == 4
        assert _mastery_to_rating(0.70) == 4
        assert _mastery_to_rating(0.75) == 4

    def test_moderate_mastery(self):
        assert _mastery_to_rating(0.60) == 3
        assert _mastery_to_rating(0.50) == 3

    def test_low_mastery(self):
        assert _mastery_to_rating(0.40) == 2
        assert _mastery_to_rating(0.30) == 2

    def test_very_low_mastery(self):
        assert _mastery_to_rating(0.20) == 1
        assert _mastery_to_rating(0.0) == 1

    def test_boundary_values(self):
        assert _mastery_to_rating(0.89) == 4   # < 0.9
        assert _mastery_to_rating(0.90) == 5   # >= 0.9
        assert _mastery_to_rating(0.69) == 3   # < 0.7
        assert _mastery_to_rating(0.70) == 4   # >= 0.7
        assert _mastery_to_rating(0.49) == 2   # < 0.5
        assert _mastery_to_rating(0.50) == 3   # >= 0.5
        assert _mastery_to_rating(0.29) == 1   # < 0.3
        assert _mastery_to_rating(0.30) == 2   # >= 0.3


class TestScheduleSimple:
    def test_low_rating_returns_1(self):
        for rating in (1, 2):
            assert _schedule_simple(rating, 0) == 1
            assert _schedule_simple(rating, 5) == 1

    def test_rating_3_streak_0_returns_1(self):
        assert _schedule_simple(3, 0) == 1

    def test_rating_4_streak_0_returns_1(self):
        assert _schedule_simple(4, 0) == 1

    def test_streak_1_rating_3(self):
        assert _schedule_simple(3, 1) == 6

    def test_streak_1_rating_4(self):
        assert _schedule_simple(4, 1) == 6

    def test_streak_2_calculation(self):
        # rating=4: 6 * (4-1)^(2-1) = 6 * 3 = 18
        assert _schedule_simple(4, 2) == 18

    def test_streak_3_calculation(self):
        # rating=4: 6 * (4-1)^(3-1) = 6 * 9 = 54
        assert _schedule_simple(4, 3) == 54

    def test_higher_rating_faster_growth(self):
        assert _schedule_simple(5, 2) > _schedule_simple(4, 2)
        # rating=5: 6 * (5-1)^(2-1) = 6 * 4 = 24
        assert _schedule_simple(5, 2) == 24