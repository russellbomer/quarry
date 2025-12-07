"""Test retry logic for interactive prompts."""

from unittest.mock import MagicMock, patch

from quarry.lib.prompts import RetryablePrompt, prompt_file, prompt_url


def test_retryable_prompt_success_first_try():
    """Test successful prompt on first attempt"""
    prompter = RetryablePrompt(max_retries=3)

    mock_prompt = MagicMock(return_value="https://example.com")
    mock_validator = MagicMock(return_value=(True, None))

    result = prompter.ask_with_retry(
        prompt_fn=mock_prompt, validator=mock_validator, allow_cancel=True
    )

    assert result == "https://example.com"
    assert mock_prompt.call_count == 1
    assert mock_validator.call_count == 1


def test_retryable_prompt_retry_then_success():
    """Test prompt that fails once then succeeds"""
    prompter = RetryablePrompt(max_retries=3)

    # First call returns invalid, second returns valid
    mock_prompt = MagicMock(side_effect=["bad_url", "https://example.com"])
    mock_validator = MagicMock(side_effect=[(False, "Invalid URL"), (True, None)])

    with patch('quarry.lib.prompts.questionary.confirm') as mock_confirm:
        mock_confirm.return_value.ask.return_value = True  # Retry

        result = prompter.ask_with_retry(
            prompt_fn=mock_prompt, validator=mock_validator, allow_cancel=True
        )

    assert result == "https://example.com"
    assert mock_prompt.call_count == 2


def test_retryable_prompt_max_retries_reached():
    """Test that max retries is enforced"""
    prompter = RetryablePrompt(max_retries=2)

    mock_prompt = MagicMock(return_value="bad_input")
    mock_validator = MagicMock(return_value=(False, "Invalid"))

    with patch('quarry.lib.prompts.questionary.confirm') as mock_confirm:
        mock_confirm.return_value.ask.return_value = True  # Always retry

        result = prompter.ask_with_retry(
            prompt_fn=mock_prompt, validator=mock_validator, allow_cancel=True
        )

    assert result is None  # Max retries, returns None
    assert mock_prompt.call_count == 2  # max_retries


def test_retryable_prompt_user_cancels():
    """Test user cancellation"""
    prompter = RetryablePrompt(max_retries=3)

    mock_prompt = MagicMock(return_value=None)  # User cancelled

    result = prompter.ask_with_retry(prompt_fn=mock_prompt, allow_cancel=True)

    assert result is None
    assert mock_prompt.call_count == 1


def test_prompt_url_validates_scheme():
    """Test URL prompt validation"""
    with patch('quarry.lib.prompts.questionary.text') as mock_text:
        with patch('quarry.lib.prompts.questionary.confirm') as mock_confirm:
            # First attempt: no scheme
            # Second attempt: valid URL
            mock_text.return_value.ask.side_effect = ["example.com", "https://example.com"]
            mock_confirm.return_value.ask.return_value = True  # Retry

            result = prompt_url("Enter URL:")

            assert result == "https://example.com"


def test_prompt_file_validates_existence():
    """Test file prompt validation"""
    with patch('quarry.lib.prompts.questionary.path') as mock_path:
        with patch('quarry.lib.prompts.questionary.confirm') as mock_confirm:
            with patch('quarry.lib.prompts.Path') as mock_pathlib:
                # First attempt: file doesn't exist
                # Second attempt: file exists
                mock_path.return_value.ask.side_effect = [
                    "/nonexistent/file.txt",
                    "/exists/file.txt",
                ]
                mock_confirm.return_value.ask.return_value = True  # Retry

                # Mock Path.exists()
                mock_path_obj = MagicMock()
                mock_path_obj.exists.side_effect = [False, True]
                mock_path_obj.is_file.return_value = True
                mock_pathlib.return_value = mock_path_obj

                result = prompt_file("Enter file:")

                assert result == "/exists/file.txt"
