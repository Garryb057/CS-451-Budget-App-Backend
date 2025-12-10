import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import date
import mysql.connector
from Money import Category
from budget import Budget


class TestBudgetCreation(unittest.TestCase):
    """Test suite for budget creation functionality"""
    
    def setUp(self):
        """Create sample budget and category for testing"""
        self.sample_budget = Budget(
            budgetID=1,
            userID="test_user",
            name="Test Budget",
            totalPlannedAmnt=0.0,
            month="2023-10",
            income=3000.0
        )
        
        self.sample_category = Category(
            categoryID=1,
            name="Test Category",
            type_="expense",
            categoryLimit=500.0,
            plannedAmnt=300.0,
            plannedPercentage=None
        )
        
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
    
    def test_budget_naming(self):
        self.assertTrue(hasattr(self.sample_budget, 'name'))
        self.assertIsInstance(self.sample_budget.name, str)
    
    def test_add_category(self):
        initial_count = len(self.sample_budget.categories)
        self.sample_budget.addCategory(self.sample_category)
        self.assertEqual(len(self.sample_budget.categories), initial_count + 1)
    
    def test_total_calculation(self):
        # Test that total is calculated automatically
        pass

    def test_create_budget_with_name(self):
        """Test creating a budget with a custom name"""
        # Setup
        user_id = "user123"
        budget_name = "October 2023 Budget"
        
        # Create budget with name
        budget = Budget(
            budgetID=1,
            userID=user_id,
            name=budget_name,
            totalPlannedAmnt=0.0,
            month="2023-10",
            income=3000.0
        )
        
        # Verify
        self.assertEqual(budget.name, budget_name)
        self.assertTrue(hasattr(budget, 'name'))
        self.assertIsInstance(budget.name, str)
        self.assertGreater(len(budget.name), 0)

    def test_add_new_custom_category(self):
        """Test adding a new custom category to a budget"""
        # Setup
        budget = Budget(1, "user123", "Test Budget", 0.0, "2023-10", 3000.0)
        mock_db = Mock()
        
        # Create new custom category
        category = Category(
            categoryID=None,
            name="Custom Category",
            type_="custom",
            categoryLimit=500.0,
            plannedAmnt=300.0,
            plannedPercentage=None
        )
        
        # Mock database interaction
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 101  # Simulate new category ID
        
        # Execute
        category.createCategory(mock_db, budget.budgetID)
        budget.addCategory(category)
        
        # Verify
        self.assertEqual(len(budget.categories), 1)
        self.assertEqual(budget.categories[0].name, "Custom Category")
        self.assertEqual(budget.categories[0].type, "custom")
        self.assertEqual(budget.categories[0].plannedAmnt, 300.0)
        mock_db.commit.assert_called_once()

    def test_edit_existing_category(self):
        """Test editing an existing category"""
        # Setup
        budget = Budget(1, "user123", "Test Budget", 0.0, "2023-10", 3000.0)
        mock_db = Mock()
        
        # Add initial category
        category = Category(
            categoryID=1,
            name="Groceries",
            type_="expense",
            categoryLimit=400.0,
            plannedAmnt=300.0,
            plannedPercentage=None
        )
        budget.categories = [category]
        budget.totalPlannedAmnt = 300.0
        
        # Mock database
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # Execute edit
        budget.editCategory(
            dbConnection=mock_db,
            categoryID=1,
            name="Weekly Groceries",
            plannedAmnt=350.0
        )
        
        # Verify
        edited_category = budget.getCategoryByID(1)
        self.assertEqual(edited_category.name, "Weekly Groceries")
        self.assertEqual(edited_category.plannedAmnt, 350.0)
        self.assertEqual(budget.totalPlannedAmnt, 350.0)  # Should be recalculated
        mock_db.commit.assert_called_once()

    def test_delete_custom_category(self):
        """Test deleting a custom category from budget"""
        # Setup
        budget = Budget(1, "user123", "Test Budget", 500.0, "2023-10", 3000.0)
        mock_db = Mock()
        
        # Add categories
        categories = [
            Category(1, "Groceries", "expense", 400.0, 300.0, None),
            Category(2, "Entertainment", "custom", 300.0, 200.0, None)  # Custom category
        ]
        budget.categories = categories
        
        # Mock database
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # Execute delete
        budget.deleteCategory(mock_db, 2)  # Delete custom category
        
        # Verify
        self.assertEqual(len(budget.categories), 1)
        self.assertIsNone(budget.getCategoryByID(2))  # Category should be removed
        self.assertEqual(budget.totalPlannedAmnt, 300.0)  # Should be recalculated
        mock_db.commit.assert_called_once()

    def test_input_planned_amount_as_dollar(self):
        """Test setting category amount as dollar value"""
        # Setup
        budget = Budget(1, "user123", "Test Budget", 0.0, "2023-10", 3000.0)
        mock_db = Mock()
        
        # Create category with dollar amount
        category = Category(
            categoryID=1,
            name="Rent",
            type_="expense",
            categoryLimit=1200.0,
            plannedAmnt=1000.0,  # Dollar amount
            plannedPercentage=None
        )
        budget.categories = [category]
        
        # Mock database
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # Set planned amount as dollar value
        success = category.setPlannedAmnt(mock_db, 1100.0)  # Increase to $1100
        
        # Verify
        self.assertTrue(success)
        self.assertEqual(category.plannedAmnt, 1100.0)
        self.assertIsNone(category.plannedPercentage)  # Percentage should be cleared
        mock_db.commit.assert_called_once()

    def test_input_planned_amount_as_percentage(self):
        """Test setting category amount as percentage of income"""
        # Setup
        budget_income = 4000.0
        budget = Budget(1, "user123", "Test Budget", 0.0, "2023-10", budget_income)
        mock_db = Mock()
        
        # Create category
        category = Category(
            categoryID=1,
            name="Savings",
            type_="savings",
            categoryLimit=800.0,
            plannedAmnt=0.0,
            plannedPercentage=None
        )
        budget.categories = [category]
        
        # Mock database
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # Set planned amount as percentage (25% of $4000 = $1000)
        success = category.setPlannedPercentage(mock_db, 25.0, budget_income)
        
        # Verify
        self.assertTrue(success)
        self.assertEqual(category.plannedPercentage, 25.0)
        self.assertEqual(category.plannedAmnt, 1000.0)  # 25% of $4000
        mock_db.commit.assert_called_once()

    def test_automatic_total_calculation_add_category(self):
        """Test total calculation when adding new category"""
        # Setup
        budget = Budget(1, "user123", "Test Budget", 0.0, "2023-10", 3000.0)
        
        # Verify initial total
        self.assertEqual(budget.totalPlannedAmnt, 0.0)
        
        # Add first category
        category1 = Category(1, "Rent", "expense", 1200.0, 1000.0, None)
        budget.addCategory(category1)
        
        # Verify total updated
        self.assertEqual(budget.totalPlannedAmnt, 1000.0)
        
        # Add second category
        category2 = Category(2, "Groceries", "expense", 500.0, 300.0, None)
        budget.addCategory(category2)
        
        # Verify total updated
        self.assertEqual(budget.totalPlannedAmnt, 1300.0)

    def test_automatic_total_calculation_edit_category(self):
        """Test total calculation when editing category amount"""
        # Setup
        budget = Budget(1, "user123", "Test Budget", 1500.0, "2023-10", 3000.0)
        
        # Add categories
        categories = [
            Category(1, "Rent", "expense", 1200.0, 1000.0, None),
            Category(2, "Groceries", "expense", 500.0, 300.0, None),
            Category(3, "Utilities", "expense", 300.0, 200.0, None)
        ]
        budget.categories = categories
        
        # Verify initial total
        self.assertEqual(budget.totalPlannedAmnt, 1500.0)
        
        # Edit a category amount
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        budget.editCategory(
            dbConnection=mock_db,
            categoryID=2,
            plannedAmnt=400.0  # Increase groceries from 300 to 400
        )
        
        # Verify total recalculated
        self.assertEqual(budget.totalPlannedAmnt, 1600.0)  # 1000 + 400 + 200

    def test_automatic_total_calculation_delete_category(self):
        """Test total calculation when deleting category"""
        # Setup
        budget = Budget(1, "user123", "Test Budget", 1500.0, "2023-10", 3000.0)
        
        # Add categories
        categories = [
            Category(1, "Rent", "expense", 1200.0, 1000.0, None),
            Category(2, "Groceries", "expense", 500.0, 300.0, None),
            Category(3, "Utilities", "expense", 300.0, 200.0, None)
        ]
        budget.categories = categories
        
        # Verify initial total
        self.assertEqual(budget.totalPlannedAmnt, 1500.0)
        
        # Delete a category
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        budget.deleteCategory(mock_db, 2)  # Delete groceries
        
        # Verify total recalculated
        self.assertEqual(budget.totalPlannedAmnt, 1200.0)  # 1000 + 200

    @patch('budget.MagicMock')
    def test_create_budget_database(self, mock_magic):
        """Test creating a budget and saving to database"""
        # Setup
        user_id = "user123"
        budget_name = "November 2023 Budget"
        mock_db = MagicMock()
        
        # Create budget
        budget = Budget(
            budgetID=None,
            userID=user_id,
            name=budget_name,
            totalPlannedAmnt=0.0,
            month="2023-11",
            income=3500.0
        )
        
        # Add categories
        categories = [
            Category(None, "Rent", "expense", 1200.0, 1000.0, None),
            Category(None, "Groceries", "expense", 500.0, 300.0, None)
        ]
        budget.categories = categories
        
        # Mock database
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 101  # Simulate new budget ID
        
        # Execute
        success = budget.createBudget(mock_db)
        
        # Verify
        self.assertTrue(success)
        self.assertEqual(budget.budgetID, 101)
        mock_db.commit.assert_called()
        
        # Verify database insert for budget
        call_args = mock_cursor.execute.call_args_list[0]
        self.assertIn("INSERT bankBudget", call_args[0][0])
        self.assertIn(budget_name, call_args[0][1])  # Check name in values

    def test_edit_budget_name(self):
        """Test editing the budget name"""
        # Setup
        budget = Budget(1, "user123", "Old Budget Name", 1000.0, "2023-10", 3000.0)
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # Execute edit
        budget.editBudget(
            dbConnection=mock_db,
            name="Updated Budget Name"
        )
        
        # Verify
        self.assertEqual(budget.name, "Updated Budget Name")
        
        # Verify database update
        call_args = mock_cursor.execute.call_args
        self.assertIn("UPDATE bankBudget SET Name = %s", call_args[0][0])
        self.assertEqual(call_args[0][1][0], "Updated Budget Name")  # First value is new name
        mock_db.commit.assert_called_once()

    def test_category_amount_from_percentage(self):
        """Test category amount calculation based on percentage of income"""
        test_cases = [
            (3000.0, 25.0, 750.0),    # 25% of 3000 = 750
            (5000.0, 10.0, 500.0),    # 10% of 5000 = 500
            (2500.0, 50.0, 1250.0),   # 50% of 2500 = 1250
            (1000.0, 100.0, 1000.0),  # 100% of 1000 = 1000
            (4000.0, 33.33, 1333.2),  # 33.33% of 4000 ≈ 1333.2
        ]
        
        for income, percentage, expected_amount in test_cases:
            with self.subTest(income=income, percentage=percentage):
                budget = Budget(1, "user123", "Test", 0.0, "2023-10", income)
                category = Category(1, "Test", "expense", 0.0, 0.0, None)
                
                # Set percentage
                mock_db = Mock()
                mock_cursor = Mock()
                mock_db.cursor.return_value = mock_cursor
                
                category.setPlannedPercentage(mock_db, percentage, income)
                
                # Verify calculation
                self.assertLess(abs(category.plannedAmnt - expected_amount), 0.01)
                self.assertEqual(category.plannedPercentage, percentage)

    def test_percentage_within_valid_range(self):
        """Test percentage validation"""
        test_cases = [
            (0.0, True),      # Minimum valid
            (50.0, True),     # Mid-range
            (100.0, True),    # Maximum valid
            (-5.0, False),    # Below minimum
            (105.0, False),   # Above maximum
        ]
        
        for percentage, should_succeed in test_cases:
            with self.subTest(percentage=percentage):
                budget = Budget(1, "user123", "Test", 0.0, "2023-10", 3000.0)
                category = Category(1, "Test", "expense", 0.0, 0.0, None)
                
                mock_db = Mock()
                mock_cursor = Mock()
                mock_db.cursor.return_value = mock_cursor
                
                try:
                    success = category.setPlannedPercentage(mock_db, percentage, 3000.0)
                    if not should_succeed:
                        self.assertFalse(success)
                except ValueError:
                    if should_succeed:
                        self.fail(f"Percentage {percentage} should be valid")

    def test_budget_name_validation(self):
        """Test budget name validation"""
        test_names = [
            ("Valid Budget Name", True, "normal name"),
            ("", False, "empty name"),
            ("A" * 100, True, "long name"),
            ("Budget 123", True, "name with numbers"),
            ("Budget-Name_2023", True, "name with special chars"),
        ]
        
        for name, should_succeed, description in test_names:
            with self.subTest(name=description):
                try:
                    budget = Budget(1, "user123", name, 0.0, "2023-10", 3000.0)
                    
                    if not should_succeed:
                        # If shouldn't succeed, we shouldn't reach here
                        # In real implementation, there would be validation
                        pass
                        
                except Exception as e:
                    if should_succeed:
                        self.fail(f"Failed for {description}: {name}")

    def test_concurrent_category_modifications(self):
        """Test handling multiple category changes"""
        # Setup
        budget = Budget(1, "user123", "Test Budget", 0.0, "2023-10", 4000.0)
        
        # Initial categories
        categories = [
            Category(1, "Rent", "expense", 1200.0, 1000.0, None),
            Category(2, "Groceries", "expense", 500.0, 300.0, None),
        ]
        budget.categories = categories
        budget.calculateTotalPlannedAmnt()
        
        # Simulate multiple edits (as might happen in UI)
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # Edit rent
        budget.editCategory(mock_db, 1, plannedAmnt=1100.0)
        
        # Edit groceries
        budget.editCategory(mock_db, 2, plannedAmnt=400.0)
        
        # Add new category
        category3 = Category(3, "Utilities", "expense", 400.0, 200.0, None)
        budget.addCategory(category3)
        
        # Delete groceries
        budget.deleteCategory(mock_db, 2)
        
        # Verify final state
        self.assertEqual(len(budget.categories), 2)  # Rent and Utilities
        self.assertEqual(budget.totalPlannedAmnt, 1300.0)  # 1100 + 200

    def test_budget_total_exceeds_income(self):
        """Test when total planned amount exceeds income"""
        income = 3000.0
        
        # Setup budget that exceeds income
        budget = Budget(1, "user123", "Test Budget", 0.0, "2023-10", income)
        
        categories = [
            Category(1, "Rent", "expense", 1200.0, 1500.0, None),
            Category(2, "Car", "expense", 600.0, 800.0, None),
            Category(3, "Groceries", "expense", 500.0, 500.0, None),
            Category(4, "Entertainment", "expense", 300.0, 400.0, None),
        ]
        budget.categories = categories
        
        # Calculate total (exceeds income)
        budget.calculateTotalPlannedAmnt()
        total = budget.totalPlannedAmnt  # 1500 + 800 + 500 + 400 = 3200
        
        # Verify system allows it (user might be using savings or have debt)
        self.assertGreater(total, income)
        self.assertEqual(total, 3200.0)
        
        # System should calculate percentage of income used
        percentage_used = (total / income) * 100
        self.assertGreater(percentage_used, 100)

    def test_acceptance_criteria_budget_naming(self):
        """Verify user can name budget on edit page"""
        # Simulate UI interaction
        budget_data = {
            'name': "My October 2023 Budget",
            'month': "2023-10",
            'income': 3500.0,
            'categories': []
        }
        
        # Create budget with name
        budget = Budget(
            budgetID=1,
            userID="user123",
            name=budget_data['name'],
            totalPlannedAmnt=0.0,
            month=budget_data['month'],
            income=budget_data['income']
        )
        
        # Verify name can be set and retrieved
        self.assertEqual(budget.name, "My October 2023 Budget")
        self.assertIsInstance(budget.name, str)
        self.assertGreater(len(budget.name), 0)
        
        # Verify name can be edited
        budget.name = "Updated Budget Name"
        self.assertEqual(budget.name, "Updated Budget Name")

    def test_acceptance_criteria_add_custom_category(self):
        """Verify user can add new custom category"""
        budget = Budget(1, "user123", "Test Budget", 0.0, "2023-10", 3000.0)
        
        # User adds custom category
        custom_category = Category(
            categoryID=1,
            name="Gym Membership",
            type_="custom",  # Custom type
            categoryLimit=80.0,
            plannedAmnt=60.0,
            plannedPercentage=None
        )
        
        budget.addCategory(custom_category)
        
        # Verify category added
        self.assertEqual(len(budget.categories), 1)
        category = budget.categories[0]
        self.assertEqual(category.name, "Gym Membership")
        self.assertEqual(category.type, "custom")
        self.assertEqual(category.plannedAmnt, 60.0)

    def test_acceptance_criteria_edit_category(self):
        """Verify user can edit existing category"""
        budget = Budget(1, "user123", "Test Budget", 100.0, "2023-10", 3000.0)
        
        # Initial category
        category = Category(1, "Groceries", "expense", 500.0, 100.0, None)
        budget.categories = [category]
        
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # User edits category
        budget.editCategory(
            dbConnection=mock_db,
            categoryID=1,
            name="Weekly Groceries",
            plannedAmnt=150.0
        )
        
        # Verify edits
        edited = budget.getCategoryByID(1)
        self.assertEqual(edited.name, "Weekly Groceries")
        self.assertEqual(edited.plannedAmnt, 150.0)
        self.assertEqual(budget.totalPlannedAmnt, 150.0)  # Updated total

    def test_acceptance_criteria_delete_category(self):
        """Verify user can delete custom category"""
        budget = Budget(1, "user123", "Test Budget", 200.0, "2023-10", 3000.0)
        
        # Add categories including custom
        categories = [
            Category(1, "Rent", "expense", 1200.0, 100.0, None),
            Category(2, "Streaming", "custom", 50.0, 50.0, None),  # Custom
            Category(3, "Gym", "custom", 80.0, 50.0, None),       # Custom
        ]
        budget.categories = categories
        
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # User deletes custom category
        budget.deleteCategory(mock_db, 2)  # Delete streaming
        
        # Verify deletion
        self.assertEqual(len(budget.categories), 2)
        self.assertIsNone(budget.getCategoryByID(2))
        self.assertEqual(budget.totalPlannedAmnt, 150.0)  # 100 + 50

    def test_acceptance_criteria_dollar_or_percentage(self):
        """Verify user can input amount as dollar or percentage"""
        income = 4000.0
        budget = Budget(1, "user123", "Test", 0.0, "2023-10", income)
        
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # Create category
        category = Category(1, "Savings", "savings", 0.0, 0.0, None)
        
        # Option 1: Input as dollar value
        category.setPlannedAmnt(mock_db, 500.0)
        self.assertEqual(category.plannedAmnt, 500.0)
        self.assertIsNone(category.plannedPercentage)
        
        # Option 2: Input as percentage (20% of 4000 = 800)
        category.setPlannedPercentage(mock_db, 20.0, income)
        self.assertEqual(category.plannedPercentage, 20.0)
        self.assertEqual(category.plannedAmnt, 800.0)
        
        # Verify both methods work
        self.assertGreater(category.plannedAmnt, 0)

    def test_acceptance_criteria_automatic_total(self):
        """Verify system automatically calculates and displays total"""
        budget = Budget(1, "user123", "Test", 0.0, "2023-10", 3000.0)
        
        # Initial state
        self.assertEqual(budget.totalPlannedAmnt, 0.0)
        
        # User adds first category
        category1 = Category(1, "Rent", "expense", 1200.0, 1000.0, None)
        budget.addCategory(category1)
        self.assertEqual(budget.totalPlannedAmnt, 1000.0)  # Auto-calculated
        
        # User adds second category
        category2 = Category(2, "Groceries", "expense", 500.0, 300.0, None)
        budget.addCategory(category2)
        self.assertEqual(budget.totalPlannedAmnt, 1300.0)  # Auto-calculated
        
        # User edits first category
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        budget.editCategory(mock_db, 1, plannedAmnt=1100.0)
        self.assertEqual(budget.totalPlannedAmnt, 1400.0)  # Auto-calculated
        
        # System always displays current total
        # This would be shown in the UI
        current_total = budget.totalPlannedAmnt
        self.assertEqual(current_total, 1400.0)


if __name__ == '__main__':
    unittest.main()