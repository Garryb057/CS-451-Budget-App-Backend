from flask import Flask, jsonify, request, session
from flask_cors import CORS
from datetime import date, datetime
from datetime import timedelta
import json
import mysql.connector
import secrets

from budget import *
from Money import *
from Pages import *
from User import User
from chart import BudgetChartManager
from notifications import NotificationManager, NotificationCategory, NotificationChannel
from notificationSettings import NotificationSettings
from BankEmail import send_verification_email

app = Flask(__name__)
app.secret_key = 'ajfab21021-219301231n-j43l21$@'
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

db = {
    'host': "localhost",
    'user': "root",
    'password': "Melt1129",
    'database': "banking_db"
}

def get_db_connection():
    return mysql.connector.connect(**db)

def get_db_cursor(connection):
    return connection.cursor(dictionary=True)

transactionManager = TransactionManager(db)
budgetManager = BudgetManager()
chartManager = BudgetChartManager(budgetManager, transactionManager)

sampleBudget = Budget(
   budgetID = 1,
   userID='user1',
   name="Montly Budget",
   totalPlannedAmnt=3000.0,
   month='October',
   income=4500.0
)

dashboard = Dashboard("user1", transactionManager)

#API Calls
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        user, msg = User.login(email, password, cursor)

        cursor.close()
        dbConnection.close()

        #Change with Alex Tokens
        if user:
            session['user_email'] = user.email
            session['user_fname'] = user.fname
            session['user_lname'] = user.lname
            session['user_id'] = user.get_userID()

            return jsonify({
                'success': True,
                'message': msg,
                'user': {
                    'userID': user.get_userID(),
                    'email': user.email,
                    'fname': user.fname,
                    'lname': user.lname,
                    'phoneNumber': user.phoneNumber
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': msg
            }), 401
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Login error: {str(e)}"
        }), 500
    
@app.route('/api/register', methods = ['POST'])
def register():
    try:
        data = request.get_json()

        newUser = User(
            email = data.get('email'),
            passwordHash=data.get('password'),
            fname = data.get('fname'),
            lname = data.get('lname'),
            phoneNumber = data.get('phoneNumber'),
            dateCreated = datetime.now()
        )

        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        success, msg = newUser.register(dbConnection, cursor)

        if success:
            # Generate verification token
            verificationToken = secrets.token_hex(32)
            tokenExpiry = datetime.now() + timedelta(hours=24)
            
            # Store token in database
            cursor.execute(
                "UPDATE bankUser SET verification_token = %s, token_expiry = %s WHERE email = %s",
                (verificationToken, tokenExpiry, newUser.email)
            )
            dbConnection.commit()
            
            # Send verification email
            emailSent = send_verification_email(newUser.email, verificationToken)
            
            cursor.close()
            dbConnection.close()
            
            if emailSent:
                return jsonify({
                    'success': True,
                    'message': 'Registration successful! Please check your email to verify your account.'
                }), 201
            else:
                return jsonify({
                    'success': True,
                    'message': 'Registration successful, but verification email failed to send. Please request a new verification email.'
                }), 201
        else:
            cursor.close()
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': msg
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Registration error: {str(e)}'
        }), 500
    
@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Logout error: {str(e)}'
        }), 500
    
@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_email' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'userID': session.get('user_id'),
                'email': session['user_email'],
                'fname': session.get('user_fname'),
                'lname': session.get('user_lname')
            }
        }), 200
    else:
        return jsonify({
            'authenticated': False
        }), 200
    
