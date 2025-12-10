from typing import List, Optional
from Money import *
import mysql.connector

class Budget:
    def __init__(self, budgetID: int, userID: str, name: str, totalPlannedAmnt: float, month: str, income: float):
        self.budgetID = budgetID
        self.userID = userID
        self.name = name
        self.totalPlannedAmnt = totalPlannedAmnt
        self.month = month
        self.income = income
        self.categories = []

    def createBudget(self, dbConnection) -> bool:
        try:
            cursor = dbConnection.cursor(dictionary=True)
            query = """INSERT bankBudget (userID, Name, totalPlanned, month, income)
            VALUES (%s, %s, %s, %s, %s)"""

            values = (self.userID, self.name, self.totalPlannedAmnt, self.month, self.income)
            cursor.execute(query, values)
            dbConnection.commit()

            self.budgetID = cursor.lastrowid

            for category in self.categories:
                category.createCategory(dbConnection, self.budgetID)

            cursor.close()
            print(f"Budget '{self.name} created with id {self.budgetID}")
            return True
        except Exception as e:
            print(f"Error creating budget: {e}")
            return False

    def editBudget(self, dbConnection, name: str = None, totalPlannedAmnt: float = None, month: str = None, income: float = None):
        try:
            cursor = dbConnection.cursor()
            query = """UPDATE bankBudget SET Name = %s, totalPlanned = %s, month = %s, income = %s
            WHERE idbankBudget = %s"""

            values = (
                name if name else self.name,
                totalPlannedAmnt if totalPlannedAmnt else self.totalPlannedAmnt,
                month if month else self.month,
                income if income else self.income,
                self.budgetID
            )
            cursor.execute(query, values)
            dbConnection.commit()
            cursor.close()

            if name: self.name = name
            if totalPlannedAmnt: self.totalPlannedAmnt = totalPlannedAmnt
            if month: self.month = month
            if income: self.income = income

            print(f"Budget {self.name} updated.")
        except Exception as e:
            print(f"Error updating budget: {e}")

    def deleteBudget(self, dbConnection) -> bool:
        try:
            cursor = dbConnection.cursor()
            query = "DELETE FROM bankBudget WHERE idbankBudget = %s"
            cursor.execute(query, (self.budgetID,))
            dbConnection.commit()
            cursor.close()
            print(f"Budget {self.name} deleted.")
            return True
        except Exception as e:
            print(f"Error deleting budget: {e}")
            return False

    def calculateTotalPlannedAmnt(self):
        self.totalPlannedAmnt = sum(cat.plannedAmnt for cat in self.categories)
        return self.totalPlannedAmnt

    def budgetTracking(self):
        print(f"{self.name} total planned = {self.totalPlannedAmnt}")

    def addCategory(self, category: 'Category'):
        self.categories.append(category)
        self.calculateTotalPlannedAmnt()
        print(f"Category '{category.name}' added to budget '{self.name}'")

    def editCategory(self, dbConnection, categoryID: int, name: str = None, type: str = None, 
                     plannedAmnt: float = None, plannedPercentage: float = None):
        category = self.getCategoryByID(categoryID)
        if category:
            category.editCategory(dbConnection, name, type, plannedAmnt, plannedPercentage, self.income)
            self.calculateTotalPlannedAmnt()
            print(f"Category {categoryID} updated")
        else:
            print(f"Category with ID {categoryID} not found.")

    def deleteCategory(self, dbConnection, categoryID: int):
        category = self.getCategoryByID
        if category:
            success = category.deleteCategory(dbConnection)
            if success:
                self.categories.remove(category)
                self.calculateTotalPlannedAmnt()
                print(f"Category {categoryID} deleted.")
            else: print(f"Failed to delete category {categoryID} from database.")
        else:
            print(f"Category with ID {categoryID} not found.")
    
    def getCategoryByID(self, categoryID: int) -> Optional['Category']:
        return next((cat for cat in self.categories if cat.categoryID == categoryID), None)
    
    def setIncome(self, dbConnection, income: float):
        self.income = income

        try:
            cursor = dbConnection.cursor()
            query = "UPDATE bankBudget SET income = %s WHERE idbankBudget = %s"

            cursor.execute(query, (income, self.budgetID))
            dbConnection.commit()
            cursor.close()

            for category in self.categories:
                if category.plannedPercentage is not None:
                    category.setPlannedPercentage(dbConnection, category.plannedPercentage, income)

                    self.calculateTotalPlannedAmnt()
        except Exception as e:
            print(f"Error setting income: {e}")
    
    def get_budget_data(self) -> dict:
        return {
        'budgetID': self.budgetID,
        'name': self.name,
        'totalPlannedAmnt': self.totalPlannedAmnt,
        'month': self.month,
        'income': self.income,
        'categories': [
            {
                'categoryID': cat.categoryID,
                'name': cat.name,
                'type': cat.type,
                'plannedAmnt': cat.plannedAmnt,
                'plannedPercentage': cat.plannedPercentage,
                'categoryLimit': cat.categoryLimit
            } for cat in self.categories
        ]
    }

    @staticmethod
    def get_user_budgets(dbConnection, userID: str):
        try:
            cursor = dbConnection.cursor(dictionary = True)
            query = "SELECT * FROM bankBudget WHERE userID = %s ORDER BY month DESC"
            cursor.execute(query, (userID,))
            rows = cursor.fetchall()

            budgets = []
            for row in rows:
                budget = Budget(
                    budgetID=row['idbankBudget'],
                    userID=row['userID'],
                    name=row['Name'],
                    totalPlannedAmnt=float(row['totalPlanned']),
                    month = row['month'],
                    income = float(row['income']) if row['income'] else 0.0
                )

                budget.categories = Category.get_categories_for_budget(dbConnection, budget.budgetID)
                budgets.append(budget)

            cursor.close()
            return budgets
        except Exception as e:
            print(f"Error loading user budgets: {e}")
            return []
        
    @staticmethod
    def get_budget_by_id(dbConnection, budgetID: int):
        try:
            cursor = dbConnection.cursor(dictionary=True)
            query = "SELECT * FROM bankBudget WHERE idbankBudget = %s"
            cursor.execute(query, (budgetID,))
            row = cursor.fetchone()

            if row:
                budget = Budget(
                    budgetID=row['idbankBudget'],
                    userID=row['userID'],
                    name=row['Name'],
                    totalPlannedAmnt=float(row['totalPlanned']),
                    month=row['month'],
                    income=float(row['income']) if row['income'] else 0.0
                )

                budget.categories = Category.get_categories_for_budget(dbConnection, budget.budgetID)
                cursor.close()
                return budget
            cursor.close()
            return None
        except Exception as e:
            print(f"Error getting budget by ID: {e}")
            return None

    #==========Part of sprint 4 by Temka, for the Budget user story.============
    def update_category_amount(self, dbConnection, categoryID: int, newAmount: float) -> bool:
        category = self.getCategoryByID(categoryID)
        if category:
            return category.setPlannedAmnt(dbConnection, newAmount)
        else:
            print(f"Category with ID {categoryID} not found.")
            return False

    def validate_budget_changes(self) -> tuple[bool, str]:
        if self.totalPlannedAmnt < 0:
            return False, "Total planned amount cannot be negative"
        if not self.categories:
            return False, "Budget must have at least one category"
        for cat in self.categories:
            if cat.plannedAmnt < 0:
                return False, f"Category '{cat.name}' cannot have negative amount"
        return True, "Budget is valid"

    def save_budget_changes(self, dbConnection) -> tuple[bool, str]:
        is_valid, message = self.validate_budget_changes()
        if not is_valid:
            return False, message
       
        try:
            self.editBudget(dbConnection, self.name, self.totalPlannedAmnt, self.month, self.income)
            return True, "Budget saved successfully"
        except Exception as e:
            return False, f"Error saving budget: {str(e)}"

    def discard_changes(self, original_data: dict):
        self.name = original_data['name']
        self.totalPlannedAmnt = original_data['totalPlannedAmnt']
        self.month = original_data['month']
        self.income = original_data['income']
        for cat_data in original_data['categories']:
            category = self.getCategoryByID(cat_data['categoryID'])
            if category:
                category.plannedAmnt = cat_data['plannedAmnt']
                category.plannedPercentage = cat_data['plannedPercentage']
        print(f"Budget '{self.name}' changes discarded")
    #==========End of part of sprint 4 by Temka, for the Budget user story.============

    #==========Part of sprint 5 by Temka============
    def get_category_comparison(self, categoryID: int, actual_spent: float) -> dict:
        category = self.getCategoryByID(categoryID)
        if not category:
            return None
        
        planned = category.plannedAmnt
        difference = actual_spent - planned
        percentage_used = (actual_spent / planned * 100) if planned > 0 else 0
        
        if actual_spent <= planned * 0.9:
            status = "on_track"
        elif actual_spent <= planned:
            status = "near_limit"
        else:
            status = "over_budget"
        
        return {
            'categoryID': categoryID,
            'name': category.name,
            'planned': planned,
            'actual': actual_spent,
            'difference': difference,
            'percentage_used': round(percentage_used, 2),
            'status': status
        }

    def get_full_budget_comparison(self, spending_data: dict) -> dict:
        comparisons = []
        total_planned = 0.0
        total_actual = 0.0
        
        for category in self.categories:
            actual_spent = spending_data.get(category.categoryID, 0.0)
            comparison = self.get_category_comparison(category.categoryID, actual_spent)
            if comparison:
                comparisons.append(comparison)
                total_planned += comparison['planned']
                total_actual += comparison['actual']
        
        return {
            'budgetID': self.budgetID,
            'name': self.name,
            'month': self.month,
            'income': self.income,
            'total_planned': total_planned,
            'total_actual': total_actual,
            'total_difference': total_actual - total_planned,
            'categories': comparisons
        }

    def get_budget_health_summary(self, spending_data: dict) -> dict:
        comparison = self.get_full_budget_comparison(spending_data)
        
        on_track_count = sum(1 for c in comparison['categories'] if c['status'] == 'on_track')
        over_budget_count = sum(1 for c in comparison['categories'] if c['status'] == 'over_budget')
        total_categories = len(comparison['categories'])
        
        if over_budget_count == 0:
            overall_status = "healthy"
        elif over_budget_count <= total_categories * 0.3:
            overall_status = "caution"
        else:
            overall_status = "needs_attention"
        
        return {
            'overall_status': overall_status,
            'on_track_count': on_track_count,
            'over_budget_count': over_budget_count,
            'total_categories': total_categories,
            'budget_utilization': round((comparison['total_actual'] / comparison['total_planned'] * 100), 2) if comparison['total_planned'] > 0 else 0
        }
    #==========End of part of sprint 5 by Temka============
    
