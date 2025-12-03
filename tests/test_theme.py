"""Tests for theme utility functions."""

import pytest

from quarry.lib.theme import (
    COLORS,
    STYLES,
    QUARRY_THEME,
    bold,
    get_border_style,
    get_status_style,
    styled,
)


class TestThemeConstants:
    """Tests for theme constant definitions."""

    def test_colors_has_required_keys(self):
        """Test COLORS dict has all expected keys."""
        expected_keys = [
            "primary",
            "secondary",
            "tertiary",
            "emphasis",
            "error",
            "success",
            "warning",
            "info",
            "dim",
            "muted",
        ]
        for key in expected_keys:
            assert key in COLORS

    def test_styles_has_required_keys(self):
        """Test STYLES dict has all expected keys."""
        expected_keys = ["header", "success", "error", "warning", "emphasis"]
        for key in expected_keys:
            assert key in STYLES

    def test_quarry_theme_is_theme(self):
        """Test QUARRY_THEME is a Rich Theme instance."""
        from rich.theme import Theme

        assert isinstance(QUARRY_THEME, Theme)


class TestGetBorderStyle:
    """Tests for get_border_style function."""

    def test_default_style(self):
        """Test default border style."""
        result = get_border_style("default")
        assert result == COLORS["tertiary"]

    def test_primary_style(self):
        """Test primary border style."""
        result = get_border_style("primary")
        assert result == COLORS["primary"]

    def test_success_style(self):
        """Test success border style."""
        result = get_border_style("success")
        assert result == COLORS["success"]

    def test_error_style(self):
        """Test error border style."""
        result = get_border_style("error")
        assert result == COLORS["error"]

    def test_warning_style(self):
        """Test warning border style."""
        result = get_border_style("warning")
        assert result == COLORS["warning"]

    def test_info_style(self):
        """Test info border style."""
        result = get_border_style("info")
        assert result == COLORS["tertiary"]

    def test_unknown_style_returns_default(self):
        """Test unknown style returns tertiary (default)."""
        result = get_border_style("unknown")
        assert result == COLORS["tertiary"]

    def test_no_argument_returns_default(self):
        """Test calling with no argument returns default."""
        result = get_border_style()
        assert result == COLORS["tertiary"]


class TestGetStatusStyle:
    """Tests for get_status_style function."""

    def test_success_status(self):
        """Test success status style."""
        result = get_status_style("success")
        assert result == COLORS["success"]

    def test_error_status(self):
        """Test error status style."""
        result = get_status_style("error")
        assert result == COLORS["error"]

    def test_warning_status(self):
        """Test warning status style."""
        result = get_status_style("warning")
        assert result == COLORS["warning"]

    def test_info_status(self):
        """Test info status style."""
        result = get_status_style("info")
        assert result == COLORS["tertiary"]

    def test_pending_status(self):
        """Test pending status style."""
        result = get_status_style("pending")
        assert result == COLORS["dim"]

    def test_unknown_status_returns_dim(self):
        """Test unknown status returns dim."""
        result = get_status_style("unknown")
        assert result == COLORS["dim"]


class TestStyled:
    """Tests for styled function."""

    def test_styled_with_color_name(self):
        """Test styled with a color name from COLORS."""
        result = styled("Hello", "primary")
        assert COLORS["primary"] in result
        assert "Hello" in result
        assert result.startswith("[")
        assert result.endswith("]")

    def test_styled_with_error(self):
        """Test styled with error color."""
        result = styled("Error!", "error")
        assert COLORS["error"] in result
        assert "Error!" in result

    def test_styled_with_unknown_style_uses_literal(self):
        """Test styled with unknown style uses it as literal."""
        result = styled("Test", "bright_green")
        assert "bright_green" in result
        assert "Test" in result

    def test_styled_empty_text(self):
        """Test styled with empty text."""
        result = styled("", "primary")
        assert result == f"[{COLORS['primary']}][/{COLORS['primary']}]"


class TestBold:
    """Tests for bold function."""

    def test_bold_default_color(self):
        """Test bold with default primary color."""
        result = bold("Hello")
        assert "bold" in result
        assert COLORS["primary"] in result
        assert "Hello" in result

    def test_bold_with_color(self):
        """Test bold with specified color."""
        result = bold("World", "error")
        assert "bold" in result
        assert COLORS["error"] in result
        assert "World" in result

    def test_bold_with_unknown_color(self):
        """Test bold with unknown color uses literal."""
        result = bold("Test", "magenta")
        assert "bold" in result
        assert "magenta" in result
        assert "Test" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
