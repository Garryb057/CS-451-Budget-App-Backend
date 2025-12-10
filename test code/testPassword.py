import unittest
from unittest.mock import Mock, patch, MagicMock
from User import User
import bcrypt
from datetime import datetime

class TestPasswordStrengthValidation(unittest.TestCase):
    """Test the validate_strong_password static method"""
    
    def test_valid_strong_password(self):
        """Test a password that meets all strength criteria"""
        test_passwords = [
            "StrongPass123!",
            "Another@Pass456",
            "Test#Password789",
            "Valid$Password2024"
        ]
        
        for password in test_passwords:
            with self.subTest(password=password):
                result, message = User.validate_strong_password(password)
                self.assertTrue(result, f"Password '{password}' should be valid: {message}")
                self.assertEqual(message, "Password is strong")
    
    def test_password_too_short(self):
        """Test passwords that are too short"""
        test_passwords = [
            "Sh0rt!",  # 6 chars
            "Aa1!",    # 4 chars
            "",        # Empty
            "A"        # 1 char
        ]
        
        for password in test_passwords:
            with self.subTest(password=password):
                result, message = User.validate_strong_password(password)
                self.assertFalse(result)
                self.assertIn("must be 8 characters long", message)
    
    def test_password_missing_uppercase(self):
        """Test passwords without uppercase letters"""
        test_passwords = [
            "lowercase123!",
            "alllower123@",
            "nouppercase456#"
        ]
        
        for password in test_passwords:
            with self.subTest(password=password):
                result, message = User.validate_strong_password(password)
                self.assertFalse(result)
                self.assertIn("must contain a uppercase letter", message)
    
    def test_password_missing_lowercase(self):
        """Test passwords without lowercase letters"""
        test_passwords = [
            "ALLUPPER123!",
            "UPPERCASE456@",
            "NO_LOWERCASE789#"
        ]
        
        for password in test_passwords:
            with self.subTest(password=password):
                result, message = User.validate_strong_password(password)
                self.assertFalse(result)
                self.assertIn("must contain a lowercase letter", message)
    
    def test_password_missing_digit(self):
        """Test passwords without digits"""
        test_passwords = [
            "NoDigits!",
            "PasswordWithoutNumbers@",
            "Special#Only"
        ]
        
        for password in test_passwords:
            with self.subTest(password=password):
                result, message = User.validate_strong_password(password)
                self.assertFalse(result)
                self.assertIn("must contain a digit", message)
    
    def test_password_missing_special_character(self):
        """Test passwords without special characters"""
        test_passwords = [
            "NoSpecial123",
            "Password456",
            "OnlyAlphaNumeric789"
        ]
        
        for password in test_passwords:
            with self.subTest(password=password):
                result, message = User.validate_strong_password(password)
                self.assertFalse(result)
                self.assertIn("must contain a special character", message)
    
    def test_password_with_only_special_chars(self):
        """Test passwords with only special characters (missing other requirements)"""
        test_passwords = [
            "!@#$%^&*",
            "_________",
            "........"
        ]
        
        for password in test_passwords:
            with self.subTest(password=password):
                result, message = User.validate_strong_password(password)
                self.assertFalse(result)
                # Should fail on multiple criteria
    
    def test_password_edge_cases(self):
        """Test edge cases for password validation"""
        # Exactly 8 characters with all requirements
        result, message = User.validate_strong_password("Aa1!Bb2@")
        self.assertTrue(result)
        
        # Unicode characters in password
        result, message = User.validate_strong_password("P@sswörd123")
        self.assertTrue(result)
        
        # Password with spaces (not allowed by current regex)
        result, message = User.validate_strong_password("Pass 123!")
        # Current implementation doesn't explicitly forbid spaces
        # Let's see what happens
        print(f"Password with spaces: {result}, {message}")
    
    def test_password_common_weak_patterns(self):
        """Test common weak password patterns"""
        weak_passwords = [
            "password123!",  # Contains "password"
            "12345678!",     # Sequential numbers
            "qwerty123!",    # Keyboard pattern
            "admin123!",     # Common word
            "letmein123!",   # Common phrase
        ]
        
        for password in weak_passwords:
            with self.subTest(password=password):
                # Current implementation doesn't check for common weak patterns
                # These might pass the technical requirements
                result, message = User.validate_strong_password(password)
                # They should technically pass current validation
                self.assertTrue(result, f"Password '{password}' passes technical validation")
    
    def test_password_with_emoji(self):
        """Test passwords containing emojis"""
        test_passwords = [
            "Pass123😀",  # Emoji at end
            "🔑Pass123!",  # Emoji at start
            "Pass👍123!"   # Emoji in middle
        ]
        
        for password in test_passwords:
            with self.subTest(password=password):
                # Current regex might or might not handle emojis
                result, message = User.validate_strong_password(password)
                print(f"Emoji password '{password}': {result}, {message}")

