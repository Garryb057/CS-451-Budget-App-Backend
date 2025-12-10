from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional, Tuple
import mysql.connector

class ExpenseType(Enum):
    FIXED = "fixed"
    VARIABLE = "variable"

class Transaction:
    def __init__ (self, transactionID: int, userID: str, total: float, date: date, 
                  payee: str, categoryID: int, notes: str = "", isRecurring: bool = False, 
                  dateRecurr: date = None, expenseType: ExpenseType = None, isTaxRelated: bool = False, isTravelRelated: bool = False):
        self.transactionID = transactionID
        self.userID = userID
        self.total = total
        self.date = date
        self.payee = payee
        self.categoryID = categoryID
        self.notes = notes
        self.isRecurring = isRecurring
        self.dateRecurr = dateRecurr
        self.expenseType = expenseType
        self.isTaxRelated = isTaxRelated
        self.isTravelRelated = isTravelRelated

    #getters
    def get_transactionID(self):
        return self.transactionID
    def get_userID(self):
        return self.userID
    def get_total(self):
        return self.total
    def get_date(self):
        return self.date
    def get_payee(self):
        return self.payee
    def get_categoryID(self):
        return self.categoryID
    def get_notes(self):
        return self.notes
    def get_isRecurring(self):
        return self.isRecurring
    def get_dateRecurr(self):
        return self.dateRecurr
    def get_expenseType(self):
        return self.expenseType
    
    #setters
    def set_transactionID(self, transactionID):
        self.transactionID = transactionID
    def set_userID(self, userID):
        self.userID = userID
    def set_total (self, total):
        self.total = total
    def set_date (self, date):
        self.date = date
    def set_payee (self, payee):
        self.payee = payee
    def set_categoryID (self, categoryID):
        self.categoryID = categoryID
    def set_notes (self, notes):
        self.notes = notes
    def set_isRecurring (self, isRecurring):
        self.isRecurring = isRecurring
    def set_dateRecurr (self, dateRecurr):
        self.dateRecurr = dateRecurr
    def set_expenseType(self, expenseType: ExpenseType):
        self.expenseType = expenseType

    def set_isTaxRelated(self, isTaxRelated: bool):
        self.isTaxRelated = isTaxRelated
    def set_isTravelRelated(self, isTravelRelated: bool):
        self.isTravelRelated = isTravelRelated
    def get_isTaxRelated(self):
        return self.isTaxRelated
    def get_isTravelRelated(self):
        return self.isTravelRelated

    
    def add_transaction(self, dbConnection) -> bool:
        try:
            cursor = dbConnection.cursor(dictionary=True)
            query = """INSERT INTO bankTransaction (userID, amount, amountPayed, date, payee,
            categoryID, isRecurring, recurrenceDate, notes, expenseType, isTaxRelated,
            isTravelRelated) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (
                self.userID, self.total, self.total, self.date, self.payee, self.categoryID,
                self.isRecurring,
                self.dateRecurr if self.dateRecurr else self.date,
                self.notes, 
                self.expenseType.value if self.expenseType else ExpenseType.VARIABLE.value,
                self.isTaxRelated, self.isTravelRelated
            )
            cursor.execute(query, values)
            dbConnection.commit()

            self.transactionID = cursor.lastrowid
            cursor.close()
            return True
        except Exception as e:
            print(f"Error adding transaction: {e}")
            dbConnection.rollback()
            return False
    def delete_transaction(self, dbConnection) -> bool:
        try:
            cursor = dbConnection.cursor()
            query = "DELETE FROM bankTransaction WHERE idbankTransaction = %s"
            cursor.execute(query, (self.transactionID,))
            dbConnection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error deleting transaction: {e}")
            return False
    def edit_transaction(self, dbConnection, total: float = None, date: date = None, payee: str = None,
                         categoryID: int = None, notes: str = None, expenseType: ExpenseType = None):
        try:
            cursor = dbConnection.cursor()
            query = """UPDATE bankTransaction
            SET amount = %s, date = %s, payee = %s, categoryID = %s, notes = %s,
            expenseType = %s WHERE idbankTransaction = %s"""

            values = (
                total if total else self.total,
                date if date else self.date,
                payee if payee else self.payee,
                categoryID if categoryID else self.categoryID,
                notes if notes else self.notes,
                expenseType.value if expenseType else (self.expenseType.valie if self.expenseType else None),
                self.transactionID
            )
            cursor.execute(query, values)
            dbConnection.commit()
            cursor.close()

            if total: self.total = total
            if date: self.date = date
            if payee: self.payee = payee
            if categoryID: self.categoryID = categoryID
            if notes: self.notes = notes
            if expenseType: self.expenseType = expenseType
        except Exception as e:
            print(f"Error updating transaction: {e}")
    def flag_expense_type(self, dbConnection, expenseType: ExpenseType):
        try:
            cursor = dbConnection.cursor()
            query = "UDPATE bankTransaction SET expenseType = %s WHERE idbankTransaction = %s"
            cursor.execute(query(expenseType.value, self.transactionID))
            dbConnection.commmit()
            cursor.close()
            self.expenseType = expenseType
            print(f"Transaction {self.transactionID} tagged as {expenseType.value} expense")
        except Exception as e:
            print(f"Error flagging expense type: {e}")

    def flag_as_tax_related(self, dbConnection):
        try:
            cursor = dbConnection.cursor()
            query = "UPDATE bankTransaction SET isTaxRelated = %s WHERE idbankTransaction = %s"
            cursor.execute(query, (True, self.transactionID))
            dbConnection.commit()
            cursor.close()
            self.isTaxRelated = True
            print(f"Transaction {self.transactionID} flagged as tax-related")
        except Exception as e:
            print(f"Error flagging tax-related: {e}")

    def unflag_tax_related(self, dbConnection):
        try:
            cursor = dbConnection.cursor()
            query = "UDPATE bankTransaction SET isTaxRelated = %s WHERE idbankTransaction = %s"
            cursor.execute(query, (False, self.transactionID))
            dbConnection.commit()
            cursor.close()
            self.isTaxRelated = False
            print(f"Transaction {self.transactionID} unflagged from tax-related")
        except Exception as e:
            print(f"Error unflagging tax-related: {e}")
    
    def flag_as_travel(self, dbConnection):
        try:
            cursor = dbConnection.cursor()
            query = "UPDATE bankTransaction SET isTravelRelated = %s WHERE idbankTransaction = %s"
            cursor.execute(query, (True, self.transactionID))
            dbConnection.commit()
            cursor.close()
            self.isTravelRelated = True
            print(f"Transaction {self.transactionID} flagged as travel-related")
        except Exception as e:
            print(f"Error flagging travel-related: {e}")

    def unflag_travel(self, dbConnection):
        try:
            cursor = dbConnection.cursor()
            query = "UPDATE bankTransaction SET isTravelRelated = %s WHERE idbankTransaction = %s"
            cursor.execute(query, (False, self.transactionID))
            dbConnection.commit()
            cursor.close()
            self.isTravelRelated = False
            print(f"Transaction {self.transactionID} unflagged from travel. Reverted to category {self.categoryID}")
        except Exception as e:
            print(f"Error unflagging travel-related: {e}")

class TransactionManager:
    def __init__(self, dbConfig=None):
        self.dbConfig = dbConfig
        self.transactions: List[Transaction] = []
    def get_db_connection(self):
        if self.dbConfig:
            return mysql.connector.connect(**self.dbConfig)
        return None
    def add_transaction(self, transaction: Transaction):
        if self.dbConfig:
            dbConnection = self.get_db_connection()
            if dbConnection:
                success = transaction.add_transaction(dbConnection)
                dbConnection.close()
                if success:
                    self.transactions.append(transaction)
                return
        self.transactions.append(transaction)
    def load_user_transactions(self, userID: str):
        if not self.dbConfig:
            return
        try:
            dbConnection = self.get_db_connection()
            cursor = dbConnection.cursor(dictionary=True)
            query = """SELECT * FROM bankTransaction WHERE userID = %s ORDER BY date DESC"""
            cursor.execute(query, (userID,))
            rows = cursor.fetchall()

            self.transactions.clear()
            for row in rows:
                transaction = Transaction(
                    transactionID=row['idbankTransaction'],
                    userID=row['userID'],
                    total=float(row['amount']),
                    date=row['date'],
                    payee=row['payee'],
                    categoryID=row['categoryID'],
                    notes=row.get('notes', ''),
                    isRecurring=bool(row['isRecurring']),
                    dateRecurr=row['recurrenceDate'],
                    expenseType=ExpenseType(row['expenseType']) if row['expenseType'] else None,
                    isTaxRelated=bool(row.get('isTaxRelated', False)),
                    isTravelRelated=bool(row.get('isTravelRelated', False))
                )
                self.transactions.append(transaction)
            
            cursor.close()
            dbConnection.close()
        except Exception as e:
            print(f"Error loading transactions: {e}")
    def get_transactions_by_expense_type(self, expenseType: ExpenseType) -> List[Transaction]:
        return [t for t in self.transactions if t.expenseType == expenseType]
    def get_recent_transactions(self, userID: str, limit: int = 10) -> List[Transaction]:
        if self.dbConfig:
            self.load_user_transactions(userID)
        
        userTransactions = [t for t in self.transactions if t.userID == userID]

        userTransactions.sort(key=lambda t: t.date, reverse=True)
        return userTransactions[:limit]
    def get_transaction_by_id(self, transactionID: int) -> Optional[Transaction]:
        for transaction in self.transactions:
            if transaction.transactionID == transactionID:
                return transaction
        return None
    def get_expense_type_summary(self) -> dict:
        fixedTotal = sum(t.total for t in self.transactions if t.expenseType == ExpenseType.FIXED)
        variableTotal = sum(t.total for t in self.transactions if t.expenseType == ExpenseType.VARIABLE)
        untaggedTotal = sum(t.total for t in self.transactions if t.expenseType is None)

        return{
            ExpenseType.FIXED: fixedTotal,
            ExpenseType.VARIABLE: variableTotal,
            "untagged": untaggedTotal,
            "total_expenses": fixedTotal + variableTotal + untaggedTotal
        }
    def get_expense_type_breakdown(self, expenseType: ExpenseType = None) -> List[dict]:
        transactions = self.transactions
        if expenseType:
            transactions = self.get_transactions_by_expense_type(expenseType)
        
        breakdown = []
        for transaction in transactions:
            breakdown.append({
                'transactionID': transaction.transactionID,
                'date': transaction.date,
                'payee': transaction.payee,
                'total': transaction.total,
                'expenseType': transaction.expenseType.value if transaction.expenseType else 'untagged',
                'categoryID': transaction.categoryID,
                'notes': transaction.notes,
                'isRecurring': transaction.isRecurring
            })
        return breakdown
    def calculate_future_expenses(self, months: int = 3) -> dict:
        currentDate = date.today()
        futureExpenses = {}

        fixedExpenses = self.get_transactions_by_expense_type(ExpenseType.FIXED)
        monthlyFixed = sum(t.total for t in fixedExpenses if t.isRecurring)

        variableExpenses = self.get_transactions_by_expense_type(ExpenseType.VARIABLE)
        if variableExpenses:
            monthlyTotals = {}
            for transaction in variableExpenses:
                monthKey = (transaction.date.year, transaction.date.month)
                monthlyTotals[monthKey] = monthlyTotals.get(monthKey, 0) + transaction.total

            avgVariable = sum(monthlyTotals.values()) / len(monthlyTotals) if monthlyTotals else 0
        else:
            avgVariable = 0
        
        for i in range(months):
            nextMonth = currentDate.replace(month=currentDate.month + i)
            if nextMonth.month > 12:
                nextMonth = nextMonth.replace(year=nextMonth.year + 1, month=nextMonth.month - 12)
            futureExpenses[nextMonth.strftime("%Y-%m")] = {
                'fixed': monthlyFixed,
                'variable': avgVariable,
                'total': monthlyFixed + avgVariable
            }
        return futureExpenses
    def get_expense_type_stats(self) -> dict:
        summary = self.get_expense_type_summary()
        totalExpenses = summary['total_expenses']

        if totalExpenses > 0:
            fixedPercentage = (summary[ExpenseType.FIXED] / totalExpenses) * 100
            variablePercentage = (summary[ExpenseType.VARIABLE] / totalExpenses) * 100
        else:
            fixedPercentage = variablePercentage = 0
        
        return {
            'fixed_amount': summary[ExpenseType.FIXED],
            'variable_amount': summary[ExpenseType.VARIABLE],
            'fixed_percentage': round(fixedPercentage, 2),
            'variable_percentage': round(variablePercentage, 2),
            'total_expenses': totalExpenses,
            'fixed_count': len(self.get_transactions_by_expense_type(ExpenseType.FIXED)),
            'variable_count': len(self.get_transactions_by_expense_type(ExpenseType.VARIABLE))
        }
    
    #====Part of sprint 4 by Temka====
    def get_transactions_by_date_range(self, start_date: date, end_date: date) -> List[Transaction]:
        return [t for t in self.transactions 
                if start_date <= t.date <= end_date]

    def get_spending_by_category_period(self, start_date: date, end_date: date) -> dict:
        transactions = self.get_transactions_by_date_range(start_date, end_date)
        category_spending = {}
        
        for transaction in transactions:
            cat_id = transaction.categoryID
            if cat_id not in category_spending:
                category_spending[cat_id] = 0.0
            category_spending[cat_id] += transaction.total
        
        return category_spending

    def get_monthly_spending_chart_data(self, year: int, month: int) -> dict:
        from calendar import monthrange
        
        start_date = date(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        
        spending = self.get_spending_by_category_period(start_date, end_date)
        
        return {
            'period': f"{year}-{month:02d}",
            'spending': spending,
            'start_date': start_date,
            'end_date': end_date
        }

    def get_yearly_spending_chart_data(self, year: int) -> dict:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        spending = self.get_spending_by_category_period(start_date, end_date)
        
        monthly_breakdown = {}
        for month in range(1, 13):
            month_data = self.get_monthly_spending_chart_data(year, month)
            monthly_breakdown[f"{year}-{month:02d}"] = month_data['spending']
        
        return {
            'period': str(year),
            'total_spending': spending,
            'monthly_breakdown': monthly_breakdown,
            'start_date': start_date,
            'end_date': end_date
        }

    def get_category_transactions(self, categoryID: int, start_date: date = None, 
                                end_date: date = None) -> List[Transaction]:
        transactions = [t for t in self.transactions if t.categoryID == categoryID]
        
        if start_date and end_date:
            transactions = [t for t in transactions 
                        if start_date <= t.date <= end_date]
        
        return transactions

    def get_category_detail_view(self, categoryID: int, start_date: date = None, 
                                end_date: date = None) -> dict:
        transactions = self.get_category_transactions(categoryID, start_date, end_date)
        
        total_spent = sum(t.total for t in transactions)
        
        return {
            'categoryID': categoryID,
            'total_spent': total_spent,
            'transaction_count': len(transactions),
            'transactions': [
                {
                    'transactionID': t.transactionID,
                    'date': t.date,
                    'payee': t.payee,
                    'amount': t.total,
                    'notes': t.notes,
                    'expenseType': t.expenseType.value if t.expenseType else 'untagged'
                } for t in transactions
            ]
        }
    #=====End of part of sprint 4 by Temka====

    #Sprint 5 part Temka Tax
    def get_tax_related_transactions(self, start_date: date = None, end_date: date = None) -> List[Transaction]:
        tax_transactions = [t for t in self.transactions if t.isTaxRelated]
        
        if start_date and end_date:
            tax_transactions = [t for t in tax_transactions 
                            if start_date <= t.date <= end_date]
        
        return tax_transactions

    def get_tax_summary(self, year: int = None) -> dict:
        if year is None:
            year = date.today().year
        
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        tax_transactions = self.get_tax_related_transactions(start_date, end_date)
        
        category_totals = {}
        total_tax_expenses = 0.0
        
        for transaction in tax_transactions:
            cat_id = transaction.categoryID
            if cat_id not in category_totals:
                category_totals[cat_id] = {
                    'total': 0.0,
                    'count': 0,
                    'transactions': []
                }
            
            category_totals[cat_id]['total'] += transaction.total
            category_totals[cat_id]['count'] += 1
            category_totals[cat_id]['transactions'].append({
                'transactionID': transaction.transactionID,
                'date': transaction.date,
                'payee': transaction.payee,
                'amount': transaction.total,
                'notes': transaction.notes
            })
            
            total_tax_expenses += transaction.total
        
        return {
            'year': year,
            'total_tax_expenses': total_tax_expenses,
            'transaction_count': len(tax_transactions),
            'category_breakdown': category_totals,
            'period': {
                'start': start_date,
                'end': end_date
            }
        }

    def export_tax_report(self, year: int = None) -> dict:
        summary = self.get_tax_summary(year)
        
        return {
            'report_type': 'Tax Expenses',
            'tax_year': summary['year'],
            'generated_date': date.today(),
            'summary': summary,
            'all_transactions': [
                {
                    'date': t.date.strftime('%Y-%m-%d'),
                    'payee': t.payee,
                    'amount': f"${t.total:.2f}",
                    'category': t.categoryID,
                    'notes': t.notes,
                    'transactionID': t.transactionID
                } for t in self.get_tax_related_transactions(
                    date(summary['year'], 1, 1),
                    date(summary['year'], 12, 31)
                )
            ]
        }
         #end of Sprint 5 part Temka Tax

    #Another sprint 5 part Temka Travel
    def get_travel_transactions(self, start_date: date = None, end_date: date = None) -> List[Transaction]:
        travel_transactions = [t for t in self.transactions if t.isTravelRelated]
        
        if start_date and end_date:
            travel_transactions = [t for t in travel_transactions 
                                if start_date <= t.date <= end_date]
        
        return travel_transactions

    def get_travel_summary(self, start_date: date = None, end_date: date = None) -> dict:
        travel_transactions = self.get_travel_transactions(start_date, end_date)
        
        category_breakdown = {}
        total_travel_spending = 0.0
        
        for transaction in travel_transactions:
            cat_id = transaction.categoryID
            if cat_id not in category_breakdown:
                category_breakdown[cat_id] = {
                    'total': 0.0,
                    'count': 0
                }
            
            category_breakdown[cat_id]['total'] += transaction.total
            category_breakdown[cat_id]['count'] += 1
            total_travel_spending += transaction.total
        
        return {
            'total_travel_spending': total_travel_spending,
            'transaction_count': len(travel_transactions),
            'category_breakdown': category_breakdown,
            'period': {
                'start': start_date,
                'end': end_date
            },
            'transactions': [
                {
                    'transactionID': t.transactionID,
                    'date': t.date,
                    'payee': t.payee,
                    'amount': t.total,
                    'categoryID': t.categoryID,
                    'notes': t.notes
                } for t in travel_transactions
            ]
        }

    def bulk_flag_travel(self, transaction_ids: List[int]) -> Tuple[int, List[int]]:
        success_count = 0
        failed_ids = []
        
        for trans_id in transaction_ids:
            transaction = self.get_transaction_by_id(trans_id)
            if transaction:
                transaction.flag_as_travel()
                success_count += 1
            else:
                failed_ids.append(trans_id)
        
        return success_count, failed_ids

    def bulk_unflag_travel(self, transaction_ids: List[int]) -> Tuple[int, List[int]]:
        success_count = 0
        failed_ids = []
        
        for trans_id in transaction_ids:
            transaction = self.get_transaction_by_id(trans_id)
            if transaction:
                transaction.unflag_travel()
                success_count += 1
            else:
                failed_ids.append(trans_id)
        
        return success_count, failed_ids

    def filter_by_travel_flag(self, include_travel: bool = True) -> List[Transaction]:
        if include_travel:
            return [t for t in self.transactions if t.isTravelRelated]
        else:
            return [t for t in self.transactions if not t.isTravelRelated]
    #end of Another sprint 5 part Temka Travel


class PayFrequency(Enum):
    DAILY = "daily"
    WEEKLY = "1 week"
    BI_WEEKLY = "bi-weekly"
    MONTHLY = "1 month"
    CUSTOM = "custom"
class Income:
    def __init__ (self, incomeID, userID, name, amount, payFrequency, datePaid, isActive=True, customDays: Optional[int] = None):
        self.incomeID = incomeID
        self.userID = userID
        self.name = name
        self.amount = amount
        self.payFrequency = payFrequency
        self.datePaid = datePaid
        self.isActive = isActive
        self.customDays = customDays
        self.date_created = date.today()

    #getters
    def get_incomeID(self):
        return self.incomeID
    def get_userID(self):
        return self.userID
    def get_name(self):
        return self.name
    def get_amount(self):
        return self.amount
    def get_payFrequency(self):
        return self.payFrequency
    def get_datePaid(self):
        return self.datePaid
    def get_isActive(self):
        return self.isActive
    def get_customDays(self):
        return self.customDays
    
    #setters
    def set_incomeID(self, incomeID):
        self.incomeID = incomeID
    def set_userID(self, userID):
        self.userID = userID
    def set_name(self, name):
        self.name = name
    def set_amount(self, amount):
        self.amount = amount
    def set_payFrequency(self, payFrequency):
        self.payFrequency = payFrequency
    def set_datePaid(self, datePaid):
        self.datePaid = datePaid
    def set_isActive(self, isActive):
        self.isActive = isActive
    def set_customDays(self, customDays):
        self.customDays = customDays

    def apply_income_to_budgets(self, dbConnection) -> bool:
        try:
            cursor = dbConnection.cursor(dictionary=True)

            currentMonth = date.today().replace(day=1)

            updateQuery = """UPDATE bankBudget SET income = income + %s WHERE userID = %s AND month = %s"""
            cursor.execute(updateQuery, (self.amount, self.userID, currentMonth))

            dbConnection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error applying income to budgets: {e}")
            dbConnection.rollback()
            return False

    def add_income(self, dbConnection) -> bool:
        try:
            cursor = dbConnection.cursor(dictionary=True)
            query = """INSERT INTO bankIncome (userID, name, amount, payFrequency,
            datePaid, isActive, customDays, date_created)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (
                self.userID, self.name, self.amount, self.payFrequency, self.datePaid,
                self.isActive, self.customDays, self.date_created
            )
            cursor.execute(query, values)
            dbConnection.commit()

            self.incomeID = cursor.lastrowid
            self.apply_income_to_budgets(dbConnection)
            cursor.close()
            return True
        except Exception as e:
            print(f"Error adding income: {e}")
            return False
    def update_income(self, dbConnection, name: str = None, amount: float = None, payFrequency: str = None,
                      datePaid: date = None, customDays: Optional[int] = None):
        try:
            cursor = dbConnection.cursor()
            query = """UPDATE bankIncome SET name = %s, amount = %s, payFrequency = %s,
            datePaid = %s, customDays = %s WHERE idbankIncome = %s"""
            values = (
                name if name else self.name,
                amount if amount else self.amount,
                payFrequency if payFrequency else self.payFrequency,
                datePaid if datePaid else self.datePaid,
                customDays if customDays else self.customDays,
                self.incomeID
            )
            cursor.execute(query, values)
            dbConnection.commit()
            cursor.close()

            if name: self.name = name
            if amount: self.amount = amount
            if payFrequency: self.payFrequency = payFrequency
            if datePaid: self.datePaid = datePaid
            if customDays: self.customDays = customDays
        except Exception as e:
            print(f"Error updating income: {e}")
    def delete_income(self, dbConnection) -> bool:
        try:
            cursor = dbConnection.cursor()
            query = "DELETE FROM bankIncome WHERE idbankIncome = %s"
            cursor.execute(query, (self.incomeID,))
            dbConnection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error deleting income: {e}")
            return False
    @staticmethod
    def get_user_incomes(dbConnection, userID: str):
        try:
            cursor = dbConnection.cursor(dictionary=True)
            query = "SELECT * FROM bankIncome WHERE userID = %s AND isActive = 1 ORDER BY datePaid DESC"
            cursor.execute(query, (userID,))
            rows = cursor.fetchall()

            incomes = []
            for row in rows:
                income = Income(
                    incomeID=row['idbankIncome'],
                    userID=row['userID'],
                    name=row['name'],
                    amount=float(row['amount']),
                    payFrequency=row['payFrequency'],
                    datePaid=row['datePaid'],
                    isActive=bool(row.get('isActive', True)),
                    customDays=row.get('customDays')
                )
                incomes.append(income)

            cursor.close()
            return incomes
        except Exception as e:
            print(f"Error getting user incomes: {e}")
            return []
        
    @staticmethod
    def get_income_by_id(dbConnection, incomeID: int):
        try:
            cursor = dbConnection.cursor(dictionary=True)
            query = "SELECT * FROM bankIncome WHERE idbankIncome = %s"
            cursor.execute(query, (incomeID,))
            row = cursor.fetchone()

            if row:
                income = Income(
                    incomeID=row['idbankIncome'],
                    userID=row['userID'],
                    name=row['name'],
                    amount=float(row['amount']),
                    payFrequency=row['payFrequency'],
                    datePaid=row['datePaid'],
                    isActive=bool(row.get('isActive', True)),
                    customDays=row.get('customDays')
                )
                income.isActive = bool(row.get('isActive', True))
                income.date_created = row.get('date_created', date.today())
                cursor.close()
                return income
            cursor.close()
            return None
        except Exception as e:
            print(f"Error getting income by ID: {e}")
            return None

    def add_month(self, fromDate: date) -> date:
        nextMonth = fromDate.month + 1
        nextYear = fromDate.year
        if nextMonth > 12:
            nextMonth = 1
            nextYear += 1

            try:
                return date(nextYear, nextMonth, fromDate.day)
            except ValueError:
                if nextMonth == 12:
                    return date(nextYear + 1, 1, 1) - timedelta(days=1)
                else:
                    return date(nextYear, nextMonth + 1, 1)
    def calc_next_payday(self, startDate: date = None) -> Optional[date]:
        if not self.isActive:
            raise ValueError("Cannot calculate payday for inactive income")
        if startDate is None:
            startDate = date.today()

        lastPaid = self.datePaid

        if lastPaid is None:
            print(f"Warning: Income {self.incomeID} has no datePaid, using current date")
            lastPaid = startDate

        payFreq = self.payFrequency.lower().strip()

        try:
            if payFreq == "daily":
                nextPayday = lastPaid + timedelta(days=1)
            elif payFreq == "weekly" or payFreq == "1 week":
                nextPayday = lastPaid + timedelta(weeks=1)
            elif payFreq == 'bi-weekly' or payFreq == 'biweekly' or payFreq == '2 weeks':
                nextPayday = lastPaid + timedelta(weeks=2)
            elif payFreq == 'monthly' or payFreq == '1 month':
                nextPayday = self.add_month(lastPaid)
            elif payFreq == 'annual' or payFreq == 'yearly':
                nextPayday = lastPaid.replace(year=lastPaid.year + 1)
            elif payFreq == "one-time" or payFreq == "one time":
                return None
            elif payFreq == "custom" and self.customDays:
                nextPayday = lastPaid + timedelta(days=self.customDays)
            else:
                raise ValueError(f"Unsupported pay frequency: {self.payFrequency}")
            
            if nextPayday is None:
                return None
       
            while nextPayday <= startDate:
                if payFreq == "daily":
                    nextPayday += timedelta(days=1)
                elif payFreq == "weekly" or payFreq == "1 week":
                    nextPayday += timedelta(weeks=1)
                elif payFreq == "bi-weekly" or payFreq == "biweekly" or payFreq == "2 weeks":
                    nextPayday += timedelta(weeks=2)
                elif payFreq == "monthly" or payFreq == "1 month":
                    nextPayday = self.add_month(nextPayday)
                elif payFreq == "annual" or payFreq == "yearly":
                    nextPayday = nextPayday.replace(year=nextPayday.year + 1)
                elif payFreq == "custom" and self.customDays:
                    nextPayday += timedelta(days=self.customDays)
                else:
                    break
            return nextPayday
        except Exception as e:
            print(f"error calculating next payday for income {self.incomeID}: {e}")
            return None
        
    def should_pay_today(self):
        try:
            nextPayday = self.calc_next_payday()
            return nextPayday == date.today() if nextPayday else False
        except ValueError:
            return False
    def get_upcoming_paydays(self, count: int = 5, startDate: Optional[date] = None) -> List[date]:
        if not self.isActive:
            return []
        if startDate is None:
            startDate = date.today()

        paydays = []
        currDate = self.datePaid

        nextPayday = self.calc_next_payday(startDate)
        if not nextPayday:
            return []
        
        paydays.append(nextPayday)

        for i in range(count - 1):
            if self.payFrequency == PayFrequency.DAILY.value:
                nextPayday += timedelta(days=1)
            elif self.payFrequency == PayFrequency.WEEKLY.value:
                nextPayday += timedelta(weeks=1)
            elif self.payFrequency == PayFrequency.BI_WEEKLY.value:
                nextPayday += timedelta(weeks=2)
            elif self.payFrequency == PayFrequency.MONTHLY.value:
                nextPayday = self.add_month(nextPayday)
            elif self.payFrequency == PayFrequency.CUSTOM.value and self.customDays:
                nextPayday += timedelta(days = self.customDays)
            paydays.append(nextPayday)
        return paydays
    
    #Added by Temka, commenting to find my code later easier for debugging. Part of Sprint 2.
    def add_manual_transaction(transaction_manager: TransactionManager, userID: str, total: float, date_: date,
                           payee: str, categoryID: int, notes: str = "", expenseType: ExpenseType = None):

        new_transaction = Transaction(
            transactionID=len(transaction_manager.transactions) + 1,
            userID=userID,
            total=total,
            date=date_,
            payee=payee,
            categoryID=categoryID,
            notes=notes,
            isRecurring=False,
            expenseType=expenseType
        )

        transaction_manager.add_transaction(new_transaction)

        print(f"\nTransaction Added Successfully:")
        print(f"  ID: {new_transaction.transactionID}")
        print(f"  Payee: {new_transaction.payee}")
        print(f"  Amount: ${new_transaction.total:.2f}")
        print(f"  Category ID: {new_transaction.categoryID}")
        print(f"  Date: {new_transaction.date}")
        print(f"  Type: {new_transaction.expenseType.value if new_transaction.expenseType else 'Unspecified'}")
        print(f"  Notes: {new_transaction.notes}\n")

        return new_transaction
    
    #Added by Temka, commenting to find my code later easier for debugging. Part of Sprint 1.
    def add_one_time_income(userID, name, amount, datePaid):
        new_income = Income(
            incomeID = 1,
            userID = userID,
            name = name,
            amount = amount,
            payFrequency = "one time",
            datePaid = datePaid
        )
        print(f"Added one time income: {new_income.name} ${new_income.amount} on {new_income.datePaid}")
        return new_income
    
    #Added by Temka, commenting to find my code later easier for debugging. Part of Sprint 1.
    def calculate_total_monthly_income(income_sources, previousTotal):
        currentTotal = previousTotal

        for income_obj in income_sources:
            amount = income_obj.amount
            payFrequency = income_obj.payFrequency.lower()

            if payFrequency == "weekly":
                currentTotal += amount * 4
            elif payFrequency == "biweekly":
                currentTotal += amount * 2
            elif payFrequency == "monthly":
                currentTotal += amount
            elif payFrequency == "annual":
                currentTotal += amount / 12
        
        return currentTotal