class Category:
    def __init__(self, categoryID: int, name: str, type_: str, categoryLimit: float, plannedAmnt: float, plannedPercentage: float):
        self.categoryID = categoryID
        self.name = name
        self.type = type_
        self.categoryLimit = categoryLimit
        self.plannedAmnt = plannedAmnt
        self.plannedPercentage = plannedPercentage

    def createCategory(self, dbConnection, budgetID: int) -> bool:
        try:
            cursor = dbConnection.cursor(dictionary=True)
            query = """INSERT INTO bankCategory (budgetID, name, type, plannedAmnt, plannedPerc, categoryLimit)
            VALUES (%s, %s, %s, %s, %s, %s)"""

            values = (budgetID, self.name, self.type, self.plannedAmnt, self.plannedPercentage, self.categoryLimit)
            cursor.execute(query, values)
            dbConnection.commit()

            self.categoryID = cursor.lastrowid
            cursor.close()
            print(f"Category '{self.name}' added.")
            return True
        except Exception as e:
            print(f"Error creating category: {e}")
            return False

    def editCategory(self, dbConnection, name: str = None, type_: str = None, plannedAmnt: float = None, plannedPercentage: float = None, budgetIncome: float = None):
        try:
            if name: self.name = name
            if type_: self.type = type_
            if plannedAmnt is not None:
                self.plannedAmnt = plannedAmnt
                self.plannedPercentage = None
            if plannedPercentage is not None and budgetIncome:
                self.plannedPercentage = plannedPercentage
                self.plannedAmnt = (plannedPercentage / 100) * budgetIncome
            
            cursor = dbConnection.cursor()
            query = """UPDATE bankCategory SET name= %s, type = %s, plannedAmnt = %s, plannedPerc = %s, categoryLimit = %s
            WHERE idbankCategory = %s"""
            values = (self.name, self.type, self.plannedAmnt, self.plannedPercentage, self.categoryLimit, self.categoryID)
            cursor.execute(query, values)
            dbConnection.commit()
            cursor.close()
            print(f"Category {self.categoryID} updated.")
        except Exception as e:
            print(f"Error updating category: {e}")

    def deleteCategory(self, dbConnection) -> bool:
        try:
            cursor = dbConnection.cursor()
            query = "DELETE FROM bankCategory WHERE idbankCategory = %s"
            cursor.execute(query, (self.categoryID,))
            dbConnection.commit()
            cursor.close()
            print(f"Category {self.categoryID} deleted.")
            return True
        except Exception as e:
            print(f"Error deleting category: {e}")
            return False

    def editLimit(self, dbConnection, newLimit: float):
        try:
            cursor = dbConnection.cursor()
            query = "UPDATE bankCategory SET categoryLimit = %s WHERE idbankCategory = %s"
            cursor.execute(query, (newLimit, self.categoryID))
            dbConnection.commit()
            cursor.close()
            self.categoryLimit = newLimit
            print(f"Category {self.categoryID} limit updated to {newLimit}")
        except Exception as e:
            print(f"Error updating category limit: {e}")

    def setPlannedAmnt(self, dbConnection, amount: float) -> bool:
        try:
            cursor = dbConnection.cursor()
            query = "UPDATE bankCategory SET plannedAmnt = %s, plannedPerc = NULL WHERE idbankCategory = %s"
            cursor.execute(query, (amount, self.categoryID))
            dbConnection.commit()
            cursor.close()
            self.plannedAmnt = amount
            self.plannedPercentage = None
            print(f"Category {self.categoryID} planned amount set to {amount}")
            return True
        except Exception as e:
            print(f"Error setting planned amount: {e}")
            return False

    def setPlannedPercentage(self, dbConnection, percentage: float, budgetIncome: float) -> bool:
        try:
            plannedAmnt = (percentage / 100) * budgetIncome
            cursor = dbConnection.cursor()
            query = "UPDATE bankCategory SET plannedAmnt = %s, plannedPerc = %s WHERE idbankCategory = %s"
            cursor.execute(query, (plannedAmnt, percentage, self.categoryID))
            dbConnection.commit()
            cursor.close()
            self.plannedPercentage = percentage
            self.plannedAmnt = (percentage / 100) * budgetIncome
            print(f"Category {self.categoryID} planned percentage set to {percentage}% (${self.plannedAmnt:.2f})")
            return True
        except Exception as e:
            print(f"Error setting planned percentage: {e}")
            return False
    
    @staticmethod
    def get_categories_for_budget(dbConnection, budgetID: int):
        try:
            cursor = dbConnection.cursor(dictionary=True)
            query = "SELECT * FROM bankCategory WHERE budgetID = %s"
            cursor.execute(query, (budgetID,))
            rows = cursor.fetchall()

            categories = []
            for row in rows:
                category = Category(
                    categoryID=row['idbankCategory'],
                    name=row['name'],
                    type_=row['type'],
                    categoryLimit=float(row['categoryLimit']) if row['categoryLimit'] is not None else 0.0,
                    plannedAmnt=float(row['plannedAmnt']) if row['plannedAmnt'] is not None else 0.0,
                    plannedPercentage=float(row['plannedPerc']) if row['plannedPerc'] is not None else None
                )
                categories.append(category)
            
            cursor.close()
            return categories
        except Exception as e:
            print(f"Error loading categories for budget: {e}")
            return []
    
    def get_category_by_id(dbConnection, categoryID: int):
        try:
            cursor = dbConnection.cursor(dictionary=True)
            query = "SELECT * FROM bankCategory WHERE idbankCategory = %s"
            cursor.execute(query, (categoryID,))
            row = cursor.fetchone()

            if row:
                category = Category(
                    categoryID=row['idbankCategory'],
                    name=row['name'],
                    type_=row['type'],
                    categoryLimit=float(row['categoryLimit']) if row['categoryLimit'] is not None else 0.0,
                    plannedAmnt=float(row['plannedAmnt']) if row['plannedAmnt'] is not None else 0.0,
                    plannedPercentage=float(row['plannedPerc']) if row['plannedPerc'] is not None else None
                )
                cursor.close()
                return category
            cursor.close()
            return None
        except Exception as e:
            print(f"Error getting category by ID: {e}")
            return None

