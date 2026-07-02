"""Core engine for calculating Pomodoro journeys."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from myTime.core.models import WorkSchedule, SessionType, SessionStatus


@dataclass
class ScheduledBlock:
    """A single block in the journey schedule."""
    session_type: SessionType
    duration_seconds: int
    order: int
    is_work_block: bool
    task_name: str = ""


class JourneyEngine:
    """Calculates and manages Pomodoro journey schedules."""

    def __init__(self, config: WorkSchedule):
        self.config = config

    def calculate_journey(
        self,
        total_work_minutes: int,
        task_name: str = ""
    ) -> List[ScheduledBlock]:
        """
        Calculate full journey schedule for given work time.

        Args:
            total_work_minutes: Total minutes of work desired
            task_name: Optional task name for work blocks

        Returns:
            List of scheduled blocks (work + breaks)
        """
        blocks: List[ScheduledBlock] = []
        work_remaining = total_work_minutes * 60
        session_count = 0
        order = 0

        while work_remaining > 0:
            work_block_duration = min(self.config.work_duration, work_remaining)

            blocks.append(ScheduledBlock(
                session_type=SessionType.WORK,
                duration_seconds=work_block_duration,
                order=order,
                is_work_block=True,
                task_name=task_name
            ))
            order += 1
            work_remaining -= work_block_duration
            session_count += 1

            if work_remaining > 0:
                if session_count % self.config.sessions_before_long_break == 0:
                    blocks.append(ScheduledBlock(
                        session_type=SessionType.LONG_BREAK,
                        duration_seconds=self.config.long_break_duration,
                        order=order,
                        is_work_block=False
                    ))
                else:
                    blocks.append(ScheduledBlock(
                        session_type=SessionType.SHORT_BREAK,
                        duration_seconds=self.config.short_break_duration,
                        order=order,
                        is_work_block=False
                    ))
                order += 1

        return blocks

    def get_total_journey_time(self, blocks: List[ScheduledBlock]) -> int:
        """Get total journey time in seconds (work + breaks)."""
        return sum(b.duration_seconds for b in blocks)

    def get_work_time(self, blocks: List[ScheduledBlock]) -> int:
        """Get total work time in seconds."""
        return sum(b.duration_seconds for b in blocks if b.is_work_block)

    def get_break_time(self, blocks: List[ScheduledBlock]) -> int:
        """Get total break time in seconds."""
        return sum(b.duration_seconds for b in blocks if not b.is_work_block)

    def get_next_block(
        self,
        blocks: List[ScheduledBlock],
        current_index: int
    ) -> Optional[ScheduledBlock]:
        """Get next block in journey."""
        if current_index + 1 < len(blocks):
            return blocks[current_index + 1]
        return None

    def get_progress(
        self,
        blocks: List[ScheduledBlock],
        current_index: int,
        elapsed_seconds: int
    ) -> dict:
        """Calculate journey progress."""
        if not blocks:
            return {
                "total_blocks": 0,
                "current_block": 0,
                "blocks_completed": 0,
                "work_percent": 0.0,
                "time_percent": 0.0,
                "eta_seconds": 0
            }

        total_work = self.get_work_time(blocks)
        completed_work = sum(
            b.duration_seconds
            for b in blocks[:current_index]
            if b.is_work_block
        )

        if current_index < len(blocks):
            current_block = blocks[current_index]
            if current_block.is_work_block:
                completed_work += min(elapsed_seconds, current_block.duration_seconds)

        total_time = self.get_total_journey_time(blocks)
        elapsed_total = sum(b.duration_seconds for b in blocks[:current_index]) + elapsed_seconds

        return {
            "total_blocks": len(blocks),
            "current_block": current_index + 1,
            "blocks_completed": current_index,
            "work_percent": (completed_work / total_work * 100) if total_work > 0 else 0,
            "time_percent": (elapsed_total / total_time * 100) if total_time > 0 else 0,
            "eta_seconds": max(0, total_time - elapsed_total)
        }

    def format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS or HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def get_session_label(self, session_type: SessionType, translator) -> str:
        """Get localized label for session type."""
        labels = {
            SessionType.WORK: "work_session",
            SessionType.SHORT_BREAK: "short_break",
            SessionType.LONG_BREAK: "long_break",
        }
        return translator.t(f"session.{labels.get(session_type, 'work_session')}")
