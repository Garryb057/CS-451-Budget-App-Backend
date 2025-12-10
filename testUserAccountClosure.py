import unittest
from unittest.mock import Mock, patch, MagicMock
from User import User
import bcrypt
from datetime import datetime

class TestAccountClosureValidation(unittest.TestCase):
    
    def setUp(self):
        """Set up test user"""
        self.user = User(
            email="test@example.com",
            passwordHash="hashed_password",
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now(),
            userID=123
        )
    
    def test_validate_deletion_prereq_no_issues(self):
        """Test validation when no prerequisites are blocking"""
        # Setup: No disputes and positive balance
        self.user.disputes = []
        self.user.balance = 100.0
        
        result, message = self.user.validate_deletion_prereq()
        
        self.assertTrue(result)
        self.assertEqual(message, "All prerequisites met. Account can be closed.")
    
    def test_validate_deletion_prereq_pending_disputes(self):
        """Test validation when user has pending disputes"""
        # Setup: Add pending dispute
        self.user.add_dispute(1, "Dispute about transaction", "pending")
        self.user.balance = 100.0
        
        result, message = self.user.validate_deletion_prereq()
        
        self.assertFalse(result)
        self.assertIn("pending disputes", message)
        self.assertIn("Cannot close account due to", message)
    
    def test_validate_deletion_prereq_negative_balance(self):
        """Test validation when user has negative balance"""
        # Setup: Negative balance, no disputes
        self.user.disputes = []
        self.user.balance = -50.0
        
        result, message = self.user.validate_deletion_prereq()
        
        self.assertFalse(result)
        self.assertIn("negative balance", message)
    
    def test_validate_deletion_prereq_both_issues(self):
        """Test validation when user has both pending disputes and negative balance"""
        # Setup: Both issues present
        self.user.add_dispute(1, "Dispute about transaction", "pending")
        self.user.add_dispute(2, "Another dispute", "pending")
        self.user.balance = -150.0
        
        result, message = self.user.validate_deletion_prereq()
        
        self.assertFalse(result)
        self.assertIn("pending disputes", message)
        self.assertIn("negative balance", message)
        # Both should be mentioned
        self.assertIn(", ", message)  # Both issues listed
    
    def test_validate_deletion_prereq_resolved_disputes(self):
        """Test validation when disputes are resolved (not pending)"""
        # Setup: Only resolved disputes
        self.user.add_dispute(1, "Resolved dispute", "resolved")
        self.user.add_dispute(2, "Closed dispute", "closed")
        self.user.balance = 100.0
        
        result, message = self.user.validate_deletion_prereq()
        
        self.assertTrue(result)
        self.assertEqual(message, "All prerequisites met. Account can be closed.")
    
    def test_validate_deletion_prereq_zero_balance(self):
        """Test validation when balance is exactly zero"""
        # Setup: Zero balance, no disputes
        self.user.disputes = []
        self.user.balance = 0.0
        
        result, message = self.user.validate_deletion_prereq()
        
        self.assertTrue(result)
        self.assertEqual(message, "All prerequisites met. Account can be closed.")
    
    def test_validate_deletion_prereq_small_positive_balance(self):
        """Test validation with small positive balance"""
        # Setup: Small positive balance
        self.user.disputes = []
        self.user.balance = 0.01
        
        result, message = self.user.validate_deletion_prereq()
        
        self.assertTrue(result)
    
    def test_has_pending_disputes_method(self):
        """Test the helper method that checks for pending disputes"""
        # Initially no disputes
        self.assertFalse(self.user.has_pending_disputes())
        
        # Add a non-pending dispute
        self.user.add_dispute(1, "Resolved", "resolved")
        self.assertFalse(self.user.has_pending_disputes())
        
        # Add a pending dispute
        self.user.add_dispute(2, "Pending", "pending")
        self.assertTrue(self.user.has_pending_disputes())
        
        # Mix of pending and resolved
        self.user.add_dispute(3, "Closed", "closed")
        self.assertTrue(self.user.has_pending_disputes())
    
    def test_dispute_lifecycle_affects_validation(self):
        """Test how dispute status changes affect validation"""
        # Start with pending dispute
        self.user.add_dispute(1, "Initial dispute", "pending")
        self.user.balance = 100.0
        
        result, message = self.user.validate_deletion_prereq()
        self.assertFalse(result)
        
        # Resolve the dispute
        self.user.update_dispute_status(1, "resolved")
        
        result, message = self.user.validate_deletion_prereq()
        self.assertTrue(result)
        
        # Reopen dispute
        self.user.update_dispute_status(1, "pending")
        
        result, message = self.user.validate_deletion_prereq()
        self.assertFalse(result)