#Part of sprint 1 by Temka
class BudgetTemplate:
    def __init__(self, templateID: int, name: str, description: str, categories: List[Category] = None):
        self.templateID = templateID
        self.name = name
        self.description = description
        self.categories = categories if categories else []

    def createBudgetFromTemplate(self, dbConnection, budgetID: int, userID: str, month: str, income: float = 0.0):
        newBudget = Budget(
            budgetID=0,
            userID=userID,
            name=self.name,
            totalPlannedAmnt=0.0,
            month=month,
            income=income
        )

        success = newBudget.createBudget(dbConnection)
        if not success:
            return None
        
        for templateCat in self.categories:
            category = Category(
                categoryID=0,
                name=templateCat.name,
                type_=templateCat.type,
                categoryLimit=templateCat.categoryLimit,
                plannedAmnt=templateCat.plannedAmnt,
                plannedPercentage=templateCat.plannedPercentage
            )
            category.createCategory(dbConnection, newBudget.budgetID)
            newBudget.categories.append(category)

        newBudget.calculateTotalPlannedAmnt()
        print(f"Budget created from template '{self.name}' for user {userID}")
        return newBudget
    
    #===== part of Sprint 5 Temka
    def get_template_description(self) -> str:
        return self.description

    def get_template_categories(self) -> List[dict]:
        return [
            {
                'categoryID': cat.categoryID,
                'name': cat.name,
                'type': cat.type,
                'suggestedAmount': cat.plannedAmnt,
                'categoryLimit': cat.categoryLimit
            } for cat in self.categories
        ]

    def clone_for_user(self, budgetID: int, userID: str, month: str, income: float = 0.0) -> Budget:
        new_budget = Budget(
            budgetID=budgetID,
            userID=userID,
            name=self.name,
            totalPlannedAmnt=0.0,
            month=month,
            income=income
        )
        
        # Clone categories with original suggested values
        for cat in self.categories:
            new_category = Category(
                categoryID=cat.categoryID,
                name=cat.name,
                type_=cat.type,
                categoryLimit=cat.categoryLimit,
                plannedAmnt=cat.plannedAmnt,
                plannedPercentage=cat.plannedPercentage
            )
            new_budget.categories.append(new_category)
        
        new_budget.calculateTotalPlannedAmnt()
        return new_budget
    #====end of part of Sprint 5 Temka

