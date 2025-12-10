import unittest
from unittest.mock import MagicMock, patch

import BankUser as bu


class TestBankLogin(unittest.TestCase):

    def setUp(self):
        # Ensure module-level entries are simple mocks
        bu.entry_email = MagicMock()
        bu.entry_password = MagicMock()

    @patch('BankUser.bcrypt.checkpw', return_value=True)
    def test_login_success_calls_open_dashboard(self, mock_checkpw):
        # Prepare email/password inputs
        bu.entry_email.get.return_value = 'test@example.com'
        bu.entry_password.get.return_value = 'correcthorsebatterystaple'

        # Prepare cursor to return a user row: (id, first_name, last_name, password_hash)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (42, 'Alice', 'Smith', 'hashedpw')

        # Patch module cursor and db, and patch open_dashboard and messagebox.
        bu.cursor = mock_cursor
        bu.db = MagicMock()

        with patch('BankDashboard.open_dashboard') as mock_open_dash, \
                patch('BankUser.messagebox.showinfo') as mock_info:

            bu.login_user()

            # open_dashboard should be called once with expected positional args
            mock_open_dash.assert_called_once()
            call_args = mock_open_dash.call_args
            # positional args: root, first_name, last_name, user_id, logout_callback
            self.assertEqual(call_args[0][1], 'Alice')
            self.assertEqual(call_args[0][2], 'Smith')
            self.assertEqual(call_args[0][3], 42)

            # current_user_email should be set
            self.assertEqual(bu.current_user_email, 'test@example.com')

            # messagebox.showinfo should have been used to welcome the user
            mock_info.assert_called()

    def test_login_failure_shows_error(self):
        # Simulate no matching user
        bu.entry_email.get.return_value = 'nouser@example.com'
        bu.entry_password.get.return_value = 'irrelevant'

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        bu.cursor = mock_cursor

        with patch('BankUser.messagebox.showerror') as mock_error:
            bu.login_user()
            mock_error.assert_called_once()


if __name__ == '__main__':
    unittest.main()
