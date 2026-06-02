"""Session-local context passed to the filter.

Deliberately *profile-free*. Building a persisted store of user attributes is
exactly the "preference bundle" objectification Viveka exists to detect (check
#1, subject/object integrity). If Viveka carried a durable user profile it would
become the thing it flags. So :class:`UserContext` holds only what is needed to
evaluate the *current* turn, and nothing that would accumulate into a model of
the user across sessions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class TaskType(Enum):
    """What the application is doing this turn. Used only to calibrate the
    cognitive-independence heuristic (#3): a direct factual lookup is *not*
    creating dependency by giving a direct answer, whereas a tutoring task
    might be. This is the one place task type legitimately matters.
    """

    UNSPECIFIED = auto()
    FACTUAL_LOOKUP = auto()    # user wants the answer; directness is appropriate
    TUTORING = auto()          # supporting the user's own reasoning is the goal
    ADVISORY = auto()          # recommendations; steering risk is higher
    OPEN_CHAT = auto()


@dataclass
class UserContext:
    """Minimal, session-local context. No durable user attributes by design.

    Parameters
    ----------
    handle:
        A conventional, non-identifying label for the speaker in *this* session
        (e.g. ``"user"``). Maps to Scherf's ``subject_handle``. It is a
        *vyāvahārika* convenience, not a claim about who the user is.
    recent_turns:
        The immediately preceding turns, for local disambiguation only. Capped;
        not persisted by Viveka.
    task_type:
        See :class:`TaskType`.
    """

    handle: str = "user"
    recent_turns: list[str] = field(default_factory=list)
    task_type: TaskType = TaskType.UNSPECIFIED

    # Intentionally NOT present: preferences, demographics, behavioral history,
    # inferred traits, embeddings, or any cross-session identifier. Their absence
    # is a design constraint, not an oversight. See module docstring.

    def __post_init__(self) -> None:
        # Hard cap: context is for local disambiguation, not profile accretion.
        if len(self.recent_turns) > 8:
            self.recent_turns = self.recent_turns[-8:]
