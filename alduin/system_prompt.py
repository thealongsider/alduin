"""Module for defining the system prompt for Alduin, the coding assistant."""

import textwrap


def get() -> str:
    """Create the system prompt for Alduin.

    Returns:
        The system prompt.
    """

    return textwrap.dedent(
        """\
            You are Alduin, a helpful and precise coding assistant for software developers.
            Keep responses concise and practical. Output should always be in markdown format.
        """
    )
