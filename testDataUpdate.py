import unittest
from unittest.mock import Mock, MagicMock
import mysql.connector
from datetime import datetime
from User import User


class TestProfileUpdate(unittest.TestCase):
    """Test suite for profile update functionality"""
    
    def setUp(self):
        """Create a sample user for testing"""
        self.sample_user = User(
            email="test@example.com",
            passwordHash="hashed_password",
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now(),
            userID=1
        )
        
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
    
    def test_update_single_field(self):
        """Test updating a single field"""
        pass

    def test_update_profile_single_field_success(self):
        """Test updating a single profile field successfully"""
        # Setup
        user = User(email="test@example.com", passwordHash="hash", fname="John", lname="Doe", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Mock successful database update
        mock_cursor.execute.return_value = None
        mock_db.commit.return_value = None
        
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

    def test_update_profile_multiple_fields_success(self):
        """Test updating multiple profile fields in a single transaction"""
        # Setup
        user = User(email="test@example.com", passwordHash="hash", fname="John", lname="Doe", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Execute
        success, message = user.update_profile(
            fname="NewFirst",
            lname="NewLast",
            email="new@example.com",
            phoneNumber="1234567890",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertTrue(success)
        self.assertIn("Profile updated successfully", message)
        self.assertTrue(all(field in message for field in ['fname', 'lname', 'email', 'phoneNumber']))
        mock_db.commit.assert_called_once()
        # Verify all fields were updated in object
        self.assertEqual(user.get_fname(), "NewFirst")
        self.assertEqual(user.get_lname(), "NewLast")
        self.assertEqual(user.get_email(), "new@example.com")
        self.assertEqual(user.get_phoneNumber(), "1234567890")

    def test_update_profile_partial_update_prevention(self):
        """Test that invalid data prevents any updates (data integrity)"""
        # Setup
        original_email = "test@example.com"
        original_fname = "Original"
        user = User(email=original_email, fname=original_fname, passwordHash="hash", lname="Doe", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Execute with one valid and one invalid field
        success, message = user.update_profile(
            fname="ValidName",
            email="invalid-email",  # Invalid email format
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertFalse(success)
        self.assertIn("Invalid email format", message)
        mock_db.commit.assert_not_called()  # No commit should happen
        mock_db.rollback.assert_not_called()  # No rollback needed since no update attempted
        # Verify object state unchanged
        self.assertEqual(user.get_email(), original_email)
        self.assertEqual(user.get_fname(), original_fname)  # Even valid field should not be updated

    def test_update_profile_duplicate_email_rollback(self):
        """Test that duplicate email constraint triggers rollback"""
        # Setup
        user = User(email="test@example.com", passwordHash="hash", fname="John", lname="Doe", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Mock database duplicate entry error (MySQL error 1062)
        from mysql.connector import Error
        mock_cursor.execute.side_effect = Error(errno=1062, msg="Duplicate entry")
        
        # Execute
        success, message = user.update_profile(
            email="duplicate@example.com",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertFalse(success)
        self.assertIn("already in use", message)
        mock_db.rollback.assert_called_once()  # Should rollback on error

    def test_update_profile_transaction_atomicity(self):
        """Test that either all updates succeed or none do"""
        # Setup
        original_data = {"fname": "Old", "lname": "Name", "email": "old@example.com"}
        user = User(email=original_data["email"], fname=original_data["fname"], lname=original_data["lname"], passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Simulate database failure after partial execution (unlikely but testing atomicity)
        call_count = 0
        def mock_execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First execute succeeds
                return None
            else:  # Second execute fails
                raise Exception("Database failure")
        
        mock_cursor.execute.side_effect = mock_execute_side_effect
        
        # Execute
        success, message = user.update_profile(
            fname="NewFirst",
            lname="NewLast",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertFalse(success)
        mock_db.rollback.assert_called_once()  # Should rollback
        # Verify object state unchanged
        self.assertEqual(user.get_fname(), original_data["fname"])
        self.assertEqual(user.get_lname(), original_data["lname"])

    def test_update_profile_no_valid_updates(self):
        """Test handling when no valid update fields are provided"""
        # Setup
        user = User(email="test@example.com", passwordHash="hash", fname="John", lname="Doe", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Execute with None values
        success, message = user.update_profile(
            fname=None,
            lname=None,
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertFalse(success)
        self.assertIn("No valid updates provided", message)
        mock_cursor.execute.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_update_profile_field_validation(self):
        """Test that all field validations are applied"""
        test_cases = [
            {
                "field": "email",
                "value": "not-an-email",
                "expected_error": "Invalid email format"
            },
            {
                "field": "fname",
                "value": "A",  # Too short
                "expected_error": "must be at least 2 characters"
            },
            {
                "field": "lname",
                "value": "",  # Empty
                "expected_error": "cannot be empty"
            },
            {
                "field": "phoneNumber",
                "value": "123",  # Too short
                "expected_error": "too short"
            },
            {
                "field": "phoneNumber",
                "value": "not-a-phone",
                "expected_error": "must contain only digits"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(field=test_case["field"], value=test_case["value"]):
                user = User(email="test@example.com", passwordHash="hash", fname="John", lname="Doe", phoneNumber="1234567890", dateCreated=datetime.now())
                mock_db = Mock()
                mock_cursor = Mock()
                
                # Build update parameters dynamically
                update_params = {test_case["field"]: test_case["value"]}
                
                # Execute
                success, message = user.update_profile(
                    dbConnection=mock_db,
                    cursor=mock_cursor,
                    **update_params
                )
                
                # Verify
                self.assertFalse(success)
                self.assertIn(test_case["expected_error"].lower(), message.lower())
                mock_cursor.execute.assert_not_called()

    def test_update_profile_concurrent_modification(self):
        """Test behavior when profile is modified concurrently"""
        # Setup
        user = User(email="test@example.com", passwordHash="hash", fname="John", lname="Doe", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Mock optimistic locking failure (simulated by general database error)
        mock_cursor.execute.side_effect = Exception("Row modified by another transaction")
        
        # Execute
        success, message = user.update_profile(
            fname="NewName",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertFalse(success)
        self.assertIn("Error updating profile", message)
        mock_db.rollback.assert_called_once()

    def test_update_profile_object_state_consistency(self):
        """Test that object state remains consistent with database"""
        # Setup
        user = User(email="old@example.com", fname="Old", lname="Name", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
        mock_db = Mock()
        mock_cursor = Mock()
        
        # Track what was actually written to database
        executed_sql = []
        executed_params = []
        
        def capture_execute(sql, params):
            executed_sql.append(sql)
            executed_params.append(params)
        
        mock_cursor.execute.side_effect = capture_execute
        
        # Execute
        success, message = user.update_profile(
            fname="NewFirst",
            lname="NewLast",
            dbConnection=mock_db,
            cursor=mock_cursor
        )
        
        # Verify
        self.assertTrue(success)
        # Check that object state matches what was sent to database
        self.assertEqual(user.get_fname(), "NewFirst")
        self.assertEqual(user.get_lname(), "NewLast")
        # Verify database update parameters match object state
        self.assertIn("first_name=%s", executed_sql[0])
        self.assertIn("last_name=%s", executed_sql[0])
        self.assertEqual(executed_params[0][0], "NewFirst")  # First parameter value
        self.assertEqual(executed_params[0][1], "NewLast")   # Second parameter value

    def test_update_profile_special_characters(self):
        """Test updating names with special characters and edge cases"""
        test_cases = [
            {"fname": "Jean-Pierre", "lname": "O'Connor"},
            {"fname": "María", "lname": "García"},
            {"fname": "John", "lname": "Smith-Jones"},
            {"fname": "Li", "lname": "王"},  # Non-Latin characters
        ]
        
        for test_data in test_cases:
            with self.subTest(fname=test_data["fname"], lname=test_data["lname"]):
                user = User(fname="Old", lname="Name", email="test@example.com", passwordHash="hash", phoneNumber="1234567890", dateCreated=datetime.now())
                mock_db = Mock()
                mock_cursor = Mock()
                
                # Execute
                success, message = user.update_profile(
                    fname=test_data["fname"],
                    lname=test_data["lname"],
                    dbConnection=mock_db,
                    cursor=mock_cursor
                )
                
                # Verify
                self.assertTrue(success)
                self.assertEqual(user.get_fname(), test_data["fname"])
                self.assertEqual(user.get_lname(), test_data["lname"])

    @unittest.skip("Requires real database connection")
    def test_integration_profile_update_flow(self):
        """Full integration test of profile update from UI to database"""
        # Setup real database connection (use test database)
        db_config = {}
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Create test user
            user = User(
                email="integration@test.com",
                passwordHash=User.hash_password("password123"),
                fname="Initial",
                lname="User",
                phoneNumber="1234567890",
                dateCreated=datetime.now()
            )
            
            # Register user
            success, msg = user.register(connection, cursor)
            self.assertTrue(success)
            
            # Update profile
            success, msg = user.update_profile(
                fname="Updated",
                lname="Profile",
                email="updated@test.com",
                phoneNumber="0987654321",
                dbConnection=connection,
                cursor=cursor
            )
            
            self.assertTrue(success)
            
            # Verify in database
            cursor.execute(
                "SELECT first_name, last_name, email, phone_number FROM bankUser WHERE idbankUser = %s",
                (user.get_userID(),)
            )
            db_data = cursor.fetchone()
            
            self.assertEqual(db_data["first_name"], "Updated")
            self.assertEqual(db_data["last_name"], "Profile")
            self.assertEqual(db_data["email"], "updated@test.com")
            self.assertEqual(db_data["phone_number"], "0987654321")
            
        finally:
            # Cleanup
            cursor.execute("DELETE FROM bankUser WHERE email LIKE %s", ("%test.com",))
            connection.commit()
            cursor.close()
            connection.close()


if __name__ == '__main__':
    unittest.main()