#Part of sprint 3 by Temka
class BudgetManager:
    def __init__(self, dbConfig=None):
        self.dbConfig = dbConfig
        self.categories: dict[int, Category] = {}      
        self.spending: dict[int, float] = {}  

    def get_db_connection(self):
        if self.dbConfig:
            return mysql.connector.connect(**self.dbConfig)
        return None

    def add_category(self, category: Category):
        if category.categoryID not in self.categories:
            self.categories[category.categoryID] = category
            self.spending[category.categoryID] = 0.0
            print(f"Category '{category.name}' added with limit ${category.categoryLimit:.2f}")
        else:
            print(f"Category '{category.name}' already exists.")

    def record_transaction(self, transaction: Transaction):
        cat_id = transaction.categoryID

        if cat_id not in self.categories:
            print(f"Transaction {transaction.transactionID} uses an unknown category (ID {cat_id}).")
            return

        amount = transaction.total
        self.spending[cat_id] += amount
        category = self.categories[cat_id]

        print(f"Added ${amount:.2f} to '{category.name}'. "
              f"Total spent: ${self.spending[cat_id]:.2f} / ${category.categoryLimit:.2f}")

        if self.spending[cat_id] > category.categoryLimit:
            print(f"WARNING: You’ve exceeded your monthly limit for '{category.name}'!\n")

    def get_summary(self):
        print("\nBudget Summary:")
        for cat_id, category in self.categories.items():
            spent = self.spending.get(cat_id, 0.0)
            status = "Over Limit!" if spent > category.categoryLimit else "Within Limit"
            print(f"  - {category.name}: ${spent:.2f} / ${category.categoryLimit:.2f} ({status})")

    #==Part of sprint 4 by Temka==
    def get_spending_by_category(self) -> dict:
        category_totals = {}
        
        for cat_id, category in self.categories.items():
            spent = self.spending.get(cat_id, 0.0)
            category_totals[category.name] = {
                'amount': spent,
                'categoryID': cat_id,
                'limit': category.categoryLimit
            }
        
        return category_totals

    def get_chart_data(self, period: str = 'current_month') -> dict:
        spending_data = self.get_spending_by_category()
        
        chart_data = {
            'labels': [],
            'amounts': [],
            'colors': [],
            'period': period
        }
        
        for category_name, data in spending_data.items():
            if data['amount'] > 0:  # Only include categories with spending
                chart_data['labels'].append(category_name)
                chart_data['amounts'].append(data['amount'])
        
        return chart_data
    #==End of Part of sprint 4 by Temka==


 #===Part of Sprint 5 Temka