def get_user_profile():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        cursor.execute(
            "SELECT idbankUser, first_name, last_name, email, phone_number, dateCreated, is_Verified FROM bankUser WHERE idbankUser = %s",
            (session['user_id'],)
        )
        userData = cursor.fetchone()

        cursor.close()
        dbConnection.close()

        if userData:
            return jsonify({
                'success': True,
                'user': {
                    'userID': userData['idbankUser'],
                    'fname': userData['first_name'],
                    'lname': userData['last_name'],
                    'email': userData['email'],
                    'phoneNumber': userData['phone_number'],
                    'dateCreated': userData['dateCreated'].isoformat() if userData['dateCreated'] else None,
                    'isVerified': bool(userData['is_Verified'])
                }
            }), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching profile: {str(e)}'}), 500
 
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        userID = session['user_id']
        budgetID = request.args.get('budgetId', type=int)


        dbConnection = get_db_connection()

        totalMonthlyIncome = 0.0
        incomes = Income.get_user_incomes(dbConnection, userID)
        for income in incomes:
            if income.isActive:
                amount = income.amount
                payFrequency = income.payFrequency.lower()

                if payFrequency in ['weekly', '1 week']:
                    totalMonthlyIncome += amount * 4
                elif payFrequency in ['bi-weekly', 'biweekly', '2 weeks']:
                    totalMonthlyIncome += amount * 2
                elif payFrequency in ['monthly', '1 month']:
                    totalMonthlyIncome += amount
                elif payFrequency in ['annual', 'yearly']:
                    totalMonthlyIncome += amount / 12
                elif payFrequency in ['one-time', 'one time']:
                    continue
                else:
                    totalMonthlyIncome += amount

        userBudgets = Budget.get_user_budgets(dbConnection, userID)

        currentBudget = None
        if budgetID:
            currentBudget = Budget.get_budget_by_id(dbConnection, budgetID)
            if currentBudget and currentBudget.userID != userID:
                currentBudget = None
        
        if not currentBudget and userBudgets:
            currentBudget = userBudgets[0]

        if not currentBudget:
            dbConnection.close()
            return jsonify({
                'income': totalMonthlyIncome,
                'expenses': 0,
                'recentTransactions': [],
                'budgets': []
            })

        userDashboard = Dashboard(userID, transactionManager)
        recentTransactions = userDashboard.get_recent_transactions_widget_data(10)

        userTransactions = [t for t in transactionManager.transactions if t.userID == userID]
        totalSpending = sum(transaction.total for transaction in userTransactions)

        categorySpending = {}
        for transaction in userTransactions:
            catID = transaction.categoryID
            categorySpending[catID] = categorySpending.get(catID, 0.0) + transaction.total

        budgetsData = []
        if userBudgets:
            # Use the first budget for dashboard display
            currentBudget = userBudgets[0]
            for cat in currentBudget.categories:
                spent = categorySpending.get(cat.categoryID, 0.0)
                budgetsData.append({
                    'id': cat.categoryID,
                    'name': cat.name,
                    'total': cat.categoryLimit,
                    'spent': spent
                })

        dbConnection.close()

        return jsonify({
            'income': totalMonthlyIncome,
            'expenses': totalSpending,
            'recentTransactions': recentTransactions,
            'budgets': budgetsData
        })
    except Exception as e:
        print(f"Error in dashboard endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/budgets/current', methods=['GET'])
def get_current_budget():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        userID = session['user_id']
        
        userTransactions = [t for t in transactionManager.transactions if t.userID == userID]
        categorySpending = {}
        for transaction in userTransactions:
            catID = transaction.categoryID
            categorySpending[catID] = categorySpending.get(catID, 0.0) + transaction.total

        budgetsData = []
        for cat in sampleBudget.categories:
            spent = categorySpending.get(cat.categoryID, 0.0)
            budgetsData.append({
                'id': cat.categoryID,
                'name': cat.name,
                'total': cat.categoryLimit,
                'spent': spent,
                'percentage': min((spent / cat.categoryLimit) * 100, 100) if cat.categoryLimit > 0 else 0
            })

        return jsonify({
            'budgets': budgetsData,
            'month': sampleBudget.month,
            'totalIncome': sampleBudget.income
        })
    except Exception as e:
        print(f"Error in current budget endpoint: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        userID = session['user_id']
        
        # Use the same logic as get_all_transactions for consistency
        sortBy = request.args.get('sort', 'date-desc')
        categoryFilter = request.args.get('category', 'all')
        limit = request.args.get('limit', 100, type=int)
        
        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        query = """
            SELECT 
                t.idbankTransaction as id,
                t.date,
                t.payee,
                t.amount,
                t.notes,
                t.categoryID,
                c.name as categoryName,
                t.expenseType
            FROM bankTransaction t
            LEFT JOIN bankCategory c ON t.categoryID = c.idbankCategory
            WHERE t.userID = %s
        """
        params = [userID]

        if categoryFilter != 'all':
            query += " AND c.name = %s"
            params.append(categoryFilter)

        if sortBy == 'date-desc':
            query += " ORDER BY t.date DESC"
        elif sortBy == 'date-asc':
            query += " ORDER BY t.date ASC"
        elif sortBy == 'amount-desc':
            query += " ORDER BY t.amount DESC"
        elif sortBy == 'amount-asc':
            query += " ORDER BY t.amount ASC"
        elif sortBy == 'payee':
            query += " ORDER BY t.payee ASC"
        elif sortBy == 'category':
            query += " ORDER BY c.name ASC"

        query += " LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        transactions = cursor.fetchall()

        transactions_data = []
        for transaction in transactions:
            transaction_data = {
                'id': transaction['id'],
                'date': transaction['date'].isoformat() if transaction['date'] else None,
                'payee': transaction['payee'],
                'amount': float(transaction['amount']),
                'notes': transaction['notes'] or '',
                'categoryID': transaction['categoryID'],
                'category': transaction['categoryName'] or 'Uncategorized',
                'expenseType': transaction['expenseType']
            }
            transactions_data.append(transaction_data)

        cursor.close()
        dbConnection.close()

        return jsonify(transactions_data)

    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    try:
        print("=== ADD TRANSACTION REQUEST ===")
        print(f"Session user_id: {session.get('user_id')}")
        print(f"Request data: {request.get_json()}")

        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        userID = session['user_id']

        if not data.get('payee') or not data.get('amount'):
            return jsonify({'error': 'Payee and amount are required'}), 400

        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        categoryID = int(data.get('categoryID', 1))
        cursor.execute('SELECT idbankCategory FROM bankCategory WHERE idbankCategory = %s', (categoryID,))
        category = cursor.fetchone()

        if not category:
            cursor.close()
            dbConnection.close()
            return jsonify({'error': f'Category ID {data.get("categoryID")} does not exist'}), 400
        
        cursor.close()
        dbConnection.close()
        
        # Create new transaction
        newTransaction = Transaction(
            transactionID=0,
            userID=userID,
            total=float(data['amount']),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            payee=data['payee'],
            categoryID=int(data.get('categoryID', 1)),
            notes=data.get('notes', ''),
            isRecurring=False,
            expenseType=ExpenseType.VARIABLE
        )

        dbConnection = get_db_connection()
        success = newTransaction.add_transaction(dbConnection)
        
        if success:
            try:
                budgetManager.record_transaction(newTransaction)
            except Exception as budget_error:
                print(f"Budget tracking error (non-critical): {budget_error}")
            
            dbConnection.close()
            return jsonify({
                'message': 'Transaction added successfully', 
                'id': newTransaction.transactionID,
                'transaction': {
                    'id': newTransaction.transactionID,
                    'payee': newTransaction.payee,
                    'amount': newTransaction.total,
                    'date': newTransaction.date.isoformat(),
                    'categoryID': newTransaction.categoryID,
                    'notes': newTransaction.notes
                }
            })
        else:
            dbConnection.close()
            return jsonify({'error': 'Failed to add transaction to database'}), 500
            
    except Exception as e:
        print(f"Error adding transaction: {e}")
        if 'dbConnection' in locals():
            dbConnection.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/budgets', methods=['GET'])
def get_budgets():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        dbConnection = get_db_connection()
        budgets = Budget.get_user_budgets(dbConnection, session['user_id'])
        dbConnection.close()

        budgetsData = []
        for budget in budgets:
            budgetData = budget.get_budget_data()

            for category in budgetData['categories']:
                category['spent'] = 0.0                 #Placeholder

            budgetsData.append(budgetData)

        return jsonify(budgetsData)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budgets', methods=['POST'])
def create_budget():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        print(f"Creating budget with data: {data}")

        monthStr = data['month']
        try:
            if ' ' in monthStr:
                monthDate = datetime.strptime(monthStr, '%B %Y').date().replace(day=1)
            else:
                monthDate = datetime.now().date().replace(day=1)
        except ValueError:
            monthDate = datetime.now().date().replace(day=1)

        totalPlanned = data.get('totalPlannedAmnt')
        if totalPlanned is None:
            categoriesData = data.get('categories', [])
            totalPlanned = sum(cat.get('plannedAmnt', 0) for cat in categoriesData)

        newBudget = Budget(
            budgetID=0,
            userID=session['user_id'],
            name=data['name'],
            totalPlannedAmnt=float(data['totalPlannedAmnt']),
            month=monthDate,
            income=float(data.get('income', 0))
        )

        categoriesData = data.get('categories', [])
        for catData in categoriesData:
            plannedAmnt = catData.get('plannedAmnt')
            categoryLimit = catData.get('categoryLimit', plannedAmnt)
            plannedPercentage = catData.get('plannedPercentage')

            category = Category(
                categoryID=0,
                name=catData['name'],
                type_=catData.get('type', 'Expense'),
                categoryLimit=float(categoryLimit) if categoryLimit is not None else 0.0,
                plannedAmnt=float(plannedAmnt) if plannedAmnt is not None else 0.0,
                plannedPercentage=float(plannedPercentage) if plannedPercentage is not None else None
            )
            newBudget.addCategory(category)

        dbConnection = get_db_connection()
        success = newBudget.createBudget(dbConnection)
        dbConnection.close()

        if success:
            return jsonify({
                'message': 'Budget created successfully',
                'budgetID': newBudget.budgetID
            })
        else:
            return jsonify({'error': 'Failed to create budget'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/budgets/<int:budget_id>', methods=['PUT'])
def update_budget(budgetID):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()

        dbConnection = get_db_connection()
        budget = Budget.get_budget_by_id(dbConnection, budgetID)

        if not budget:
            dbConnection.close()
            return jsonify({'error': 'Budget not found'}), 404
        
        if budget.userID != session['user_id']:
            dbConnection.close()
            return jsonify({'error': 'Unauthorized'}), 403
        
        budget.editBudget(
            dbConnection,
            name=data.get('name'),
            totalPlannedAmnt=data.get('totalPlannedAmnt'),
            month=data.get('month'),
            income=data.get('income')
        )

        dbConnection.close()
        return jsonify({'message': 'Budget updated successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
def delete_budget(budgetID):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        dbConnection = get_db_connection()
        budget = Budget.get_budget_by_id(dbConnection, budgetID)

        if not budget:
            dbConnection.close()
            return jsonify({'error': 'Budget not found'}), 404
        
        if budget.userID != session['user_id']:
            dbConnection.close()
            return jsonify({'error': 'Unauthorized'}), 403
        
        success = budget.deleteBudget(dbConnection)
        dbConnection.close()

        if success:
            return jsonify({'message': 'Budget deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete budget'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/profile', methods=['GET'])
def get_profile():
    return get_user_profile()

@app.route('/api/spending-chart', methods=['GET'])
def get_spending_chart():
    try:
        chartData = chartManager.get_all_chart_data(sampleBudget) #Fix this for full implementation
        return jsonify(chartData)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expense-stats', methods=['GET'])
def get_expense_stats():
    try:
        stats = transactionManager.get_expense_type_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/incomes', methods=['GET'])
def get_incomes():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        dbConnection = get_db_connection()
        incomes = Income.get_user_incomes(dbConnection, session['user_id'])
        dbConnection.close()

        totalMonthly = 0.0
        incomesData = []
        
        for income in incomes:
            amount = income.amount
            payFrequency = income.payFrequency.lower()

            if payFrequency == 'weekly' or payFrequency == '1 week':
                monthly_amount = amount * 4
            elif payFrequency == 'bi-weekly' or payFrequency == 'biweekly' or payFrequency == '2 weeks':
                monthly_amount = amount * 2
            elif payFrequency == 'monthly' or payFrequency == '1 month':
                monthly_amount = amount
            elif payFrequency == 'annual' or payFrequency == 'yearly':
                monthly_amount = amount / 12
            else:
                monthly_amount = amount  # fallback for one-time or custom
            
            totalMonthly += monthly_amount

            datePaid = income.datePaid
            if hasattr(datePaid, 'isoformat'):
                datePaidStr = datePaid.isoformat()
            else:
                datePaidStr = str(datePaid)

            nextPayday = None
            if income.isActive:
                try:
                    nextPaydayObj = income.calc_next_payday()
                    if nextPaydayObj and hasattr(nextPaydayObj, 'isoformat'):
                        nextPayday = nextPaydayObj.isoformat()
                    else:
                        nextPayday = None
                except Exception as e:
                    print(f"Error calculating next payday for income {income.incomeID}: {e}")
                    nextPayday = None

            income_data = {
                'incomeID': income.incomeID,
                'name': income.name,
                'amount': float(income.amount),
                'payFrequency': income.payFrequency,
                'datePaid': datePaidStr,
                'isActive': income.isActive,
                'nextPayday': nextPayday
            }
            incomesData.append(income_data)

        return jsonify({
            'success': True,
            'incomes': incomesData,
            'totalMonthlyIncome': round(totalMonthly, 2)
        })
    except Exception as e:
        print(f"Error in get_incomes: {e}")
        return jsonify({
            'success': False,
            'message': f'Error fetching incomes: {str(e)}'
        }), 500
    
@app.route('/api/incomes', methods=['POST'])
def add_income():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False, 
                'message': 'Not authenticated'
            }), 401
        
        data = request.get_json()

        requiredFields = ['name', 'amount', 'payFrequency', 'datePaid']
        for field in requiredFields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        try:
            datePaid = datetime.strptime(data['datePaid'], '%Y-%m-%d').date()
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': f'Invalid date format for datePaid. Expected YYYY-MM-DD.'
            }), 400
            
        newIncome = Income(
            incomeID= 0,
            userID=session['user_id'],
            name= data['name'],
            amount=float(data['amount']),
            payFrequency=data['payFrequency'],
            datePaid=datePaid,
            isActive=True,
            customDays=data.get('customDays')
        )

        dbConnection = get_db_connection()
        success = newIncome.add_income(dbConnection)

        if success:
            incomes = Income.get_user_incomes(dbConnection, session['user_id'])
            totalMonthly = 0.0
            for income in incomes:
                amount = income.amount
                payFrequency = income.payFrequency.lower()

                if payFrequency == 'weekly' or payFrequency == '1 week':
                    totalMonthly += amount * 4
                elif payFrequency == 'bi-weekly' or payFrequency == 'biweekly' or payFrequency == '2 weeks':
                    totalMonthly += amount * 2
                elif payFrequency == 'monthly' or payFrequency == '1 month':
                    totalMonthly += amount
                elif payFrequency == 'annual' or payFrequency == 'yearly':
                    totalMonthly += amount / 12
            dbConnection.close()


            datePaidResponse = newIncome.datePaid
            if hasattr(datePaidResponse, 'isoformat'):
                datePaidStr = datePaidResponse.isoformat()
            else:
                datePaidStr = str(datePaidResponse)

            nextPayday = None
            if newIncome.isActive:
                try:
                    nextPaydayObj = newIncome.calc_next_payday()
                    if nextPaydayObj and hasattr(nextPaydayObj, 'isoformat'):
                        nextPayday = nextPaydayObj.isoformat()
                    else:
                        nextPayday = None
                except Exception as e:
                    print(f"Error calculating next payday: {e}")
                    nextPayday = None
            
            dbConnection.close()

            return jsonify({
                'success': True,
                'message': 'Income source added successfully',
                'income': {
                    'incomeID': newIncome.incomeID,
                    'name': newIncome.name,
                    'amount': newIncome.amount,
                    'payFrequency': newIncome.payFrequency,
                    'datePaid': newIncome.datePaid.isoformat(),
                    'isActive': newIncome.isActive,
                    'nextPayday': nextPayday
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to add income to database'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error adding income: {str(e)}"
        }), 500
    
@app.route('/api/incomes/<int:income_id>', methods=['PUT'])
def update_income(income_id):
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        data = request.get_json()

        dbConnection = get_db_connection()
        income = Income.get_income_by_id(dbConnection, income_id)

        if not income:
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'Income not found'
            }), 404
        
        if income.userID != session['user_id']:
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'Unauthorized to update this income'
            }), 403
        
        oldAmount = income.amount
        oldFrequency = income.payFrequency

        datePaid = None
        if data.get('datePaid'):
            try:
                datePaid = datetime.strptime(data['datePaid'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format for datePaid. Expected YYYY-MM-DD'
                }), 400
        
        income.update_income(
            dbConnection,
            name=data.get('name'),
            amount=data.get('amount'),
            payFrequency=data.get('payFrequency'),
            datePaid=datePaid,
            customDays=data.get('customDays')
        )

        if data.get('amount') and float(data['amount']) != oldAmount:
            income.apply_income_to_budgets(dbConnection)

        dbConnection.close()

        return jsonify({
            'success': True,
            'message': 'Income source updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating income: {str(e)}'
        }), 500
    
@app.route('/api/incomes/<int:income_id>', methods=['DELETE'])
def delete_income(income_id):
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        dbConnection = get_db_connection()
        income = Income.get_income_by_id(dbConnection, income_id)

        if not income:
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'Income not found'
            }), 404
        
        if income.userID != session['user_id']:
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'Unauthorized to delete this income'
            }), 403
        
        success = income.delete_income(dbConnection)
        dbConnection.close()

        if success:
            return jsonify({
                'success': True,
                'message': 'Income source deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to delete income'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleteing income: {str(e)}'
        }), 500

