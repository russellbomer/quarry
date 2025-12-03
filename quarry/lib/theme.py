"""Quarry visual theme and color definitions.

Mars/Jupiter Palette - warm, earthy, professional colors for terminal display.

This module centralizes all color definitions to maintain visual consistency
across the entire CLI interface. Uses named colors for broad terminal compatibility.
"""

from rich.style import Style
from rich.theme import Theme

# =============================================================================
# Mars/Jupiter Color Palette (Terminal Compatible)
# =============================================================================
# Using named colors that work across most terminal emulators
# Primary: dark_orange - Headers, primary accents
# Secondary: orange3 - Highlights, secondary accents
# Tertiary: wheat4 - Borders, subtle elements
# Emphasis: orange4 - Text emphasis
# Error: indian_red - Errors, warnings

COLORS = {
    "primary": "dark_orange",  # Headers, main accents
    "secondary": "orange3",  # Highlights, secondary accents
    "tertiary": "tan",  # Borders, subtle elements
    "emphasis": "dark_goldenrod",  # Text emphasis
    "error": "indian_red",  # Errors
    "success": "dark_olive_green3",  # Success messages
    "warning": "gold3",  # Warnings
    "info": "tan",  # Info (reuse tertiary)
    "dim": "grey62",  # Muted text
    "muted": "grey50",  # Darker muted
}

# =============================================================================
# Rich Styles
# =============================================================================
# Pre-defined styles for common UI elements

STYLES = {
    # Headers and titles
    "header": Style(color=COLORS["primary"], bold=True),
    "subheader": Style(color=COLORS["secondary"], bold=True),
    "title": Style(color=COLORS["primary"], bold=True),
    # Status indicators
    "success": Style(color=COLORS["success"], bold=True),
    "error": Style(color=COLORS["error"], bold=True),
    "warning": Style(color=COLORS["warning"], bold=True),
    "info": Style(color=COLORS["tertiary"]),
    # Text styles
    "emphasis": Style(color=COLORS["emphasis"], bold=True),
    "dim": Style(color=COLORS["dim"]),
    "muted": Style(color=COLORS["muted"]),
    # Interactive elements
    "prompt": Style(color=COLORS["secondary"]),
    "selection": Style(color=COLORS["primary"], bold=True),
    "highlight": Style(color=COLORS["secondary"], bold=True),
    # Code and data
    "code": Style(color=COLORS["tertiary"]),
    "selector": Style(color=COLORS["secondary"]),
    "url": Style(color=COLORS["tertiary"], underline=True),
    "path": Style(color=COLORS["emphasis"]),
    "number": Style(color=COLORS["success"], bold=True),
    # Borders and decorations
    "border": Style(color=COLORS["tertiary"]),
    "border_primary": Style(color=COLORS["primary"]),
    "border_success": Style(color=COLORS["success"]),
    "border_error": Style(color=COLORS["error"]),
}

# =============================================================================
# Rich Theme
# =============================================================================
# Theme for Rich Console that replaces default markup colors

QUARRY_THEME = Theme(
    {
        # Override default Rich markup colors
        "primary": COLORS["primary"],
        "secondary": COLORS["secondary"],
        "tertiary": COLORS["tertiary"],
        "emphasis": COLORS["emphasis"],
        "success": COLORS["success"],
        "error": COLORS["error"],
        "warning": COLORS["warning"],
        # Common markup replacements
        "cyan": COLORS["primary"],  # Replace cyan with rusty orange
        "bright_cyan": COLORS["secondary"],  # Replace bright_cyan with terracotta
        "blue": COLORS["tertiary"],  # Replace blue with dusty tan
        "green": COLORS["success"],  # Keep green-ish but earthy
        "red": COLORS["error"],  # Muted red
        "yellow": COLORS["warning"],  # Goldenrod
        "magenta": COLORS["secondary"],  # Use terracotta for magenta
        # Semantic styles
        "info": COLORS["tertiary"],
        "repr.number": COLORS["success"],
        "repr.str": COLORS["tertiary"],
        "repr.url": COLORS["tertiary"],
        "progress.elapsed": COLORS["dim"],
        "progress.remaining": COLORS["dim"],
        "progress.percentage": COLORS["primary"],
        "bar.complete": COLORS["primary"],
        "bar.finished": COLORS["success"],
        "status.spinner": COLORS["secondary"],
    }
)

# =============================================================================
# ASCII Banner Colors (for quarry.py BANNER)
# =============================================================================
# The banner uses gradient coloring for visual appeal

BANNER_COLORS = {
    "line1": COLORS["primary"],  # Top lines: Rusty Orange
    "line2": COLORS["primary"],
    "line3": COLORS["secondary"],  # Middle: Terracotta
    "line4": COLORS["secondary"],
    "line5": COLORS["tertiary"],  # Bottom: Dusty Tan
    "line6": COLORS["tertiary"],
    "tagline": COLORS["dim"],
}

# =============================================================================
# Questionary Styles (for interactive prompts)
# =============================================================================
# Style dict compatible with questionary.Style.from_dict()
# Uses ANSI color names that prompt_toolkit understands

QUESTIONARY_STYLE = {
    "question": "bold ansibrightred",
    "answer": "bold ansiyellow",
    "pointer": "bold ansibrightred",
    "highlighted": "bold ansiyellow",
    "selected": "ansigreen",
    "separator": "ansigray",
    "instruction": "ansigray",
    "text": "",  # Default terminal color
    "disabled": "ansidarkgray",
}

# =============================================================================
# Utility Functions
# =============================================================================


def get_border_style(style_type: str = "default") -> str:
    """Get border color for Rich panels/tables.

    Args:
        style_type: One of 'default', 'primary', 'success', 'error', 'warning'

    Returns:
        Color string for border_style parameter
    """
    mapping = {
        "default": COLORS["tertiary"],
        "primary": COLORS["primary"],
        "success": COLORS["success"],
        "error": COLORS["error"],
        "warning": COLORS["warning"],
        "info": COLORS["tertiary"],
    }
    return mapping.get(style_type, COLORS["tertiary"])


def get_status_style(status: str) -> str:
    """Get color for status indicators.

    Args:
        status: One of 'success', 'error', 'warning', 'info', 'pending'

    Returns:
        Color string
    """
    mapping = {
        "success": COLORS["success"],
        "error": COLORS["error"],
        "warning": COLORS["warning"],
        "info": COLORS["tertiary"],
        "pending": COLORS["dim"],
    }
    return mapping.get(status, COLORS["dim"])


def styled(text: str, style: str) -> str:
    """Wrap text in Rich markup with theme style.

    Args:
        text: Text to style
        style: Style name from STYLES dict or color name

    Returns:
        Text wrapped in Rich markup

    Example:
        styled("Hello", "primary")  -> "[#CD4F39]Hello[/#CD4F39]"
        styled("Error!", "error")   -> "[#B85042]Error![/#B85042]"
    """
    color = COLORS.get(style, style)
    return f"[{color}]{text}[/{color}]"


def bold(text: str, color: str = "primary") -> str:
    """Wrap text in bold Rich markup with color.

    Args:
        text: Text to make bold
        color: Color name from COLORS dict

    Returns:
        Text wrapped in bold markup
    """
    color_code = COLORS.get(color, color)
    return f"[bold {color_code}]{text}[/bold {color_code}]"


# =============================================================================
# Exports
# =============================================================================
__all__ = [
    "BANNER_COLORS",
    "COLORS",
    "QUARRY_THEME",
    "QUESTIONARY_STYLE",
    "STYLES",
    "bold",
    "get_border_style",
    "get_status_style",
    "styled",
]
