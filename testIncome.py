import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, timedelta
from Money import PayFrequency, Income

class TestPayFrequencyEnum(unittest.TestCase):
    """Test the PayFrequency enumeration"""
    
    def test_pay_frequency_values(self):
        """Test that PayFrequency enum has correct values"""
        self.assertEqual(PayFrequency.DAILY.value, "daily")
        self.assertEqual(PayFrequency.WEEKLY.value, "1 week")
        self.assertEqual(PayFrequency.BI_WEEKLY.value, "bi-weekly")
        self.assertEqual(PayFrequency.MONTHLY.value, "1 month")
        self.assertEqual(PayFrequency.CUSTOM.value, "custom")
    
    def test_bi_weekly_variations(self):
        """Test that bi-weekly has multiple accepted values in Income class"""
        # Note: Income.calc_next_payday accepts multiple bi-weekly variations
        test_values = ["bi-weekly", "biweekly", "2 weeks"]
        
        for value in test_values:
            income = Income(
                incomeID=1,
                userID="user123",
                name="Test Income",
                amount=1000.00,
                payFrequency=value,
                datePaid=date(2024, 1, 1)
            )
            
            # Should not raise ValueError
            self.assertEqual(income.payFrequency, value)
    
    def test_pay_frequency_from_string(self):
        """Test creating PayFrequency from string values"""
        self.assertEqual(PayFrequency("bi-weekly"), PayFrequency.BI_WEEKLY)
        self.assertEqual(PayFrequency("daily"), PayFrequency.DAILY)
        self.assertEqual(PayFrequency("1 week"), PayFrequency.WEEKLY)
        self.assertEqual(PayFrequency("1 month"), PayFrequency.MONTHLY)
        self.assertEqual(PayFrequency("custom"), PayFrequency.CUSTOM)

class TestBiWeeklyIncomeCalculations(unittest.TestCase):
    """Test bi-weekly income calculations"""
    
    def setUp(self):
        """Set up test income with bi-weekly frequency"""
        self.income = Income(
            incomeID=1,
            userID="user123",
            name="Bi-Weekly Salary",
            amount=2000.00,
            payFrequency="bi-weekly",
            datePaid=date(2024, 1, 1)  # Monday, Jan 1, 2024
        )
    
    def test_calc_next_payday_bi_weekly_basic(self):
        """Test basic bi-weekly next payday calculation"""
        # From Jan 1, next bi-weekly should be Jan 15
        next_payday = self.income.calc_next_payday(date(2024, 1, 1))
        
        self.assertEqual(next_payday, date(2024, 1, 15))
    
    def test_calc_next_payday_bi_weekly_with_start_date(self):
        """Test bi-weekly calculation with different start dates"""
        # Test from a date after last payment
        next_payday = self.income.calc_next_payday(date(2024, 1, 10))
        
        # Should still be Jan 15 (first future payday after Jan 10)
        self.assertEqual(next_payday, date(2024, 1, 15))
    
    def test_calc_next_payday_bi_weekly_on_payday(self):
        """Test calculation when today is payday"""
        # If today is Jan 15 (payday), next should be Jan 29
        next_payday = self.income.calc_next_payday(date(2024, 1, 15))
        
        self.assertEqual(next_payday, date(2024, 1, 29))
    
    def test_calc_next_payday_bi_weekly_after_payday(self):
        """Test calculation when date is after payday"""
        # If today is Jan 20 (after Jan 15 payday), next should be Jan 29
        next_payday = self.income.calc_next_payday(date(2024, 1, 20))
        
        self.assertEqual(next_payday, date(2024, 1, 29))
    
    def test_calc_next_payday_bi_weekly_across_months(self):
        """Test bi-weekly calculation across month boundaries"""
        # Set last payment to Jan 29
        self.income.datePaid = date(2024, 1, 29)
        
        # Next should be Feb 12
        next_payday = self.income.calc_next_payday(date(2024, 2, 1))
        
        self.assertEqual(next_payday, date(2024, 2, 12))
    
    def test_calc_next_payday_bi_weekly_across_years(self):
        """Test bi-weekly calculation across year boundaries"""
        # Set last payment to Dec 18, 2024
        self.income.datePaid = date(2024, 12, 18)
        
        # Next should be Jan 1, 2025
        next_payday = self.income.calc_next_payday(date(2024, 12, 25))
        
        self.assertEqual(next_payday, date(2025, 1, 1))
    
    def test_calc_next_payday_bi_weekly_leap_year(self):
        """Test bi-weekly calculation with leap year"""
        # Set last payment to Feb 14, 2024 (leap year)
        self.income.datePaid = date(2024, 2, 14)
        
        # Next should be Feb 28
        next_payday = self.income.calc_next_payday(date(2024, 2, 20))
        
        self.assertEqual(next_payday, date(2024, 2, 28))
    
    def test_calc_next_payday_bi_weekly_inactive(self):
        """Test calculation when income is inactive"""
        self.income.isActive = False
        
        with self.assertRaises(ValueError):
            self.income.calc_next_payday()
    
    def test_calc_next_payday_bi_weekly_no_date_paid(self):
        """Test calculation when datePaid is None"""
        self.income.datePaid = None
        
        # Should use current date as last paid
        next_payday = self.income.calc_next_payday(date(2024, 1, 1))
        
        # With no datePaid, it uses startDate (which defaults to current date)
        # So from Jan 1, next would be Jan 15
        self.assertEqual(next_payday, date(2024, 1, 15))
    
    def test_bi_weekly_variations(self):
        """Test that all bi-weekly variations work correctly"""
        variations = ["bi-weekly", "biweekly", "2 weeks"]
        
        for variation in variations:
            with self.subTest(payFrequency=variation):
                income = Income(
                    incomeID=2,
                    userID="user123",
                    name=f"Test {variation}",
                    amount=1000.00,
                    payFrequency=variation,
                    datePaid=date(2024, 1, 1)
                )
                
                next_payday = income.calc_next_payday(date(2024, 1, 1))
                self.assertEqual(next_payday, date(2024, 1, 15))
    
    def test_calc_next_payday_edge_case_month_end(self):
        """Test bi-weekly calculation at month end"""
        # Last payment on Jan 31
        self.income.datePaid = date(2024, 1, 31)
        
        # Next should be Feb 14
        next_payday = self.income.calc_next_payday(date(2024, 2, 1))
        
        self.assertEqual(next_payday, date(2024, 2, 14))