class TestAccountDeletion(unittest.TestCase):
    
    def setUp(self):
        """Set up test user and database mocks"""
        self.user = User(
            email="test@example.com",
            passwordHash="hashed_password",
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now(),
            userID=123
        )
        
        # Mock database connection and cursor
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_connection.cursor.return_value = self.mock_cursor
    
    def test_successful_account_deletion(self):
        """Test successful account closure when all prerequisites are met"""
        # Setup: No blocking issues
        self.user.disputes = []
        self.user.balance = 100.0
        
        # Mock successful database update
        self.mock_cursor.execute.return_value = None
        self.mock_connection.commit.return_value = None
        
        result, message = self.user.delete(self.mock_connection, self.mock_cursor)
        
        # Verify result
        self.assertTrue(result)
        self.assertEqual(message, "Account successfully closed.")
        
        # Verify database was called correctly
        self.mock_cursor.execute.assert_called_once_with(
            "UPDATE bankUser SET is_Verified = 0 WHERE idbankUser = %s",
            (123,)
        )
        self.mock_connection.commit.assert_called_once()
        
        # Verify user state was updated
        self.assertFalse(self.user.isActive)
    
    def test_account_deletion_fails_due_to_pending_disputes(self):
        """Test account closure blocked by pending disputes"""
        # Setup: Pending disputes exist
        self.user.add_dispute(1, "Pending dispute", "pending")
        self.user.balance = 100.0
        
        result, message = self.user.delete(self.mock_connection, self.mock_cursor)
        
        # Verify failure
        self.assertFalse(result)
        self.assertIn("Cannot close account due to", message)
        self.assertIn("pending disputes", message)
        
        # Verify database was NOT called
        self.mock_cursor.execute.assert_not_called()
        self.mock_connection.commit.assert_not_called()
        
        # Verify user is still active
        self.assertTrue(self.user.isActive)
    
    def test_account_deletion_fails_due_to_negative_balance(self):
        """Test account closure blocked by negative balance"""
        # Setup: Negative balance
        self.user.disputes = []
        self.user.balance = -50.0
        
        result, message = self.user.delete(self.mock_connection, self.mock_cursor)
        
        # Verify failure
        self.assertFalse(result)
        self.assertIn("Cannot close account due to", message)
        self.assertIn("negative balance", message)
        
        # Verify database was NOT called
        self.mock_cursor.execute.assert_not_called()
        self.mock_connection.commit.assert_not_called()
        
        # Verify user is still active
        self.assertTrue(self.user.isActive)
    
    def test_account_deletion_database_error(self):
        """Test account closure when database operation fails"""
        # Setup: No blocking issues
        self.user.disputes = []
        self.user.balance = 100.0
        
        # Mock database error
        self.mock_cursor.execute.side_effect = Exception("Database connection failed")
        
        result, message = self.user.delete(self.mock_connection, self.mock_cursor)
        
        # Verify failure
        self.assertFalse(result)
        self.assertIn("Error deleting account", message)
        
        # Verify rollback was called
        self.mock_connection.rollback.assert_called_once()
        
        # Verify user is still active (since transaction failed)
        self.assertTrue(self.user.isActive)
    
    def test_account_deletion_with_multiple_pending_disputes(self):
        """Test account closure with multiple pending disputes"""
        # Setup: Multiple disputes
        self.user.add_dispute(1, "Dispute 1", "pending")
        self.user.add_dispute(2, "Dispute 2", "pending")
        self.user.add_dispute(3, "Dispute 3", "pending")
        self.user.balance = 500.0
        
        result, message = self.user.delete(self.mock_connection, self.mock_cursor)
        
        self.assertFalse(result)
        self.assertIn("pending disputes", message)
    
    def test_account_deletion_after_dispute_resolution(self):
        """Test account closure after resolving disputes"""
        # Start with pending dispute
        self.user.add_dispute(1, "Chargeback dispute", "pending")
        self.user.balance = 100.0
        
        # First attempt should fail
        result, message = self.user.delete(self.mock_connection, self.mock_cursor)
        self.assertFalse(result)
        
        # Resolve dispute
        self.user.update_dispute_status(1, "resolved")
        
        # Reset mock
        self.mock_cursor.reset_mock()
        self.mock_connection.reset_mock()
        
        # Second attempt should succeed
        result, message = self.user.delete(self.mock_connection, self.mock_cursor)
        self.assertTrue(result)
        self.assertEqual(message, "Account successfully closed.")

