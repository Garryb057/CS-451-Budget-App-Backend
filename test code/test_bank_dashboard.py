import unittest
from unittest.mock import MagicMock, patch
import time
import BankDashboard as bd


class TestBankDashboard(unittest.TestCase):

    def setUp(self):
        # Reset session before each test
        bd.SESSION["token"] = None
        bd.SESSION["last_active"] = None

    @patch("BankDashboard.tk.StringVar")
    @patch("BankDashboard.tk.Toplevel")
    def test_open_dashboard_creates_token_and_session(self, mock_toplevel, mock_stringvar):
        mock_root = MagicMock()
        mock_logout_callback = MagicMock()

        # Prepare StringVar mock to accept .set()
        mock_sv = MagicMock()
        mock_stringvar.return_value = mock_sv

        # Prepare cursor to return a balance.
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (123.45,)
        mock_db = MagicMock()

        # call with the current signature: (root, first_name, last_name, user_id, logout_callback, ...)
        bd.open_dashboard(mock_root, "John", "Doe", 1, mock_logout_callback, settings_callback=None, db=mock_db, cursor=mock_cursor)

        self.assertIsNotNone(bd.SESSION["token"])
        self.assertIsNotNone(bd.SESSION["last_active"])
        # ensure we attempted to read balance
        mock_cursor.execute.assert_called()

    def test_update_activity_refreshes_timestamp(self):
        old_time = time.time() - 100
        bd.SESSION["last_active"] = old_time
        bd.update_activity()
        self.assertGreater(bd.SESSION["last_active"], old_time)

    def test_logout_resets_session(self):
        bd.SESSION["token"] = "abc123"
        bd.SESSION["last_active"] = time.time()

        mock_dashboard = MagicMock()
        mock_root = MagicMock()
        mock_callback = MagicMock()

        bd.logout(mock_dashboard, mock_root, mock_callback)

        # Should clear session and destroy dashboard
        self.assertIsNone(bd.SESSION["token"])
        self.assertIsNone(bd.SESSION["last_active"])
        mock_dashboard.destroy.assert_called_once()
        mock_callback.assert_called_once_with(mock_root)

    @patch("BankDashboard.messagebox.showinfo")
    def test_check_inactivity_triggers_logout(self, mock_msgbox):
        # Set old session timestamp
        bd.SESSION["last_active"] = time.time() - (bd.SESSION_TIMEOUT + 10)

        mock_window = MagicMock()
        mock_root = MagicMock()
        mock_callback = MagicMock()

        bd.check_inactivity(mock_window, mock_root, mock_callback)

        mock_msgbox.assert_called_once()
        mock_callback.assert_called_once_with(mock_root)


if __name__ == "__main__":
    unittest.main()