class TestUpcomingPaydays(unittest.TestCase):
    """Test getting upcoming paydays for bi-weekly income"""
    
    def setUp(self):
        self.income = Income(
            incomeID=1,
            userID="user123",
            name="Bi-Weekly Salary",
            amount=2000.00,
            payFrequency="bi-weekly",
            datePaid=date(2024, 1, 1)
        )
    
    def test_get_upcoming_paydays_basic(self):
        """Test getting basic upcoming paydays"""
        # From Jan 1, get next 3 paydays
        paydays = self.income.get_upcoming_paydays(count=3, startDate=date(2024, 1, 1))
        
        expected = [
            date(2024, 1, 15),
            date(2024, 1, 29),
            date(2024, 2, 12)
        ]
        
        self.assertEqual(paydays, expected)
    
    def test_get_upcoming_paydays_with_start_date(self):
        """Test getting paydays from a specific start date"""
        # From Jan 10, get next 3 paydays
        paydays = self.income.get_upcoming_paydays(count=3, startDate=date(2024, 1, 10))
        
        expected = [
            date(2024, 1, 15),  # First after Jan 10
            date(2024, 1, 29),
            date(2024, 2, 12)
        ]
        
        self.assertEqual(paydays, expected)
    
    def test_get_upcoming_paydays_inactive_income(self):
        """Test getting paydays for inactive income"""
        self.income.isActive = False
        
        paydays = self.income.get_upcoming_paydays(count=3)
        
        self.assertEqual(paydays, [])
    
    def test_get_upcoming_paydays_one_time_income(self):
        """Test getting paydays for one-time income"""
        one_time_income = Income(
            incomeID=2,
            userID="user123",
            name="Bonus",
            amount=5000.00,
            payFrequency="one time",
            datePaid=date(2024, 1, 1)
        )
        
        paydays = one_time_income.get_upcoming_paydays(count=3)
        
        self.assertEqual(paydays, [])
    
    def test_get_upcoming_paydays_custom_frequency(self):
        """Test getting paydays for custom frequency"""
        custom_income = Income(
            incomeID=3,
            userID="user123",
            name="Custom",
            amount=1000.00,
            payFrequency="custom",
            datePaid=date(2024, 1, 1),
            customDays=10  # Every 10 days
        )
        
        paydays = custom_income.get_upcoming_paydays(count=3, startDate=date(2024, 1, 1))
        
        expected = [
            date(2024, 1, 11),  # Jan 1 + 10 days
            date(2024, 1, 21),  # +10 more
            date(2024, 1, 31)   # +10 more
        ]
        
        self.assertEqual(paydays, expected)
    
    def test_get_upcoming_paydays_large_count(self):
        """Test getting many upcoming paydays"""
        paydays = self.income.get_upcoming_paydays(count=10, startDate=date(2024, 1, 1))
        
        self.assertEqual(len(paydays), 10)
        
        # Verify they're bi-weekly (14 days apart)
        for i in range(1, len(paydays)):
            days_between = (paydays[i] - paydays[i-1]).days
            self.assertEqual(days_between, 14)
    
    def test_should_pay_today_true(self):
        """Test should_pay_today returns True when today is payday"""
        # Mock date.today() to return Jan 15
        with patch('Money.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 15)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            
            should_pay = self.income.should_pay_today()
            
            self.assertTrue(should_pay)
    
    def test_should_pay_today_false(self):
        """Test should_pay_today returns False when today is not payday"""
        with patch('Money.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 10)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            
            should_pay = self.income.should_pay_today()
            
            self.assertFalse(should_pay)
    
    def test_should_pay_today_inactive(self):
        """Test should_pay_today for inactive income"""
        self.income.isActive = False
        
        should_pay = self.income.should_pay_today()
        
        self.assertFalse(should_pay)

class TestBudgetIntegration(unittest.TestCase):
    """Test how bi-weekly income integrates with budgets"""
    
    @patch('Money.mysql.connector.connect')
    def test_monthly_budget_with_bi_weekly_income(self, mock_connect):
        """Test calculating monthly budget from bi-weekly income"""
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.commit.return_value = None
        mock_connect.return_value = mock_connection
        
        # Create bi-weekly income
        income = Income(
            incomeID=1,
            userID="user123",
            name="Bi-Weekly Salary",
            amount=2000.00,
            payFrequency="bi-weekly",
            datePaid=date(2024, 1, 1)
        )
        
        # Calculate expected monthly income
        # Some months have 2 pay periods, some have 3
        # Jan 2024: Jan 1, Jan 15, Jan 29 = 3 pay periods
        # Feb 2024: Feb 12, Feb 26 = 2 pay periods
        
        jan_paydays = income.get_upcoming_paydays(
            count=10, 
            startDate=date(2023, 12, 31)  # Start before Jan to catch Jan 1
        )
        jan_paydays = [d for d in jan_paydays if d.month == 1 and d.year == 2024]
        
        feb_paydays = income.get_upcoming_paydays(
            count=10,
            startDate=date(2024, 1, 31)  # Start before Feb
        )
        feb_paydays = [d for d in feb_paydays if d.month == 2 and d.year == 2024]
        
        jan_income = len(jan_paydays) * 2000.00
        feb_income = len(feb_paydays) * 2000.00
        
        self.assertEqual(jan_income, 6000.00)  # 3 pay periods
        self.assertEqual(feb_income, 4000.00)  # 2 pay periods
        
        # Apply income to January budget
        with patch('Money.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 15)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            
            # Mock the apply_income_to_budgets method
            success = income.apply_income_to_budgets(mock_connection)
            
            self.assertTrue(success)
            
            # Verify budget was updated for January
            mock_cursor.execute.assert_called_once()
            call_args = mock_cursor.execute.call_args[0]
            values = call_args[1]
            
            # Should update budget for January 2024
            self.assertEqual(values[2], date(2024, 1, 1))  # month (first of January)
    
    def test_bi_weekly_to_monthly_conversion(self):
        """Test helper method to convert bi-weekly to monthly income"""
        # This is a suggested helper method not in current code
        
        def bi_weekly_to_monthly(bi_weekly_amount: float, year: int, month: int) -> float:
            """Convert bi-weekly amount to estimated monthly income"""
            # Create a temporary income to calculate paydays
            temp_income = Income(
                incomeID=0,
                userID="temp",
                name="Temp",
                amount=bi_weekly_amount,
                payFrequency="bi-weekly",
                datePaid=date(year, month, 1)
            )
            
            # Get paydays in the month
            start_date = date(year, month, 1)
            end_date = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
            end_date = end_date - timedelta(days=1)  # Last day of month
            
            # Get enough paydays to cover the period
            paydays = temp_income.get_upcoming_paydays(count=10, startDate=start_date)
            
            # Count paydays in the target month
            monthly_paydays = [d for d in paydays if d.year == year and d.month == month]
            
            return len(monthly_paydays) * bi_weekly_amount
        
        # Test conversion
        jan_income = bi_weekly_to_monthly(2000.00, 2024, 1)
        feb_income = bi_weekly_to_monthly(2000.00, 2024, 2)
        
        self.assertEqual(jan_income, 6000.00)  # 3 pay periods in Jan 2024
        self.assertEqual(feb_income, 4000.00)  # 2 pay periods in Feb 2024

class TestBiWeeklyEdgeCases(unittest.TestCase):
    """Test edge cases for bi-weekly income"""
    
    def test_bi_weekly_with_29th_february(self):
        """Test bi-weekly schedule that lands on Feb 29 (leap year)"""
        income = Income(
            incomeID=1,
            userID="user123",
            name="Bi-Weekly Leap Year Test",
            amount=1000.00,
            payFrequency="bi-weekly",
            datePaid=date(2024, 2, 15)  # Leap year
        )
        
        # Next payday from Feb 15 should be Feb 29
        next_payday = income.calc_next_payday(date(2024, 2, 20))
        self.assertEqual(next_payday, date(2024, 2, 29))
        
        # After Feb 29, next should be Mar 14
        next_after_leap = income.calc_next_payday(date(2024, 3, 1))
        self.assertEqual(next_after_leap, date(2024, 3, 14))
    
    def test_bi_weekly_with_invalid_frequency(self):
        """Test with invalid pay frequency"""
        income = Income(
            incomeID=1,
            userID="user123",
            name="Test",
            amount=1000.00,
            payFrequency="invalid",  # Invalid frequency
            datePaid=date(2024, 1, 1)
        )
        
        # Should raise ValueError when calculating next payday
        with self.assertRaises(ValueError):
            income.calc_next_payday()
    
    def test_bi_weekly_with_zero_amount(self):
        """Test bi-weekly income with zero amount (edge case)"""
        income = Income(
            incomeID=1,
            userID="user123",
            name="Zero Income",
            amount=0.00,
            payFrequency="bi-weekly",
            datePaid=date(2024, 1, 1)
        )
        
        # Should still calculate paydays correctly
        next_payday = income.calc_next_payday(date(2024, 1, 1))
        self.assertEqual(next_payday, date(2024, 1, 15))
        
        # Upcoming paydays should work
        paydays = income.get_upcoming_paydays(count=3)
        self.assertEqual(len(paydays), 3)
    
    def test_bi_weekly_with_very_large_amount(self):
        """Test bi-weekly income with very large amount"""
        income = Income(
            incomeID=1,
            userID="user123",
            name="Large Income",
            amount=9999999.99,
            payFrequency="bi-weekly",
            datePaid=date(2024, 1, 1)
        )
        
        # Calculations should still work
        next_payday = income.calc_next_payday(date(2024, 1, 1))
        self.assertEqual(next_payday, date(2024, 1, 15))
    
    def test_bi_weekly_date_overflow(self):
        """Test bi-weekly calculation with date overflow (month with 31 days)"""
        income = Income(
            incomeID=1,
            userID="user123",
            name="Test",
            amount=1000.00,
            payFrequency="bi-weekly",
            datePaid=date(2024, 1, 31)
        )
        
        # Jan 31 + 14 days = Feb 14
        next_payday = income.calc_next_payday(date(2024, 1, 31))
        self.assertEqual(next_payday, date(2024, 2, 14))
        
        # Test from March 17 (should handle April correctly)
        income.datePaid = date(2024, 3, 17)
        next_payday = income.calc_next_payday(date(2024, 3, 17))
        self.assertEqual(next_payday, date(2024, 3, 31))
    
    def test_concurrent_income_updates(self):
        """Test scenario with multiple rapid income updates"""
        income = Income(
            incomeID=1,
            userID="user123",
            name="Test",
            amount=1000.00,
            payFrequency="bi-weekly",
            datePaid=date(2024, 1, 1)
        )
        
        # Simulate rapid updates
        for i in range(5):
            income.amount = 1000.00 + (i * 100)
            # Recalculate shouldn't crash
            next_payday = income.calc_next_payday(date(2024, 1, 1))
            self.assertEqual(next_payday, date(2024, 1, 15))

class TestAcceptanceCriteria(unittest.TestCase):
    """Direct tests for acceptance criteria"""
    
    def test_ac_create_recurring_income_bi_weekly(self):
        """AC: Create recurring income with bi-weekly frequency"""
        # Create bi-weekly income
        income = Income(
            incomeID=1,
            userID="user123",
            name="Bi-Weekly Salary",
            amount=2000.00,
            payFrequency="bi-weekly",
            datePaid=date(2024, 1, 1),
            isActive=True
        )
        
        self.assertEqual(income.payFrequency, "bi-weekly")
        self.assertTrue(income.isActive)
        self.assertEqual(income.amount, 2000.00)
        
        # Verify it's recurring (not one-time)
        self.assertNotEqual(income.payFrequency.lower(), "one time")
        self.assertNotEqual(income.payFrequency.lower(), "one-time")
    
    def test_ac_payment_auto_populate_missing(self):
        """AC: Payment should automatically appear on pay dates - NOT IMPLEMENTED"""
        print("\n" + "="*60)
        print("AC GAP: Auto-population of payments not implemented")
        print("="*60)
        print("Current implementation only calculates pay dates.")
        print("No automatic transaction creation occurs.")
        print("="*60)
        
        self.skipTest("Auto-population feature not implemented")
    
    def test_ac_edit_income_schedule(self):
        """AC: Should be able to edit the schedule"""
        income = Income(
            incomeID=1,
            userID="user123",
            name="Original Income",
            amount=1500.00,
            payFrequency="bi-weekly",
            datePaid=date(2024, 1, 1)
        )
        
        # Test editing various properties
        original_amount = income.amount
        original_frequency = income.payFrequency
        original_date = income.datePaid
        
        # Edit amount
        income.amount = 1800.00
        self.assertNotEqual(income.amount, original_amount)
        self.assertEqual(income.amount, 1800.00)
        
        # Edit frequency (still bi-weekly, different variation)
        income.payFrequency = "biweekly"
        self.assertNotEqual(income.payFrequency, original_frequency)
        self.assertEqual(income.payFrequency, "biweekly")
        
        # Edit date
        income.datePaid = date(2024, 1, 15)
        self.assertNotEqual(income.datePaid, original_date)
        self.assertEqual(income.datePaid, date(2024, 1, 15))
        
        # Recalculate should work with new values
        next_payday = income.calc_next_payday(date(2024, 1, 15))
        self.assertEqual(next_payday, date(2024, 1, 29))
    
    def test_ac_cancel_income_schedule(self):
        """AC: Should be able to cancel the schedule"""
        income = Income(
            incomeID=1,
            userID="user123",
            name="Bi-Weekly Income",
            amount=2000.00,
            payFrequency="bi-weekly",
            datePaid=date(2024, 1, 1),
            isActive=True
        )
        
        # Initially active
        self.assertTrue(income.isActive)
        
        # Cancel (deactivate) the income
        income.isActive = False
        
        # Should not calculate paydays when inactive
        with self.assertRaises(ValueError):
            income.calc_next_payday()
        
        # Should return empty upcoming paydays
        paydays = income.get_upcoming_paydays(count=5)
        self.assertEqual(paydays, [])
        
        # Reactivate
        income.isActive = True
        
        # Should work again
        next_payday = income.calc_next_payday(date(2024, 1, 1))
        self.assertEqual(next_payday, date(2024, 1, 15))