class BudgetTemplateManager:
    
        def __init__(self, dbConfig=None):
            self.dbConfig = dbConfig
            self.templates: List[BudgetTemplate] = []
            self._initialize_default_templates()

        def get_db_connection(self):
            if self.dbConfig:
                return mysql.connector.connect(**self.dbConfig)
            return None
        
        def _initialize_default_templates(self):
            fifty_thirty_twenty = BudgetTemplate(
                templateID=1,
                name="50/30/20 Budget",
                description="Allocate 50% of income to needs, 30% to wants, and 20% to savings/debt."
            )
            
            zero_based = BudgetTemplate(
                templateID=2,
                name="Zero-Based Budget",
                description="Assign every dollar a job so income minus expenses equals zero."
            )
            
            envelope = BudgetTemplate(
                templateID=3,
                name="Envelope Budget",
                description="Divide spending into specific categories with strict limits."
            )
            
            self.templates = [fifty_thirty_twenty, zero_based, envelope]
        
        def get_all_templates(self) -> List[BudgetTemplate]:
            return self.templates
        
        def get_template_by_id(self, templateID: int) -> Optional[BudgetTemplate]:
            return next((t for t in self.templates if t.templateID == templateID), None)
        
        def is_first_time_user(self, userID: str) -> bool:
            if not self.dbConfig:
                return True
            
            try:
                dbConnection = self.get_db_connection()
                cursor = dbConnection.cursor()
                query = "SELECT COUNT(*) FROM bankBudget WHERE userID = %s"
                cursor.execute(query, (userID,))
                result = cursor.fetchone()
                cursor.close()
                dbConnection.close()

                return result[0] == 0
            except Exception as e:
                print(f"Error checking first-time user: {e}")
                return True
        
        #====End of Sprint 5 part Temka

    