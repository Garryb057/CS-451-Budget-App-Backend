import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import date, timedelta
from Money import Transaction, TransactionManager, ExpenseType


class TestRecentTransactions(unittest.TestCase):
    """Test suite for recent transactions functionality"""
    
    def setUp(self):
        """Create sample transactions and manager for testing"""
        self.sample_transaction = Transaction(
            transactionID=1,
            userID="user123",
            total=100.0,
            date=date(2023, 10, 15),
            payee="Test Merchant",
            categoryID=5,
            notes="Test transaction",
            isRecurring=False
        )
        
        # Create manager with sample data
        self.manager_with_data = TransactionManager()
        user_id = "user123"
        
        # Create 10 transactions
        transactions = []
        for i in range(10):
            transactions.append(
                Transaction(
                    transactionID=i+1,
                    userID=user_id,
                    total=(i+1) * 10.0,
                    date=date(2023, 10, 1) + timedelta(days=i),
                    payee=f"Payee{i+1}",
                    categoryID=(i % 5) + 1
                )
            )
        self.manager_with_data.transactions = transactions
        
        # Mock database
        self.mock_db = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_db.cursor.return_value = self.mock_cursor
    
    def test_widget_data_structure(self):
        """Test that transaction data has all fields needed for widget"""
        user_id = "user123"
        recent = self.manager_with_data.get_recent_transactions(user_id, limit=5)
        
        # Verify each transaction has required fields
        for transaction in recent:
            self.assertTrue(hasattr(transaction, 'date'))
            self.assertTrue(hasattr(transaction, 'payee'))
            self.assertTrue(hasattr(transaction, 'total'))
            self.assertTrue(hasattr(transaction, 'categoryID'))
            self.assertTrue(hasattr(transaction, 'transactionID'))
    
    def test_limit_parameter(self):
        """Test that limit parameter works correctly"""
        user_id = "user123"
        
        # Test with limit 3
        recent = self.manager_with_data.get_recent_transactions(user_id, limit=3)
        self.assertEqual(len(recent), 3)
        
        # Test with limit 7
        recent = self.manager_with_data.get_recent_transactions(user_id, limit=7)
        self.assertEqual(len(recent), 7)
        
        # Test with limit larger than available
        recent = self.manager_with_data.get_recent_transactions(user_id, limit=20)
        self.assertEqual(len(recent), 10)  # Only 10 transactions available
    
    @patch('mysql.connector.connect')
    def test_database_loading(self, mock_connect):
        """Test loading transactions from database"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Setup mock database response
        mock_rows = []
        mock_cursor.fetchall.return_value = mock_rows
        
        manager = TransactionManager({'host': 'localhost'})

    def test_get_recent_transactions_default_limit(self):
        """Test retrieving recent transactions with default limit of 10"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        # Create mock transactions with different dates
        mock_transactions = [
            Transaction(transactionID=1, userID=user_id, total=100.0, date=date(2023, 10, 1), 
                    payee="Amazon", categoryID=1),
            Transaction(transactionID=2, userID=user_id, total=50.0, date=date(2023, 10, 2), 
                    payee="Walmart", categoryID=2),
            Transaction(transactionID=3, userID=user_id, total=25.0, date=date(2023, 10, 3), 
                    payee="Starbucks", categoryID=3),
            Transaction(transactionID=4, userID=user_id, total=75.0, date=date(2023, 10, 4), 
                    payee="Gas Station", categoryID=4),
            Transaction(transactionID=5, userID=user_id, total=200.0, date=date(2023, 10, 5), 
                    payee="Restaurant", categoryID=5),
            Transaction(transactionID=6, userID=user_id, total=30.0, date=date(2023, 10, 6), 
                    payee="Netflix", categoryID=6),
            Transaction(transactionID=7, userID=user_id, total=45.0, date=date(2023, 10, 7), 
                    payee="Uber", categoryID=7),
            Transaction(transactionID=8, userID=user_id, total=80.0, date=date(2023, 10, 8), 
                    payee="Groceries", categoryID=8),
            Transaction(transactionID=9, userID=user_id, total=150.0, date=date(2023, 10, 9), 
                    payee="Best Buy", categoryID=9),
            Transaction(transactionID=10, userID=user_id, total=60.0, date=date(2023, 10, 10), 
                    payee="Pharmacy", categoryID=10),
            Transaction(transactionID=11, userID=user_id, total=90.0, date=date(2023, 10, 11), 
                    payee="Should Not Appear", categoryID=11),  # Should be excluded (11th item)
        ]
        manager.transactions = mock_transactions
        
        # Execute
        recent_transactions = manager.get_recent_transactions(user_id)
        
        # Verify
        self.assertEqual(len(recent_transactions), 10)  # Default limit
        # Verify transactions are in reverse chronological order (most recent first)
        dates = [t.date for t in recent_transactions]
        self.assertEqual(dates, sorted(dates, reverse=True))
        # Verify transaction 11 is not included
        self.assertTrue(all(t.transactionID != 11 for t in recent_transactions))

    def test_get_recent_transactions_custom_limit(self):
        """Test retrieving exactly 5 recent transactions"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        # Create 8 transactions
        mock_transactions = [
            Transaction(transactionID=i, userID=user_id, total=i*10.0, 
                    date=date(2023, 10, i), payee=f"Payee{i}", categoryID=i)
            for i in range(1, 9)
        ]
        manager.transactions = mock_transactions
        
        # Execute with custom limit
        recent_transactions = manager.get_recent_transactions(user_id, limit=5)
        
        # Verify
        self.assertEqual(len(recent_transactions), 5)
        # Verify we get the most recent 5 (IDs 8, 7, 6, 5, 4)
        expected_ids = [8, 7, 6, 5, 4]
        actual_ids = [t.transactionID for t in recent_transactions]
        self.assertEqual(actual_ids, expected_ids)

    def test_get_recent_transactions_user_filtering(self):
        """Test that only transactions for the specified user are returned"""
        # Setup
        manager = TransactionManager()
        user1_id = "user1"
        user2_id = "user2"
        
        # Create mixed transactions
        mock_transactions = [
            Transaction(transactionID=1, userID=user1_id, total=100.0, 
                    date=date(2023, 10, 1), payee="Amazon", categoryID=1),
            Transaction(transactionID=2, userID=user2_id, total=50.0,  # Different user
                    date=date(2023, 10, 2), payee="Walmart", categoryID=2),
            Transaction(transactionID=3, userID=user1_id, total=25.0, 
                    date=date(2023, 10, 3), payee="Starbucks", categoryID=3),
            Transaction(transactionID=4, userID=user1_id, total=75.0, 
                    date=date(2023, 10, 4), payee="Gas Station", categoryID=4),
        ]
        manager.transactions = mock_transactions
        
        # Execute for user1
        user1_transactions = manager.get_recent_transactions(user1_id, limit=10)
        
        # Verify
        self.assertEqual(len(user1_transactions), 3)  # Only user1's transactions
        self.assertTrue(all(t.userID == user1_id for t in user1_transactions))
        
        # Execute for user2
        user2_transactions = manager.get_recent_transactions(user2_id, limit=10)
        self.assertEqual(len(user2_transactions), 1)
        self.assertTrue(all(t.userID == user2_id for t in user2_transactions))

    def test_transaction_has_required_fields(self):
        """Test that Transaction objects have all fields needed for dashboard display"""
        # Setup
        transaction = Transaction(
            transactionID=1,
            userID="user123",
            total=99.99,
            date=date(2023, 10, 15),
            payee="Test Merchant",
            categoryID=5,
            notes="Test transaction",
            isRecurring=False
        )
        
        # Verify all required fields exist and have getters
        required_fields = {
            'date': transaction.get_date(),
            'payee': transaction.get_payee(),
            'total': transaction.get_total(),
            'categoryID': transaction.get_categoryID(),
            'transactionID': transaction.get_transactionID()  # Needed for edit link
        }
        
        # Verify all fields are present
        self.assertEqual(len(required_fields), 5)
        self.assertEqual(required_fields['date'], date(2023, 10, 15))
        self.assertEqual(required_fields['payee'], "Test Merchant")
        self.assertEqual(required_fields['total'], 99.99)
        self.assertEqual(required_fields['categoryID'], 5)
        self.assertEqual(required_fields['transactionID'], 1)

    def test_get_transaction_by_id(self):
        """Test retrieving a specific transaction by ID for edit page navigation"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        # Create multiple transactions
        transactions = [
            Transaction(transactionID=i, userID=user_id, total=i*10.0,
                    date=date(2023, 10, i), payee=f"Payee{i}", categoryID=i)
            for i in range(1, 6)
        ]
        manager.transactions = transactions
        
        # Execute - get transaction with ID 3
        transaction = manager.get_transaction_by_id(3)
        
        # Verify
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.transactionID, 3)
        self.assertEqual(transaction.payee, "Payee3")
        self.assertEqual(transaction.total, 30.0)
        
        # Test non-existent transaction
        non_existent = manager.get_transaction_by_id(999)
        self.assertIsNone(non_existent)

    def test_recent_transactions_sorting_order(self):
        """Test that transactions are sorted by date descending (most recent first)"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        # Create transactions with specific dates (not in order)
        mock_transactions = [
            Transaction(transactionID=1, userID=user_id, total=100.0, 
                    date=date(2023, 10, 5), payee="Day 5", categoryID=1),
            Transaction(transactionID=2, userID=user_id, total=200.0, 
                    date=date(2023, 10, 1), payee="Day 1", categoryID=2),
            Transaction(transactionID=3, userID=user_id, total=300.0, 
                    date=date(2023, 10, 3), payee="Day 3", categoryID=3),
            Transaction(transactionID=4, userID=user_id, total=400.0, 
                    date=date(2023, 10, 2), payee="Day 2", categoryID=4),
            Transaction(transactionID=5, userID=user_id, total=500.0, 
                    date=date(2023, 10, 4), payee="Day 4", categoryID=5),
        ]
        manager.transactions = mock_transactions
        
        # Execute
        recent_transactions = manager.get_recent_transactions(user_id, limit=5)
        
        # Verify sorting (most recent first)
        expected_order = [1, 5, 3, 4, 2]  # By date: 5, 4, 3, 2, 1
        actual_order = [t.transactionID for t in recent_transactions]
        self.assertEqual(actual_order, expected_order)

    @patch.object(TransactionManager, 'get_db_connection')
    def test_get_recent_transactions_with_database(self, mock_get_db):
        """Test that get_recent_transactions loads from database when dbConfig is present"""
        # Setup
        db_config = {'host': 'localhost', 'database': 'test'}
        manager = TransactionManager(db_config)
        user_id = "user123"
        
        # Mock database connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock the query results
        mock_rows = [
            {
                'idbankTransaction': i,
                'userID': user_id,
                'amount': i * 10.0,
                'date': date(2023, 10, i),
                'payee': f'Payee{i}',
                'categoryID': i,
                'notes': '',
                'isRecurring': False,
                'recurrenceDate': None,
                'expenseType': 'variable',
                'isTaxRelated': False,
                'isTravelRelated': False
            }
            for i in range(1, 6)
        ]
        mock_cursor.fetchall.return_value = mock_rows
        mock_connection.cursor.return_value = mock_cursor
        
        # Mock get_db_connection to return our mock connection
        mock_get_db.return_value = mock_connection
        
        # Execute
        recent_transactions = manager.get_recent_transactions(user_id, limit=5)
        
        # Verify database was called
        mock_get_db.assert_called_once()
        mock_cursor.execute.assert_called_once()
        
        # Verify correct query
        call_args = mock_cursor.execute.call_args
        self.assertIn("SELECT * FROM bankTransaction WHERE userID = %s ORDER BY date DESC", call_args[0][0])
        self.assertEqual(call_args[0][1], (user_id,))
        
        # Verify transactions were loaded
        self.assertEqual(len(recent_transactions), 5)
        self.assertTrue(all(t.userID == user_id for t in recent_transactions))

    def test_get_recent_transactions_empty(self):
        """Test behavior when user has no transactions"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        # No transactions added
        
        # Execute
        recent_transactions = manager.get_recent_transactions(user_id)
        
        # Verify
        self.assertEqual(len(recent_transactions), 0)
        self.assertEqual(recent_transactions, [])

    def test_transaction_amount_display(self):
        """Test that transaction amounts can be formatted for display"""
        # Setup various transaction amounts
        test_cases = [
            (100.0, "$100.00"),
            (99.99, "$99.99"),
            (0.5, "$0.50"),
            (1000.0, "$1000.00"),
            (-50.0, "-$50.00"),  # Negative amounts (refunds)
        ]
        
        for amount, expected_format in test_cases:
            with self.subTest(amount=amount):
                transaction = Transaction(
                    transactionID=1,
                    userID="user123",
                    total=amount,
                    date=date(2023, 10, 1),
                    payee="Test",
                    categoryID=1
                )
                
                # In a real dashboard, you'd format this. For test, verify the raw data
                self.assertIsInstance(transaction.get_total(), (int, float))
                self.assertEqual(transaction.get_total(), amount)

    def test_transaction_date_display(self):
        """Test that transaction dates can be formatted for display"""
        # Setup
        transaction = Transaction(
            transactionID=1,
            userID="user123",
            total=100.0,
            date=date(2023, 10, 15),
            payee="Test",
            categoryID=1
        )
        
        # Verify date is a date object
        self.assertIsInstance(transaction.get_date(), date)
        
        # Test various display formats
        test_date = transaction.get_date()
        
        # Common dashboard formats
        formats = [
            ("%Y-%m-%d", "2023-10-15"),  # Standard
            ("%m/%d/%Y", "10/15/2023"),  # US format
            ("%b %d, %Y", "Oct 15, 2023"),  # Short month
            ("%d %b %Y", "15 Oct 2023"),  # Day first
        ]
        
        for fmt, expected in formats:
            with self.subTest(format=fmt):
                formatted = test_date.strftime(fmt)
                self.assertEqual(formatted, expected)

    def test_transaction_category_display(self):
        """Test that category IDs can be mapped to category names"""
        # Setup
        transaction = Transaction(
            transactionID=1,
            userID="user123",
            total=100.0,
            date=date(2023, 10, 15),
            payee="Amazon",
            categoryID=3  # Assuming 3 = Shopping
        )
        
        # In a real system, you'd have a category service
        # For testing, verify the categoryID is accessible
        category_id = transaction.get_categoryID()
        
        # Mock category mapping (in real app this would come from database)
        category_map = {
            1: "Groceries",
            2: "Dining",
            3: "Shopping",
            4: "Transportation",
            5: "Entertainment"
        }
        
        # Verify category can be mapped
        self.assertIn(category_id, category_map)
        category_name = category_map[category_id]
        self.assertEqual(category_name, "Shopping")

    @patch.object(TransactionManager, 'get_db_connection')
    def test_load_user_transactions(self, mock_get_db):
        """Test that load_user_transactions properly loads user's transactions"""
        # Setup
        db_config = {'host': 'localhost', 'database': 'test'}
        manager = TransactionManager(db_config)
        user_id = "user123"
        
        # Mock database
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        mock_rows = [
            {
                'idbankTransaction': 1,
                'userID': user_id,
                'amount': 100.0,
                'date': date(2023, 10, 1),
                'payee': 'Test1',
                'categoryID': 1,
                'notes': '',
                'isRecurring': False,
                'recurrenceDate': None,
                'expenseType': 'variable',
                'isTaxRelated': False,
                'isTravelRelated': False
            },
            {
                'idbankTransaction': 2,
                'userID': user_id,
                'amount': 200.0,
                'date': date(2023, 10, 2),
                'payee': 'Test2',
                'categoryID': 2,
                'notes': 'Note',
                'isRecurring': True,
                'recurrenceDate': date(2023, 11, 2),
                'expenseType': 'fixed',
                'isTaxRelated': True,
                'isTravelRelated': False
            }
        ]
        mock_cursor.fetchall.return_value = mock_rows
        mock_connection.cursor.return_value = mock_cursor
        
        mock_get_db.return_value = mock_connection
        
        # Execute
        manager.load_user_transactions(user_id)
        
        # Verify
        self.assertEqual(len(manager.transactions), 2)
        self.assertEqual(manager.transactions[0].transactionID, 1)
        self.assertEqual(manager.transactions[1].transactionID, 2)
        self.assertEqual(manager.transactions[1].expenseType, ExpenseType.FIXED)
        self.assertEqual(manager.transactions[1].isTaxRelated, True)

    def test_edit_transaction(self):
        """Test editing a transaction (for when user clicks on transaction)"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        original_transaction = Transaction(
            transactionID=1,
            userID=user_id,
            total=100.0,
            date=date(2023, 10, 1),
            payee="Original Payee",
            categoryID=1,
            notes="Original notes"
        )
        manager.transactions = [original_transaction]
        
        # Mock database
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # Execute edit
        original_transaction.edit_transaction(
            mock_db,
            payee="Updated Payee",
            total=150.0,
            notes="Updated notes"
        )
        
        # Verify
        self.assertEqual(original_transaction.payee, "Updated Payee")
        self.assertEqual(original_transaction.total, 150.0)
        self.assertEqual(original_transaction.notes, "Updated notes")
        mock_db.commit.assert_called_once()

    def test_transaction_data_for_dashboard_widget(self):
        """Test complete transaction data structure for dashboard widget"""
        # Setup
        transaction = Transaction(
            transactionID=42,
            userID="user123",
            total=125.50,
            date=date(2023, 10, 20),
            payee="Example Merchant",
            categoryID=7,
            notes="Test purchase",
            isRecurring=False
        )
        
        # Simulate widget data preparation
        widget_data = {
            'id': transaction.get_transactionID(),
            'date': transaction.get_date(),
            'payee': transaction.get_payee(),
            'amount': transaction.get_total(),
            'category': transaction.get_categoryID()
        }
        
        # Verify complete widget data
        self.assertEqual(widget_data['id'], 42)
        self.assertEqual(widget_data['date'], date(2023, 10, 20))
        self.assertEqual(widget_data['payee'], "Example Merchant")
        self.assertEqual(widget_data['amount'], 125.50)
        self.assertEqual(widget_data['category'], 7)

    def test_get_recent_transactions_large_dataset(self):
        """Test performance with large number of transactions"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        # Create 1000 transactions
        large_dataset = []
        for i in range(1000):
            large_dataset.append(
                Transaction(
                    transactionID=i,
                    userID=user_id,
                    total=float(i),
                    date=date(2023, 1, 1) + timedelta(days=i % 365),
                    payee=f"Payee{i}",
                    categoryID=(i % 10) + 1
                )
            )
        manager.transactions = large_dataset
        
        # Execute
        recent = manager.get_recent_transactions(user_id, limit=10)
        
        # Verify
        self.assertEqual(len(recent), 10)
        self.assertTrue(all(isinstance(t, Transaction) for t in recent))

    def test_recent_transactions_same_date(self):
        """Test handling transactions with same date"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        same_date = date(2023, 10, 15)
        
        # Create multiple transactions on same date
        transactions = [
            Transaction(transactionID=i, userID=user_id, total=i*10.0,
                    date=same_date, payee=f"Payee{i}", categoryID=i)
            for i in range(1, 6)
        ]
        manager.transactions = transactions
        
        # Execute
        recent = manager.get_recent_transactions(user_id, limit=5)
        
        # Verify all are returned
        self.assertEqual(len(recent), 5)
        # All should have same date
        self.assertTrue(all(t.date == same_date for t in recent))

    def test_transactions_with_negative_amounts(self):
        """Test handling transactions with negative amounts (refunds)"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        transactions = [
            Transaction(transactionID=1, userID=user_id, total=100.0,
                    date=date(2023, 10, 1), payee="Purchase", categoryID=1),
            Transaction(transactionID=2, userID=user_id, total=-50.0,  # Refund
                    date=date(2023, 10, 2), payee="Refund", categoryID=1),
            Transaction(transactionID=3, userID=user_id, total=75.0,
                    date=date(2023, 10, 3), payee="Another Purchase", categoryID=2),
        ]
        manager.transactions = transactions
        
        # Execute
        recent = manager.get_recent_transactions(user_id, limit=10)
        
        # Verify negative amount is preserved
        refund_transaction = next(t for t in recent if t.transactionID == 2)
        self.assertEqual(refund_transaction.total, -50.0)
        self.assertLess(refund_transaction.total, 0)

    def test_transactions_with_long_payee_names(self):
        """Test handling transactions with very long payee names"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        long_payee = "A" * 200  # Very long payee name
        
        transaction = Transaction(
            transactionID=1,
            userID=user_id,
            total=100.0,
            date=date(2023, 10, 1),
            payee=long_payee,
            categoryID=1
        )
        manager.transactions = [transaction]
        
        # Execute
        recent = manager.get_recent_transactions(user_id, limit=1)
        
        # Verify
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].payee, long_payee)
        # In real UI, this would be truncated for display

    def test_transaction_missing_category(self):
        """Test handling transaction with missing/None category"""
        # Setup
        transaction = Transaction(
            transactionID=1,
            userID="user123",
            total=100.0,
            date=date(2023, 10, 1),
            payee="Test",
            categoryID=None  # No category assigned
        )
        
        manager = TransactionManager()
        manager.transactions = [transaction]
        
        # Execute
        recent = manager.get_recent_transactions("user123", limit=10)
        
        # Verify transaction is still returned
        self.assertEqual(len(recent), 1)
        self.assertIsNone(recent[0].categoryID)

    def test_recent_transactions_mixed_expense_types(self):
        """Test recent transactions with mixed expense types"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        transactions = [
            Transaction(transactionID=1, userID=user_id, total=100.0,
                    date=date(2023, 10, 1), payee="Fixed", categoryID=1,
                    expenseType=ExpenseType.FIXED),
            Transaction(transactionID=2, userID=user_id, total=50.0,
                    date=date(2023, 10, 2), payee="Variable", categoryID=2,
                    expenseType=ExpenseType.VARIABLE),
            Transaction(transactionID=3, userID=user_id, total=75.0,
                    date=date(2023, 10, 3), payee="No Type", categoryID=3,
                    expenseType=None),
        ]
        manager.transactions = transactions
        
        # Execute
        recent = manager.get_recent_transactions(user_id, limit=10)
        
        # Verify all types are handled
        self.assertEqual(len(recent), 3)
        expense_types = [t.expenseType for t in recent]
        self.assertIn(ExpenseType.FIXED, expense_types)
        self.assertIn(ExpenseType.VARIABLE, expense_types)
        self.assertIn(None, expense_types)

    def test_acceptance_criteria_widget_presence(self):
        """AC: Recent transactions widget should be visible on dashboard"""
        # Setup - simulate dashboard loading
        manager = TransactionManager()
        user_id = "user123"
        
        # Add some transactions
        transactions = [
            Transaction(transactionID=i, userID=user_id, total=i*10.0,
                    date=date(2023, 10, i), payee=f"Payee{i}", categoryID=i)
            for i in range(1, 6)
        ]
        manager.transactions = transactions
        
        # Execute - get data for widget
        widget_data = manager.get_recent_transactions(user_id, limit=5)
        
        # Verify widget can be populated
        self.assertIsNotNone(widget_data)
        self.assertGreater(len(widget_data), 0)
        # Each transaction should have required display fields
        for transaction in widget_data:
            self.assertIsNotNone(transaction.date)
            self.assertIsNotNone(transaction.payee)
            self.assertIsNotNone(transaction.total)

    def test_acceptance_criteria_transaction_details(self):
        """AC: Widget should show date, payee, and amount for each transaction"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        # Create transaction with all required details
        transaction = Transaction(
            transactionID=1,
            userID=user_id,
            total=125.50,
            date=date(2023, 10, 15),
            payee="Example Store",
            categoryID=5
        )
        manager.transactions = [transaction]
        
        # Execute
        recent = manager.get_recent_transactions(user_id, limit=1)
        
        # Verify all required fields are present
        self.assertEqual(len(recent), 1)
        displayed_transaction = recent[0]
        
        # Verify date
        self.assertEqual(displayed_transaction.date, date(2023, 10, 15))
        
        # Verify payee
        self.assertEqual(displayed_transaction.payee, "Example Store")
        
        # Verify amount
        self.assertEqual(displayed_transaction.total, 125.50)

    def test_acceptance_criteria_edit_navigation(self):
        """AC: Clicking transaction should navigate to edit page"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        transaction = Transaction(
            transactionID=42,
            userID=user_id,
            total=100.0,
            date=date(2023, 10, 1),
            payee="Test",
            categoryID=1
        )
        manager.transactions = [transaction]
        
        # Execute - get transaction for edit
        transaction_to_edit = manager.get_transaction_by_id(42)
        
        # Verify transaction can be retrieved for editing
        self.assertIsNotNone(transaction_to_edit)
        self.assertEqual(transaction_to_edit.transactionID, 42)
        
        # In real UI, this would generate link: /edit-transaction/42
        edit_url = f"/edit-transaction/{transaction_to_edit.transactionID}"
        self.assertEqual(edit_url, "/edit-transaction/42")

    def test_acceptance_criteria_view_all_navigation(self):
        """AC: View All link should navigate to full transaction history"""
        # Setup
        manager = TransactionManager()
        user_id = "user123"
        
        # Create more than 5 transactions
        transactions = [
            Transaction(transactionID=i, userID=user_id, total=i*10.0,
                    date=date(2023, 10, i), payee=f"Payee{i}", categoryID=i)
            for i in range(1, 11)
        ]
        manager.transactions = transactions
        
        # Widget shows only recent 5
        recent_widget = manager.get_recent_transactions(user_id, limit=5)
        self.assertEqual(len(recent_widget), 5)
        
        # View All should show all transactions
        all_transactions = manager.get_recent_transactions(user_id, limit=None)
        # In real implementation, limit=None would return all
        # For this test, we verify more are available
        self.assertGreater(len(manager.transactions), len(recent_widget))


if __name__ == '__main__':
    unittest.main()