@app.route('/api/incomes/calculate-monthly', methods=['POST'])
def calc_monthly_income():
    try:
        data = request.get_json()
        incomes = data.get('incomes', [])

        totalMonthly = 0.0

        for income in incomes:
            amount = income['amount']
            payFrequency = income['payFrequency'].lower()

            if payFrequency == 'weekly':
                totalMonthly += amount * 4
            elif payFrequency == 'bi-weekly' or payFrequency == 'biweekly':
                totalMonthly += amount * 2
            elif payFrequency == 'monthly':
                totalMonthly += amount
            elif payFrequency == 'annual':
                totalMonthly += amount / 12

        return jsonify({
            'success': True,
            'totalMonthlyIncome': totalMonthly
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error calculating monthly income: {str(e)}'
        }), 500
    
@app.route('/api/account-settings', methods=['GET'])
def get_account_settings():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        cursor.execute("SELECT idbankUser, first_name, last_name, email, phone_number, dateCreated, is_Verified FROM bankUser WHERE idbankUser = %s",
                       (session['user_id'],)
        )
        userData = cursor.fetchone()
        
        cursor.close()
        dbConnection.close()

        if userData:
            return jsonify({
                'success': True,
                'user': {
                    'userID': userData['idbankUser'],
                    'fname': userData['first_name'],
                    'lname': userData['last_name'],
                    'email': userData['email'],
                    'phoneNumber': userData['phone_number'],
                    'dateCreated': userData['dateCreated'].isoformat() if userData['dateCreated'] else None,
                    'isVerified': bool(userData['is_Verified'])
                },
                #PLACEHOLDER
                'notificationSettings': {
                    'emailNotifs': True,
                    'smsNotifs': False,
                    'pushNotifs': True,
                    'twoFactor': False
                }
            }), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching account settings: {str(e)}'
        }), 500

