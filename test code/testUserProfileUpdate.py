import unittest
from unittest.mock import Mock, MagicMock
import mysql.connector
from datetime import datetime
from User import User


class TestProfileUpdateFunctionality(unittest.TestCase):
    """Test suite for profile update functionality"""
    
    def setUp(self):
        """Create a sample user for testing"""
        self.sample_user = User(
            email="test@example.com",
            passwordHash=User.hash_password("TestPass123!"),
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now(),
            userID=1
        )
        
        self.mock_db = Mock()
        self.mock_cursor = Mock()
    
    def test_update_first_name(self):
        """Test updating first name"""
        # Test implementation
        pass
    
    def test_change_password(self):
        """Test changing password"""
        # Test implementation
        pass
    
    @unittest.skip("Integration test - requires real database")
    def test_end_to_end_update(self):
        """Integration test for end-to-end update"""
        pass

    def test_update_first_name_success(self):
        """Test updating first name successfully"""
        # Setup
        user = User(email="test@example.com", fname="Old", lname="Doe", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Execute
        success, message = user.update_profile(
            fname="NewFirstName",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertTrue(success)
        self.assertIn("Profile updated successfully", message)
        self.assertEqual(user.get_fname(), "NewFirstName")
        mock_db.commit.assert_called_once()

    def test_update_last_name_success(self):
        """Test updating last name successfully"""
        # Setup
        user = User(email="test@example.com", fname="John", lname="Old", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Execute
        success, message = user.update_profile(
            lname="NewLastName",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertTrue(success)
        self.assertIn("Profile updated successfully", message)
        self.assertEqual(user.get_lname(), "NewLastName")

    def test_update_both_names_success(self):
        """Test updating both first and last name in one operation"""
        # Setup
        user = User(email="test@example.com", fname="OldFirst", lname="OldLast", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Execute
        success, message = user.update_profile(
            fname="NewFirst",
            lname="NewLast",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertTrue(success)
        self.assertIn("fname", message)
        self.assertIn("lname", message)
        self.assertEqual(user.get_fname(), "NewFirst")
        self.assertEqual(user.get_lname(), "NewLast")

    def test_change_password_success(self):
        """Test changing password with correct old password"""
        # Setup
        old_password = "OldPass123!"
        new_password = "NewPass456@"
        user = User(
            email="test@example.com",
            passwordHash=User.hash_password(old_password),
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now()
        )
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Execute
        success, message = user.change_password(
            old_password=old_password,
            new_password=new_password,
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertTrue(success)
        self.assertIn("Password Updated Successfully", message)
        self.assertTrue(User.verify_password(new_password, user.get_passwordHash()))
        mock_db.commit.assert_called_once()
    
    def test_change_password_wrong_old_password(self):
        """Test password change fails with incorrect old password"""
        # Setup
        user = User(
            email="test@example.com",
            passwordHash=User.hash_password("CorrectPass123!"),
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now()
        )
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Execute with wrong old password
        success, message = user.change_password(
            old_password="WrongPass123!",
            new_password="NewPass456@",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertFalse(success)
        self.assertIn("Old Password is incorrect", message)
        mock_cursor.execute.assert_not_called()

    def test_change_password_weak_password(self):
        """Test password change fails with weak new password"""
        # Setup
        user = User(
            email="test@example.com",
            passwordHash=User.hash_password("OldPass123!"),
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now()
        )
        mock_db = Mock()
        mock_cursor = Mock()
        
        weak_passwords = [
            ("short", "Password must be 8 characters long"),
            ("nouppercase123!", "Password must contain a uppercase letter"),
            ("NOLOWERCASE123!", "Password must contain a lowercase letter"),
            ("NoDigits!", "Password must contain a digit"),
            ("NoSpecial123", "Password must contain a special character"),
        ]
        
        for weak_pass, expected_error in weak_passwords:
            with self.subTest(password=weak_pass):
                success, message = user.change_password(
                    old_password="OldPass123!",
                    new_password=weak_pass,
                    dbConnection=mock_db,
                    cursor=mock_cursor
                )
                
                self.assertFalse(success)
                self.assertIn(expected_error, message)

    def test_name_update_reflected_immediately(self):
        """Test that name updates are reflected immediately in the object"""
        # Setup
        user = User(email="test@example.com", fname="John", lname="Doe", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        
        # Verify initial state
        self.assertEqual(user.get_fname(), "John")
        self.assertEqual(user.get_lname(), "Doe")
        
        # Update without database (simulating immediate UI update)
        success, message = user.update_profile(fname="Jane", lname="Smith")
        
        # Verify immediate reflection
        self.assertTrue(success)
        self.assertEqual(user.get_fname(), "Jane")
        self.assertEqual(user.get_lname(), "Smith")
        
        # Verify get_profile_info also reflects changes
        profile_info = user.get_profile_info()
        self.assertEqual(profile_info['fname'], "Jane")
        self.assertEqual(profile_info['lname'], "Smith")

    def test_name_update_persisted_to_database(self):
        """Test that name updates are persisted to database"""
        # Setup
        user = User(email="test@example.com", fname="Old", lname="Name", userID=1, passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        captured_query = None
        captured_params = None
        
        def capture_execute(query, params):
            nonlocal captured_query, captured_params
            captured_query = query
            captured_params = params
        
        mock_cursor.execute.side_effect = capture_execute
        
        # Execute
        success, message = user.update_profile(
            fname="UpdatedFirst",
            lname="UpdatedLast",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify database interaction
        self.assertTrue(success)
        self.assertIn("UPDATE bankUser SET", captured_query)
        self.assertIn("first_name=%s", captured_query)
        self.assertIn("last_name=%s", captured_query)
        self.assertEqual(captured_params[0], "UpdatedFirst")  # first_name value
        self.assertEqual(captured_params[1], "UpdatedLast")   # last_name value
        self.assertEqual(captured_params[2], 1)               # userID in WHERE clause
        mock_db.commit.assert_called_once()

    def test_password_update_persisted_to_database(self):
        """Test that password updates are persisted to database"""
        # Setup
        old_password = "OldPass123!"
        new_password = "NewPass456@"
        user = User(
            email="test@example.com",
            passwordHash=User.hash_password(old_password),
            userID=1,
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now()
        )
        mock_db = Mock()
        mock_cursor = Mock()
        
        captured_query = None
        captured_params = None
        
        def capture_execute(query, params):
            nonlocal captured_query, captured_params
            captured_query = query
            captured_params = params
        
        mock_cursor.execute.side_effect = capture_execute
        
        # Execute
        success, message = user.change_password(
            old_password=old_password,
            new_password=new_password,
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify database interaction
        self.assertTrue(success)
        self.assertIn("UPDATE bankUser SET password_hash = %s WHERE idbankUser = %s", captured_query)
        self.assertEqual(captured_params[0], user.get_passwordHash())  # new hashed password
        self.assertEqual(captured_params[1], 1)                       # userID
        mock_db.commit.assert_called_once()

    def test_combined_name_email_update(self):
        """Test updating name and email together"""
        # Setup
        user = User(email="old@example.com", fname="Old", lname="Name", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Execute
        success, message = user.update_profile(
            fname="NewFirst",
            lname="NewLast",
            email="new@example.com",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertTrue(success)
        self.assertEqual(user.get_fname(), "NewFirst")
        self.assertEqual(user.get_lname(), "NewLast")
        self.assertEqual(user.get_email(), "new@example.com")

    def test_name_update_invalid_characters(self):
        """Test name update with invalid characters"""
        # Setup
        user = User(email="test@example.com", fname="Valid", lname="Name", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        invalid_names = [
            "John123",      # Contains numbers
            "Mary@Doe",     # Contains @ symbol
            "Test_Name",    # Contains underscore
            "Bob*Smith",    # Contains asterisk
        ]
        
        for invalid_name in invalid_names:
            with self.subTest(name=invalid_name):
                success, message = user.update_profile(
                    fname=invalid_name,
                    dbConnection=mock_db,
                    cursor=mock_cursor
                )
                
                self.assertFalse(success)
                self.assertIn("contains invalid characters", message)
                mock_cursor.execute.assert_not_called()
    
    def test_name_update_length_constraints(self):
        """Test name update with length violations"""
        # Setup
        user = User(email="test@example.com", fname="Valid", lname="Name", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Test too short
        success, message = user.update_profile(fname="A", dbConnection=mock_db, cursor=mock_cursor)
        self.assertFalse(success)
        self.assertIn("must be at least 2 characters", message)
        
        # Test too long
        long_name = "A" * 51
        success, message = user.update_profile(fname=long_name, dbConnection=mock_db, cursor=mock_cursor)
        self.assertFalse(success)
        self.assertIn("must be less than 50 characters", message)
        
        # Test valid length
        valid_name = "A" * 50  # Exactly 50 characters
        success, message = user.update_profile(fname=valid_name, dbConnection=mock_db, cursor=mock_cursor)
        self.assertTrue(success)

    def test_name_update_empty_or_whitespace(self):
        """Test name update with empty or whitespace-only values"""
        # Setup
        user = User(email="test@example.com", fname="Valid", lname="Name", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        empty_values = ["", "   ", "\t", "\n"]
        
        for empty_val in empty_values:
            with self.subTest(value=repr(empty_val)):
                success, message = user.update_profile(
                    fname=empty_val,
                    dbConnection=mock_db,
                    cursor=mock_cursor
                )
                
                self.assertFalse(success)
                self.assertIn("cannot be empty", message)
                mock_cursor.execute.assert_not_called()

    def test_name_update_transaction_rollback(self):
        """Test that failed name updates are rolled back"""
        # Setup
        user = User(email="test@example.com", fname="Old", lname="Name", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Simulate database error during update
        mock_cursor.execute.side_effect = Exception("Database connection lost")
        
        # Execute
        success, message = user.update_profile(
            fname="NewName",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertFalse(success)
        mock_db.rollback.assert_called_once()

    def test_password_change_transaction_rollback(self):
        """Test that failed password changes are rolled back"""
        # Setup
        user = User(
            email="test@example.com",
            passwordHash=User.hash_password("OldPass123!"),
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now()
        )
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Simulate database error
        mock_cursor.execute.side_effect = Exception("Database error")
        
        # Execute
        success, message = user.change_password(
            old_password="OldPass123!",
            new_password="NewPass456@",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertFalse(success)
        mock_db.rollback.assert_called_once()

    def test_acceptance_criteria_update_name(self):
        """AC: Users should be able to update their first and last name"""
        # Setup
        user = User(email="user@example.com", fname="Original", lname="User", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Execute - update name
        success, message = user.update_profile(
            fname="Updated",
            lname="Username",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertTrue(success)
        self.assertEqual(user.get_fname(), "Updated")
        self.assertEqual(user.get_lname(), "Username")
        mock_db.commit.assert_called_once()

    def test_acceptance_criteria_change_password(self):
        """AC: Users should be able to change their password"""
        # Setup
        old_password = "OldPassword123!"
        new_password = "NewPassword456@"
        user = User(
            email="user@example.com",
            passwordHash=User.hash_password(old_password),
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now()
        )
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Execute - change password
        success, message = user.change_password(
            old_password=old_password,
            new_password=new_password,
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertTrue(success)
        self.assertTrue(User.verify_password(new_password, user.get_passwordHash()))
        self.assertFalse(User.verify_password(old_password, user.get_passwordHash()))
        mock_db.commit.assert_called_once()

    def test_acceptance_criteria_changes_persist(self):
        """AC: Changes should persist after page refresh (database storage)"""
        # Setup
        user = User(email="user@example.com", fname="Before", lname="Update", userID=1, passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        executed_queries = []
        
        def capture_execute(query, params):
            executed_queries.append((query, params))
        
        mock_cursor.execute.side_effect = capture_execute
        
        # Execute - make changes
        success, message = user.update_profile(
            fname="After",
            lname="Update",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify database was called to persist
        self.assertTrue(success)
        self.assertEqual(len(executed_queries), 1)
        query, params = executed_queries[0]
        self.assertIn("UPDATE bankUser", query)
        mock_db.commit.assert_called_once()

    def test_acceptance_criteria_immediate_reflection(self):
        """AC: Changes should be reflected immediately on the page"""
        # Setup
        user = User(email="test@example.com", fname="Before", lname="Change", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        
        # Execute - update without committing to DB
        success, message = user.update_profile(fname="After", lname="Change")
        
        # Verify immediate update in object
        self.assertTrue(success)
        self.assertEqual(user.get_fname(), "After")
        
        # Simulate page displaying profile
        displayed_name = f"{user.get_fname()} {user.get_lname()}"
        self.assertEqual(displayed_name, "After Change")


if __name__ == '__main__':
    unittest.main()