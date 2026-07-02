"""Tests for JourneyEngine."""
import pytest
from myTime.core.models import WorkSchedule, SessionType
from myTime.core.engine import JourneyEngine, ScheduledBlock


class TestJourneyEngine:
    """Test journey calculation engine."""

    @pytest.fixture
    def default_config(self):
        return WorkSchedule()

    @pytest.fixture
    def custom_config(self):
        return WorkSchedule(
            work_duration=30 * 60,
            short_break_duration=3 * 60,
            long_break_duration=10 * 60,
            sessions_before_long_break=3,
        )

    @pytest.fixture
    def engine(self, default_config):
        return JourneyEngine(default_config)

    def test_initialization(self, default_config):
        engine = JourneyEngine(default_config)
        assert engine.config == default_config

    def test_empty_journey(self, engine):
        blocks = engine.calculate_journey(0)
        assert len(blocks) == 0

    def test_single_block(self, engine):
        blocks = engine.calculate_journey(25)  # 25 min = exactly one block
        assert len(blocks) == 1
        assert blocks[0].session_type == SessionType.WORK
        assert blocks[0].duration_seconds == 25 * 60
        assert blocks[0].is_work_block

    def test_two_blocks_with_break(self, engine):
        blocks = engine.calculate_journey(50)  # 50 min = 2 work blocks + 1 break
        assert len(blocks) == 3
        assert blocks[0].session_type == SessionType.WORK
        assert blocks[1].session_type == SessionType.SHORT_BREAK
        assert blocks[2].session_type == SessionType.WORK

    def test_long_break_after_4_blocks(self, engine):
        blocks = engine.calculate_journey(100)  # 100 min = 4 blocks of 25, no leftover
        # 4 blocks => breaks after 1,2,3. No break after 4th (no more work).
        # Journey: Work(0), Short(1), Work(2), Short(3), Work(4), Short(5), Work(6)
        session_types = [b.session_type for b in blocks]
        assert len(blocks) == 7
        assert session_types[-1] == SessionType.WORK
        # Long break triggers when remaining work > 0 AND count % 4 == 0
        blocks = engine.calculate_journey(101)  # 101 min = 4 blocks + 1 leftover
        session_types = [b.session_type for b in blocks]
        assert session_types[-2] == SessionType.LONG_BREAK

    def test_blocks_sum_equals_total(self, engine):
        total = 120  # 2 hours
        blocks = engine.calculate_journey(total)
        work_time = engine.get_work_time(blocks)
        assert work_time == total * 60  # Work time in seconds matches input

    def test_task_name_assigned(self, engine):
        blocks = engine.calculate_journey(25, task_name="Coding")
        for block in blocks:
            if block.is_work_block:
                assert block.task_name == "Coding"

    def test_custom_config(self, custom_config):
        engine = JourneyEngine(custom_config)
        blocks = engine.calculate_journey(60)  # 1 hour = 2 blocks of 30
        assert len(blocks) == 3  # 2 work + 1 short break (no break after last)
        work_time = engine.get_work_time(blocks)
        assert work_time == 60 * 60
        # Test long break with custom config (3 before long break)
        blocks = engine.calculate_journey(95)  # 3 full + 1 partial block
        assert len(blocks) == 7  # 4 work + 2 short breaks (after 1&2) + 1 long break (after 3)
        session_types = [b.session_type for b in blocks]
        assert session_types[-2] == SessionType.LONG_BREAK

    def test_partial_final_block(self, engine):
        blocks = engine.calculate_journey(20)  # Less than one full block
        assert len(blocks) == 1
        assert blocks[0].duration_seconds == 20 * 60  # Partial block

    def test_total_journey_time(self, engine):
        blocks = engine.calculate_journey(120)  # 2h work = 4 blocks + 3 short breaks + 1 long
        total = engine.get_total_journey_time(blocks)
        expected = 120 * 60 + 3 * 5 * 60 + 15 * 60  # work + breaks
        assert total == expected

    def test_break_time_separate(self, engine):
        blocks = engine.calculate_journey(120)
        work = engine.get_work_time(blocks)
        breaks = engine.get_break_time(blocks)
        assert work == 120 * 60
        assert breaks == 3 * 5 * 60 + 15 * 60  # 3 short + 1 long

    def test_get_next_block(self, engine):
        blocks = engine.calculate_journey(25)
        assert engine.get_next_block(blocks, 0) is None  # No next block after single block

        blocks = engine.calculate_journey(50)
        next_block = engine.get_next_block(blocks, 0)
        assert next_block is not None
        assert next_block.session_type == SessionType.SHORT_BREAK

        none_block = engine.get_next_block(blocks, 3)  # Past end
        assert none_block is None

    def test_format_time(self, engine):
        assert engine.format_time(0) == "00:00"
        assert engine.format_time(60) == "01:00"
        assert engine.format_time(3661) == "01:01:01"
        assert engine.format_time(1500) == "25:00"

    def test_get_progress_empty(self, engine):
        progress = engine.get_progress([], 0, 0)
        assert progress["total_blocks"] == 0
        assert progress["work_percent"] == 0.0

    def test_get_progress_partial(self, engine):
        blocks = engine.calculate_journey(25)
        progress = engine.get_progress(blocks, 0, 300)  # 5 min into first block
        assert progress["work_percent"] == pytest.approx(20.0)  # 5/25 = 20%
        assert progress["current_block"] == 1

    def test_order_field(self, engine):
        blocks = engine.calculate_journey(50)
        orders = [b.order for b in blocks]
        assert orders == [0, 1, 2]  # Sequential ordering