@app.route('/api/account-settings', methods=['PUT'])
def update_account_settings():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        data = request.get_json()

        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        cursor.execute("SELECT idbankUser, first_name, last_name, email, phone_number FROM bankUser WHERE idbankUser = %s",
                       (session['user_id'],)
        )
        currentUser = cursor.fetchone()

        if not currentUser:
            cursor.close()
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        updates = {}
        updateFields = []
        values = []

        if 'legalName' in data and data['legalName']:
            nameParts = data['legalName'].strip().split(' ', 1)
            if len(nameParts) >= 2:
                updates['first_name'] = nameParts[0]
                updates['last_name'] = nameParts[1]
            else:
                updates['first_name'] = nameParts[0]

        #PLACEHOLDER
        if 'preferredName' in data:
            pass

        if 'phone' in data:
            updates['phone_number'] = data['phone']

        if 'accountEmail' in data and data['accountEmail']:
            updates['email'] = data['accountEmail']

        for field, value in updates.items():
            updateFields.append(f"{field} = %s")
            values.append(value)

        if updateFields:
            values.append(session['user_id'])
            setClause = ", ".join(updateFields) 
            cursor.execute(f"UPDATE bankUser SET {setClause} WHERE idbankUser = %s", values)
            dbConnection.commit()

            if 'email' in updates:
                session['user_email'] = updates['email']

        notificationUpdates = {}
        if 'emailNotifs' in data:
            notificationUpdates['email_notifications'] = data['emailNotifs']
        if 'smsNotifs' in data:
            notificationUpdates['sms_notifications'] = data['smsNotifs']
        if 'pushNotifs' in data:
            notificationUpdates['push_notifications'] = data['pushNotifs']
        if 'twoFactor' in data:
            notificationUpdates['two_factor_auth'] = data['twoFactor']
        
        if notificationUpdates:
            try:

                cursor.execute("""
                    INSERT INTO bankUserNotificationSetting 
                    (userID, email_notifications, sms_notifications, push_notifications, two_factor_auth) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    email_notifications = VALUES(email_notifications),
                    sms_notifications = VALUES(sms_notifications),
                    push_notifications = VALUES(push_notifications),
                    two_factor_auth = VALUES(two_factor_auth)
                """, (
                    session['user_id'],
                    notificationUpdates.get('email_notifications', True),
                    notificationUpdates.get('sms_notifications', False),
                    notificationUpdates.get('push_notifications', True),
                    notificationUpdates.get('two_factor_auth', False)
                ))
                dbConnection.commit()
            except Exception as e:
                print(f"Notificaiton error: {e}")

        cursor.close()
        dbConnection.close()

        return jsonify({
            'success': True,
            'message': 'Account settings updated successfully',
            'updates': {
                'profile': updates,
                'notifications': notificationUpdates,
            }
        }), 200
    except mysql.connector.Error as err:
        dbConnection.rollback()
        cursor.close()
        dbConnection.close()
        if err.errno == 1062:
            return jsonify({
                'success': False,
                'message': f'Database error: {str(err)}'
            }), 500
    except Exception as e:
        if 'dbConnection' in locals():
            dbConnection.rollback()
            cursor.close()
            dbConnection.close()
        return jsonify({
            'success': False,
            'message': f'Error updating account settings: {str(e)}'
        }), 500
    