#Added by Temka, commenting to find my code later easier for debugging. Part of Sprint 2.
class Expense:
    def __init__(self, expenseID: int, userID: int, name: str, amount: float, category: str, payFrequency: str, startDate: date):
        self.expenseID = expenseID
        self.userID = userID
        self.name = name
        self.amount = amount
        self.category = category
        self.payFrequency = payFrequency.lower()
        self.startDate = startDate
        self.nextDate = startDate

    def __str__(self):
        return f"{self.name} ({self.category}) - ${self.amount:.2f} [{self.payFrequency.capitalize()}] Next: {self.nextDate}"

    def get_next_occurrence(self):
        if self.payFrequency == "weekly":
            self.nextDate += timedelta(weeks=1)
        elif self.payFrequency == "biweekly":
            self.nextDate += timedelta(weeks=2)
        elif self.payFrequency == "monthly":
            new_month = self.nextDate.month + 1 if self.nextDate.month < 12 else 1
            new_year = self.nextDate.year if self.nextDate.month < 12 else self.nextDate.year + 1
            self.nextDate = self.nextDate.replace(year=new_year, month=new_month)
        elif self.payFrequency == "annual":
            self.nextDate = self.nextDate.replace(year=self.nextDate.year + 1)
        return self.nextDate

    def post_expense(self, expenses_list):
        expenses_list.append({
            "name": self.name,
            "amount": self.amount,
            "category": self.category,
            "date": self.nextDate
        })
        print(f"Recurring expense '{self.name}' posted for {self.nextDate}.")
        self.get_next_occurrence()

#Added by Temka, commenting to find my code later easier for debugging. Part of Sprint 2.
def add_recurring_transportation_expense(expenses, userID, name, amount, category, payFrequency, startDate=None):
    if startDate is None:
        startDate = date.today()
    
    new_expense = Expense(
        expenseID=len(expenses),
        userID=userID,
        name=name,
        amount=amount,
        category=category,
        payFrequency=payFrequency,
        startDate=startDate
    )

    expenses.append(new_expense)
    print(f"Transportation expense '{name}' added as a recurring {payFrequency} cost under '{category}'.")
    return new_expense