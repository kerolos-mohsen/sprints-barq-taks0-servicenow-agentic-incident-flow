"""Unit tests for webhook authentication and security."""

from src.core.security import verify_webhook_secret


class TestSecurity:
    """Tests for constant-time webhook secret verification."""

    def test_correct_secret_returns_true(self):
        assert verify_webhook_secret("my-super-secret", "my-super-secret") is True

    def test_incorrect_secret_returns_false(self):
        assert verify_webhook_secret("wrong-secret", "my-super-secret") is False

    def test_none_secret_returns_false(self):
        assert verify_webhook_secret(None, "my-super-secret") is False

    def test_empty_string_mismatch(self):
        assert verify_webhook_secret("", "my-super-secret") is False

    def test_prefix_match_returns_false(self):
        assert verify_webhook_secret("my-super", "my-super-secret") is False