@app.route('/api/change-password', methods=['POST'])
def change_password():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        data = request.get_json()
        currentPassword = data.get('currentPassword')
        newPassword = data.get('newPassword')
        confirmPassword = data.get('confirmPassword')

        if not currentPassword or not newPassword or not confirmPassword:
            return jsonify({
                'success': False,
                'message': 'All password fields are required'
            }), 400
        
        if newPassword != confirmPassword:
            return jsonify({
                'success': False,
                'message': 'New passwords do not match'
            }), 400
        
        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        cursor.execute("SELECT password_hash FROM bankUser WHERE idbankUser = %s", (session['user_id'],))
        userData = cursor.fetchone()

        if not userData:
            cursor.close()
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        if not User.verify_password(currentPassword, userData['password_hash']):
            cursor.close()
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 400
        
        strongPass, msg = User.validate_strong_password(newPassword)
        if not strongPass:
            cursor.close()
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': msg
            }), 400
        
        newHashedPassword = User.hash_password(newPassword)
        if not newHashedPassword:
            cursor.close()
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'Error hashing new password'
            }), 500
        
        cursor.execute("UPDATE bankUser SET password_hash = %s WHERE idbankUser = %s",
                       (newHashedPassword, session['user_id'])
        )
        dbConnection.commit()

        cursor.close()
        dbConnection.close()
        
        return jsonify({
            'success': True,
            'message': 'Password updated successfully'
        }), 200
    
    except Exception as e:
        if 'dbConnection' in locals():
            dbConnection.rollback()
            cursor.close()
            dbConnection.close()

        return jsonify({
            'success': False,
            'message': f'Error changing password: {str(e)}'
        }), 500

