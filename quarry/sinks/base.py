"""Base sink interfaces."""

from typing import Protocol

from quarry.transforms.base import Frame


class Sink(Protocol):
    """Protocol for output sinks."""

    def write(self, df: Frame, job: str) -> str:
        """
        Write DataFrame to sink.

        Returns:
            Path to written file.
        """
        ...