class TestAccountClosureEdgeCases(unittest.TestCase):
    
    def setUp(self):
        self.user = User(
            email="test@example.com",
            passwordHash="hashed_password",
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now(),
            userID=123
        )
        
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_connection.cursor.return_value = self.mock_cursor
    
    def test_deletion_with_no_user_id(self):
        """Test account deletion when user has no ID (edge case)"""
        user = User(
            email="test@example.com",
            passwordHash="hashed_password",
            fname="John",
            lname="Doe",
            phoneNumber="1234567890",
            dateCreated=datetime.now(),
            userID=None  # No user ID
        )
        user.disputes = []
        user.balance = 100.0
        
        # This should fail because userID is None in SQL query
        result, message = user.delete(self.mock_connection, self.mock_cursor)
        
        # The actual behavior depends on implementation, but typically would fail
        # Let's see what happens: SQL would fail with None userID
        self.assertFalse(result)
        self.assertIn("Error", message)
    
    def test_deletion_with_empty_disputes_list(self):
        """Test with empty disputes list (should be valid)"""
        self.user.disputes = []  # Explicitly empty list
        self.user.balance = 100.0
        
        result, message = self.user.validate_deletion_prereq()
        self.assertTrue(result)
    
    def test_deletion_with_none_disputes_attribute(self):
        """Test when disputes attribute is None (should handle gracefully)"""
        # Simulate disputes attribute being None (edge case)
        self.user.disputes = None
        self.user.balance = 100.0
        
        # This might cause AttributeError in has_pending_disputes
        # We need to handle this in our test
        try:
            result, message = self.user.validate_deletion_prereq()
            # If it doesn't crash, check the result
            # The method should handle None gracefully
        except AttributeError:
            self.fail("validate_deletion_prereq should handle None disputes attribute")
    
    def test_deletion_with_large_negative_balance(self):
        """Test with very large negative balance"""
        self.user.disputes = []
        self.user.balance = -1000000.0  # Large negative
        
        result, message = self.user.validate_deletion_prereq()
        
        self.assertFalse(result)
        self.assertIn("negative balance", message)
    
    def test_deletion_with_very_small_negative_balance(self):
        """Test with very small negative balance (still should fail)"""
        self.user.disputes = []
        self.user.balance = -0.01  # Small negative
        
        result, message = self.user.validate_deletion_prereq()
        
        self.assertFalse(result)
        self.assertIn("negative balance", message)
    
    def test_dispute_status_case_sensitivity(self):
        """Test dispute status checking with different case variations"""
        # Add disputes with different case statuses
        self.user.disputes = [
            {'id': 1, 'description': 'Dispute 1', 'status': 'PENDING'},  # Uppercase
            {'id': 2, 'description': 'Dispute 2', 'status': 'Pending'},  # Capitalized
            {'id': 3, 'description': 'Dispute 3', 'status': 'pending'},  # Lowercase
        ]
        
        # Current implementation uses exact match with 'pending'
        # So only the lowercase one should be detected
        self.assertTrue(self.user.has_pending_disputes())
        
        # But let's verify our implementation handles this correctly
        # The code uses: dispute.get('status') == 'pending'
        # So it's case-sensitive
        pending_count = sum(1 for d in self.user.disputes if d.get('status') == 'pending')
        self.assertEqual(pending_count, 1)  # Only one exact match
    
    def test_balance_precision_issues(self):
        """Test with floating point precision edge cases"""
        self.user.disputes = []
        
        # Test with very small positive value
        self.user.balance = 0.0000001
        result, message = self.user.validate_deletion_prereq()
        self.assertTrue(result)
        
        # Test with very small negative value
        self.user.balance = -0.0000001
        result, message = self.user.validate_deletion_prereq()
        self.assertFalse(result)
    
    def test_concurrent_dispute_updates(self):
        """Test scenario where disputes are being added while checking prerequisites"""
        self.user.disputes = []
        self.user.balance = 100.0
        
        # Initial check passes
        result1, _ = self.user.validate_deletion_prereq()
        self.assertTrue(result1)
        
        # Add dispute while user is trying to delete
        self.user.add_dispute(1, "New dispute", "pending")
        
        # Now check should fail
        result2, message2 = self.user.validate_deletion_prereq()
        self.assertFalse(result2)
        
        # Simulate delete attempt
        result3, message3 = self.user.delete(self.mock_connection, self.mock_cursor)
        self.assertFalse(result3)