@app.route('/api/notification-settings', methods=['GET'])
def get_notification_settings():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        notificationSettings = NotificationSettings(session['user_id'], db)
        summary = notificationSettings.get_settings_summary()
        
        return jsonify({
            'success': True,
            'settings': summary
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching notification settings: {str(e)}'
        }), 500

@app.route('/api/notification-settings', methods=['PUT'])
def update_notification_settings():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        data = request.get_json()
        notificationSettings = NotificationSettings(session['user_id'], db)
        
        if 'category_updates' in data:
            for categoryName, channels in data['category_updates'].items():
                try:
                    category = NotificationCategory(categoryName)
                    channelDict = {}
                    
                    for channelName, enabled in channels.items():
                        channel = NotificationChannel(channelName)
                        channelDict[channel] = enabled
                    
                    success = notificationSettings.notification_manager.update_category_channels(category, channelDict)
                    if not success:
                        return jsonify({
                            'success': False,
                            'message': f'Failed to update {categoryName} settings'
                        }), 400
                        
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': f'Invalid category or channel: {categoryName}'
                    }), 400
        
        return jsonify({
            'success': True,
            'message': 'Notification settings updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating notification settings: {str(e)}'
        }), 500

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        limit = request.args.get('limit', 50, type=int)
        unreadOnly = request.args.get('unread_only', 'false').lower() == 'true'
        
        notificationManager = NotificationManager(session['user_id'], db)
        notifications = notificationManager.get_user_notifications(limit, unreadOnly)
        
        return jsonify({
            'success': True,
            'notifications': notifications
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching notifications: {str(e)}'
        }), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notificationID):
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        notificationManager = NotificationManager(session['user_id'], db)
        success = notificationManager.mark_notification_as_read(notificationID)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to mark notification as read'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error marking notification as read: {str(e)}'
        }), 500

