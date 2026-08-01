from unittest.mock import patch, MagicMock
import pytest
from app.services.auth import register_user
from app.services.auth import login_user


class TestUser:
    @patch("app.services.auth.db")
    @patch("app.services.auth.hash_pw")
    @patch("app.services.auth.helper_email")
    @patch("app.services.auth.helper_name")
    def test_registration_success(self, mock_name, mock_pw, mock_email, mock_db):
        mock_name.return_value = True
        mock_email.return_value = True
        mock_pw.return_value = "hashed_password_123"
        mock_session = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_session

        result = register_user("Test User", "test@example.com", "TestPass123!")

        assert result is True
        mock_session.execute.assert_called_once()

    @patch("app.services.auth.bcrypt")
    @patch("app.services.auth.db")
    def test_login_success(self, mock_db, mock_bcrypt):
        mock_user = MagicMock()
        mock_user.user_id = "some-uuid-1234"
        mock_user.email = "test@example.com"
        mock_user.password = "hashed_password_123"

        mock_session = MagicMock()
        mock_session.scalar.return_value = mock_user
        mock_db.return_value.__enter__.return_value = mock_session

        mock_bcrypt.checkpw.return_value = True

        result = login_user("test@example.com", "TestPass123!")

        assert result == ("some-uuid-1234", "test@example.com")