class TestPasswordHashing(unittest.TestCase):
    """Test password hashing and verification methods"""
    
    def test_hash_password_success(self):
        """Test successful password hashing"""
        password = "TestPassword123!"
        
        hashed = User.hash_password(password)
        
        self.assertIsNotNone(hashed)
        self.assertIsInstance(hashed, str)
        self.assertTrue(len(hashed) > 0)
        # bcrypt hashes start with $2b$
        self.assertTrue(hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$"))
    
    def test_hash_empty_password(self):
        """Test hashing empty password"""
        hashed = User.hash_password("")
        
        self.assertEqual(hashed, "")
    
    def test_hash_none_password(self):
        """Test hashing None password"""
        hashed = User.hash_password(None)
        
        self.assertEqual(hashed, "")
    
    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "CorrectPassword123!"
        hashed = User.hash_password(password)
        
        result = User.verify_password(password, hashed)
        
        self.assertTrue(result)
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "CorrectPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = User.hash_password(password)
        
        result = User.verify_password(wrong_password, hashed)
        
        self.assertFalse(result)
    
    def test_verify_password_empty(self):
        """Test verifying empty password"""
        password = "TestPassword123!"
        hashed = User.hash_password(password)
        
        result = User.verify_password("", hashed)
        
        self.assertFalse(result)
    
    def test_verify_password_none(self):
        """Test verifying None password"""
        password = "TestPassword123!"
        hashed = User.hash_password(password)
        
        result = User.verify_password(None, hashed)
        
        self.assertFalse(result)
    
    def test_hash_verify_round_trip(self):
        """Test that hashing and verifying work correctly together"""
        test_passwords = [
            "Simple123!",
            "VeryLongPasswordWithSpecialChars@123",
            "MixedCase123#",
            "P@$$w0rd123"
        ]
        
        for password in test_passwords:
            with self.subTest(password=password):
                hashed = User.hash_password(password)
                self.assertTrue(User.verify_password(password, hashed))
                # Verify wrong password fails
                self.assertFalse(User.verify_password(password + "extra", hashed))
    
    def test_password_hashing_salt_uniqueness(self):
        """Test that each hash uses unique salt"""
        password = "SamePassword123!"
        
        hash1 = User.hash_password(password)
        hash2 = User.hash_password(password)
        
        # Hashes should be different due to different salts
        self.assertNotEqual(hash1, hash2)
        
        # But both should verify correctly
        self.assertTrue(User.verify_password(password, hash1))
        self.assertTrue(User.verify_password(password, hash2))

class TestChangePasswordMethod(unittest.TestCase):
    """Test the change_password method"""
    
    def setUp(self):
        """Set up test user with mock database"""
        self.user = User(
            email="test@example.com",
            passwordHash=User.hash_password("CurrentPass123!"),
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now(),
            userID=123
        )
        
        # Mock database objects
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_connection.cursor.return_value = self.mock_cursor
    
    def test_successful_password_change(self):
        """Test successful password change with valid old and new passwords"""
        # Mock successful database update
        self.mock_cursor.execute.return_value = None
        self.mock_connection.commit.return_value = None
        
        result, message = self.user.change_password(
            "CurrentPass123!",  # Correct old password
            "NewStrongPass456@",  # Strong new password
            self.mock_connection,
            self.mock_cursor
        )
        
        self.assertTrue(result)
        self.assertEqual(message, "Password Updated Successfully")
        
        # Verify database was updated
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_called_once()
        
        # Verify user's password hash was updated
        self.assertNotEqual(self.user.passwordHash, User.hash_password("CurrentPass123!"))
        # New password should verify
        self.assertTrue(User.verify_password("NewStrongPass456@", self.user.passwordHash))
    
    def test_change_password_wrong_old_password(self):
        """Test password change with incorrect old password"""
        result, message = self.user.change_password(
            "WrongOldPass123!",  # Incorrect old password
            "NewStrongPass456@",  # Strong new password
            self.mock_connection,
            self.mock_cursor
        )
        
        self.assertFalse(result)
        self.assertEqual(message, "Old Password is incorrect")
        
        # Verify database was NOT called
        self.mock_cursor.execute.assert_not_called()
        self.mock_connection.commit.assert_not_called()
        
        # Verify password hash unchanged
        self.assertTrue(User.verify_password("CurrentPass123!", self.user.passwordHash))
    
    def test_change_password_weak_new_password(self):
        """Test password change with weak new password"""
        weak_passwords = [
            "weak",            # Too short
            "nouppercase123!", # No uppercase
            "NOLOWERCASE123!", # No lowercase
            "NoDigits!",       # No digits
            "NoSpecial123"     # No special characters
        ]
        
        for weak_password in weak_passwords:
            with self.subTest(password=weak_password):
                # Reset mocks for each test
                self.mock_cursor.reset_mock()
                self.mock_connection.reset_mock()
                
                result, message = self.user.change_password(
                    "CurrentPass123!",
                    weak_password,
                    self.mock_connection,
                    self.mock_cursor
                )
                
                self.assertFalse(result)
                self.assertIn("Password must", message)
                
                # Verify database was NOT called
                self.mock_cursor.execute.assert_not_called()
                self.mock_connection.commit.assert_not_called()
    
    def test_change_password_same_as_old(self):
        """Test changing password to same as old password"""
        # This should fail because new password must be different
        # Current implementation doesn't check this
        result, message = self.user.change_password(
            "CurrentPass123!",
            "CurrentPass123!",  # Same as old
            self.mock_connection,
            self.mock_cursor
        )
        
        # It will pass validation but should we allow it?
        # For security, we should reject same password
        print(f"Same password change: {result}, {message}")
        # This is a security gap - should add this check
    
    def test_change_password_similar_to_old(self):
        """Test changing password to similar password"""
        similar_passwords = [
            "CurrentPass123!1",  # Old + 1
            "CurrentPass123",    # Old without special char
            "currentpass123!",   # All lowercase version
            "CURRENTPASS123!"    # All uppercase version
        ]
        
        for similar_password in similar_passwords:
            with self.subTest(password=similar_password):
                # Current implementation doesn't check similarity
                result, message = self.user.change_password(
                    "CurrentPass123!",
                    similar_password,
                    self.mock_connection,
                    self.mock_cursor
                )
                
                # These should pass current validation but are security risks
                print(f"Similar password '{similar_password}': {result}, {message}")
    
    def test_change_password_database_error(self):
        """Test password change when database update fails"""
        # Mock database error
        self.mock_cursor.execute.side_effect = Exception("Database error")
        
        result, message = self.user.change_password(
            "CurrentPass123!",
            "NewStrongPass456@",
            self.mock_connection,
            self.mock_cursor
        )
        
        self.assertFalse(result)
        self.assertIn("Error updating password", message)
        
        # Verify rollback was called
        self.mock_connection.rollback.assert_called_once()
        
        # Verify password hash unchanged
        self.assertTrue(User.verify_password("CurrentPass123!", self.user.passwordHash))
    
    def test_change_password_hashing_error(self):
        """Test password change when hashing fails"""
        with patch.object(User, 'hash_password', return_value=""):
            result, message = self.user.change_password(
                "CurrentPass123!",
                "NewStrongPass456@",
                self.mock_connection,
                self.mock_cursor
            )
            
            self.assertFalse(result)
            self.assertEqual(message, "Error hashing new password")
            
            # Verify database was NOT called
            self.mock_cursor.execute.assert_not_called()
            self.mock_connection.commit.assert_not_called()
    
    def test_change_password_with_special_characters(self):
        """Test password change with various special characters"""
        special_char_passwords = [
            "Pass123!@#$%^&*",
            "Test#Password$123",
            "Complex@Pass(123)",
            "Special[Pass]123",
            "Unusual|Pass~123"
        ]
        
        for password in special_char_passwords:
            with self.subTest(password=password):
                # Reset mocks
                self.mock_cursor.reset_mock()
                self.mock_connection.reset_mock()
                self.mock_cursor.execute.return_value = None
                
                result, message = self.user.change_password(
                    "CurrentPass123!",
                    password,
                    self.mock_connection,
                    self.mock_cursor
                )
                
                # Check if password passes current validation
                # Some special chars might not be in the regex pattern
                strong_result, _ = User.validate_strong_password(password)
                
                if strong_result:
                    self.assertTrue(result, f"Password '{password}' should pass")
                    self.assertEqual(message, "Password Updated Successfully")
                else:
                    self.assertFalse(result)
                    self.assertIn("Password must", message)

class TestAcceptanceCriteria(unittest.TestCase):
    """Direct tests for acceptance criteria"""
    
    def test_ac_current_password_verification(self):
        """AC: Verify current password is checked"""
        user = User(
            email="ac@example.com",
            passwordHash=User.hash_password("Current123!"),
            fname="AC",
            lname="Test",
            phoneNumber="5550001111",
            dateCreated=datetime.now(),
            userID=1001
        )
        
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Wrong current password should fail
        result, message = user.change_password(
            "WrongCurrent123!",
            "NewPass456@",
            mock_conn,
            mock_cursor
        )
        self.assertFalse(result)
        self.assertEqual(message, "Old Password is incorrect")
        mock_cursor.execute.assert_not_called()
    
    def test_ac_password_strength_rules(self):
        """AC: New password must pass strength rules"""
        user = User(
            email="strength@example.com",
            passwordHash=User.hash_password("Current123!"),
            fname="Strength",
            lname="Test",
            phoneNumber="5552223333",
            dateCreated=datetime.now(),
            userID=1002
        )
        
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Test each strength rule failure
        test_cases = [
            ("short", "Too short"),
            ("NOLOWER123!", "No lowercase"),
            ("noupper123!", "No uppercase"),
            ("NoDigits!", "No digits"),
            ("NoSpecial123", "No special character")
        ]
        
        for weak_password, description in test_cases:
            with self.subTest(description=description):
                mock_cursor.reset_mock()
                
                result, message = user.change_password(
                    "Current123!",
                    weak_password,
                    mock_conn,
                    mock_cursor
                )
                self.assertFalse(result, f"'{weak_password}' should fail: {message}")
                self.assertIn("Password must", message)
                mock_cursor.execute.assert_not_called()
    
    def test_ac_successful_password_update(self):
        """AC: Successful password update"""
        user = User(
            email="success@example.com",
            passwordHash=User.hash_password("OldPass123!"),
            fname="Success",
            lname="Test",
            phoneNumber="5553334444",
            dateCreated=datetime.now(),
            userID=1003
        )
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.return_value = None
        
        strong_password = "NewStrongPass456@"
        result, message = user.change_password(
            "OldPass123!",
            strong_password,
            mock_conn,
            mock_cursor
        )
        
        self.assertTrue(result)
        self.assertEqual(message, "Password Updated Successfully")
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        
        # Verify new password works
        self.assertTrue(User.verify_password(strong_password, user.passwordHash))
        # Verify old password doesn't work
        self.assertFalse(User.verify_password("OldPass123!", user.passwordHash))