class TestAcceptanceCriteria(unittest.TestCase):
    """Direct tests for the acceptance criteria"""
    
    def test_ac_given_i_request_closure_then_i_see_prerequisites(self):
        """AC: Given I request closure, then I see prerequisites no pending disputes or negative balance"""
        # Create test scenarios that directly map to acceptance criteria
        
        # Scenario 1: User with no issues
        user1 = User(
            email="good@user.com",
            passwordHash="hash",
            fname="Good",
            lname="User",
            phoneNumber="1112223333",
            dateCreated=datetime.now(),
            userID=1001
        )
        user1.disputes = []
        user1.balance = 0.0
        
        result1, message1 = user1.validate_deletion_prereq()
        self.assertTrue(result1)
        self.assertEqual(message1, "All prerequisites met. Account can be closed.")
        
        # Scenario 2: User with pending dispute
        user2 = User(
            email="dispute@user.com",
            passwordHash="hash",
            fname="Dispute",
            lname="User",
            phoneNumber="4445556666",
            dateCreated=datetime.now(),
            userID=1002
        )
        user2.add_dispute(401, "Transaction issue", "pending")
        user2.balance = 100.0
        
        result2, message2 = user2.validate_deletion_prereq()
        self.assertFalse(result2)
        self.assertIn("pending disputes", message2)
        self.assertIn("Cannot close account due to", message2)
        
        # Scenario 3: User with negative balance
        user3 = User(
            email="negative@user.com",
            passwordHash="hash",
            fname="Negative",
            lname="Balance",
            phoneNumber="7778889999",
            dateCreated=datetime.now(),
            userID=1003
        )
        user3.disputes = []
        user3.balance = -25.0
        
        result3, message3 = user3.validate_deletion_prereq()
        self.assertFalse(result3)
        self.assertIn("negative balance", message3)
        self.assertIn("Cannot close account due to", message3)
        
        # Scenario 4: User with both issues
        user4 = User(
            email="both@user.com",
            passwordHash="hash",
            fname="Both",
            lname="Issues",
            phoneNumber="0001112222",
            dateCreated=datetime.now(),
            userID=1004
        )
        user4.add_dispute(402, "Chargeback", "pending")
        user4.add_dispute(403, "Fraud claim", "pending")
        user4.balance = -150.0
        
        result4, message4 = user4.validate_deletion_prereq()
        self.assertFalse(result4)
        self.assertIn("pending disputes", message4)
        self.assertIn("negative balance", message4)
        # Both should be mentioned in the error message
        self.assertIn(", ", message4)  # Indicates list of issues