@app.route('/api/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        notificationManager = NotificationManager(session['user_id'], db)
        success = notificationManager.mark_all_notifications_as_read()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'All notifications marked as read'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to mark notifications as read'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error marking notifications as read: {str(e)}'
        }), 500

@app.route('/api/notifications/test', methods=['POST'])
def send_test_notification():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        data = request.get_json()
        categoryName = data.get('category', 'transaction_alerts')
        message = data.get('message', 'Test notification')
        
        notificationSettings = NotificationSettings(session['user_id'], db)
        success = notificationSettings.send_test_notification(categoryName, message)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Test notification sent'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send test notification - category may be disabled'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error sending test notification: {str(e)}'
        }), 500
    
@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        budgetID = request.args.get('budgetId', type=int)
        
        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        if budgetID:
            cursor.execute("""SELECT c.idbankCategory, c.name, c.type FROM bankCategory c WHERE c.budgetID = %s""", (budgetID,))
        else:
            cursor.execute("""SELECT c.idbankCategory, c.name, c.type FROM bankCategory c JOIN bankBudget b ON c.budgetID = b.idbankBudget WHERE b.userID = %s LIMIT 10""", (session['user_id'],))

        categories = cursor.fetchall()
        cursor.close()
        dbConnection.close()

        return jsonify({
            'categories': categories,
            'budgetId': budgetID
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-verification', methods=['POST'])
def send_verification():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400
        
        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        cursor.execute("SELECT idbankUser, is_Verified FROM bankUser WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        if user['is_Verified']:
            cursor.close()
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'Account is already verified'
            }), 400
        
        verificationToken = secrets.token_hex(32)
        tokenExpiry = datetime.now() + timedelta(hours=24)

        cursor.execute("UPDATE bankUser SET verification_token = %s, token_expiry = %s WHERE email = %s", (verificationToken, tokenExpiry, email))
        dbConnection.commit()

        emailSent = send_verification_email(email, verificationToken)

        cursor.close()
        dbConnection.close()

        if emailSent:
            return jsonify({
                'success': True,
                'message': 'Verification email sent successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send verification email'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error sending verification: {str(e)}'
        }), 500
    
@app.route('/api/verify-email', methods=['POST'])
def verify_email():
    try:
        data = request.get_json()
        token = data.get('token')

        if not token:
            return jsonify({
                'success': False,
                'message': 'Verification token is required'
            }), 400
        
        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        cursor.execute("SELECT idbankUser, token_expiry FROM bankUser WHERE verification_token = %s", (token,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'Invalid verification token'
            }), 400
        
        if user['token_expiry'] and user['token_expiry'] < datetime.now():
            cursor.close()
            dbConnection.close()
            return jsonify({
                'success': False,
                'message': 'Verification token has expired'
            }), 400
        
        cursor.execute("UPDATE bankUser SET is_Verified = 1, verification_token = NULL, token_expiry = NULL WHERE idbankUser = %s", (user['idbankUser'],))
        dbConnection.commit()

        cursor.close()
        dbConnection.close()

        return jsonify({
            'success': True,
            'message': 'Email verified successfully! You can log in.'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error verifying email: {str(e)}'
        }), 500

@app.route('/api/check-verification', methods=['GET'])
def check_verification():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        cursor.execute("SELECT is_Verified FROM bankUser WHERE idbankUser = %s", (session['user_id'],))
        user = cursor.fetchone()

        cursor.close()
        dbConnection.close()

        if user:
            return jsonify({
                'success': True,
                'isVerified': bool(user['is_Verified'])
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error checking verification: {str(e)}'
        }), 500
    
@app.route('/api/transactions/all', methods=['GET'])
def get_all_transactions():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        userID = session['user_id']
        
        sortBy = request.args.get('sort', 'date-desc')
        categoryFilter = request.args.get('category', 'all')
        limit = request.args.get('limit', 100, type=int)
        
        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        query = """
            SELECT 
                t.idbankTransaction as id,
                t.date,
                t.payee,
                t.amount,
                t.notes,
                t.categoryID,
                c.name as categoryName,
                t.expenseType
            FROM bankTransaction t
            LEFT JOIN bankCategory c ON t.categoryID = c.idbankCategory
            WHERE t.userID = %s
        """
        params = [userID]

        if categoryFilter != 'all':
            query += " AND c.name = %s"
            params.append(categoryFilter)

        if sortBy == 'date-desc':
            query += " ORDER BY t.date DESC"
        elif sortBy == 'date-asc':
            query += " ORDER BY t.date ASC"
        elif sortBy == 'amount-desc':
            query += " ORDER BY t.amount DESC"
        elif sortBy == 'amount-asc':
            query += " ORDER BY t.amount ASC"
        elif sortBy == 'payee':
            query += " ORDER BY t.payee ASC"
        elif sortBy == 'category':
            query += " ORDER BY c.name ASC"

        query += " LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        transactions = cursor.fetchall()

        transactions_data = []
        for transaction in transactions:
            transaction_data = {
                'id': transaction['id'],
                'date': transaction['date'].isoformat() if transaction['date'] else None,
                'payee': transaction['payee'],
                'amount': float(transaction['amount']),
                'notes': transaction['notes'] or '',
                'categoryID': transaction['categoryID'],
                'category': transaction['categoryName'] or 'Uncategorized',
                'expenseType': transaction['expenseType']
            }
            transactions_data.append(transaction_data)

        cursor.close()
        dbConnection.close()

        return jsonify(transactions_data)

    except Exception as e:
        print(f"Error fetching all transactions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        userID = session['user_id']

        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        cursor.execute("SELECT idbankTransaction FROM bankTransaction WHERE idbankTransaction = %s AND userID = %s", 
                      (transaction_id, userID))
        transaction = cursor.fetchone()

        if not transaction:
            cursor.close()
            dbConnection.close()
            return jsonify({'error': 'Transaction not found or unauthorized'}), 404

        updateFields = []
        params = []

        if 'payee' in data:
            updateFields.append("payee = %s")
            params.append(data['payee'])
        if 'amount' in data:
            updateFields.append("amount = %s")
            params.append(float(data['amount']))
        if 'date' in data:
            updateFields.append("date = %s")
            params.append(data['date'])
        if 'notes' in data:
            updateFields.append("notes = %s")
            params.append(data['notes'])
        if 'categoryID' in data:
            updateFields.append("categoryID = %s")
            params.append(int(data['categoryID']))

        if not updateFields:
            cursor.close()
            dbConnection.close()
            return jsonify({'error': 'No fields to update'}), 400

        params.append(transaction_id)
        params.append(userID)

        setClause = ", ".join(updateFields)
        query = f"UPDATE bankTransaction SET {setClause} WHERE idbankTransaction = %s AND userID = %s"
        
        cursor.execute(query, params)
        dbConnection.commit()

        cursor.close()
        dbConnection.close()

        return jsonify({'message': 'Transaction updated successfully'})

    except Exception as e:
        print(f"Error updating transaction: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        userID = session['user_id']

        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        cursor.execute("SELECT idbankTransaction FROM bankTransaction WHERE idbankTransaction = %s AND userID = %s", 
                      (transaction_id, userID))
        transaction = cursor.fetchone()

        if not transaction:
            cursor.close()
            dbConnection.close()
            return jsonify({'error': 'Transaction not found or unauthorized'}), 404

        cursor.execute("DELETE FROM bankTransaction WHERE idbankTransaction = %s AND userID = %s", 
                      (transaction_id, userID))
        dbConnection.commit()

        cursor.close()
        dbConnection.close()

        return jsonify({'message': 'Transaction deleted successfully'})

    except Exception as e:
        print(f"Error deleting transaction: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/all', methods=['GET'])
def get_all_categories():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        dbConnection = get_db_connection()
        cursor = get_db_cursor(dbConnection)

        cursor.execute("""
            SELECT DISTINCT c.name 
            FROM bankCategory c 
            JOIN bankBudget b ON c.budgetID = b.idbankBudget 
            WHERE b.userID = %s 
            ORDER BY c.name
        """, (session['user_id'],))

        categories = cursor.fetchall()
        categoryNames = [category['name'] for category in categories]

        cursor.close()
        dbConnection.close()

        return jsonify({'categories': categoryNames})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)