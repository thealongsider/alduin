"""Module for defining the theme and styles used in Alduin's CLI interface."""

from rich.theme import Theme

BANNER_TEXT_STYLE = "bold bright_green"

BANNER_BORDER = "bright_magenta"
USER_BORDER = "bright_cyan"
ASSISTANT_BORDER = "bright_green"
TOOL_BORDER = "yellow"
TOOL_RESULT_BORDER = "green"
ERROR_BORDER = "red"
DEBUG_BORDER = "dim"

TOOL_NAME_STYLE = "bold yellow"
SUCCESS_STYLE = "bold green"
ERROR_TEXT_STYLE = "bold red"
MUTED_STYLE = "dim"

ALDUIN_THEME = Theme(
    {
        "user_prompt": "bold bright_cyan",
        "assistant_name": "bold bright_green",
        "system": "dim",
        "error": "bold red",
        "tool": "bold yellow",
    }
)
