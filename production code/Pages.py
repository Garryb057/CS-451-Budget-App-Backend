from datetime import date
from typing import List, Dict
from Money import Transaction, TransactionManager
from chart import *

class Dashboard:
    def __init__ (self, userID, transactionManager: TransactionManager):
       self.userID = userID
       self.transactionManager = transactionManager

    #getters
    def get_userID (self):
        return self.userID
    
    #setters
    def set_userID (self):
        return self.userID
    
    def get_monthly_summary(self, month: date) -> bool:
        #Future Implementation
        return True
    def get_recent_transaction(self, limit: int = 10) -> List[Transaction]:
        return self.transactionManager.get_recent_transactions(self.userID, limit)
    def get_recent_transactions_widget_data(self, limit: int = 10) -> List[dict]:
        recentTransactions = self.get_recent_transaction(limit)
        widgetData = []

        for transaction in recentTransactions:
           widgetData.append({
               'transactionID': transaction.transactionID,
               'date': transaction.date,
               'payee': transaction.payee,
               'amount': transaction.total,
               'category': transaction.categoryID
           })
        return widgetData

    def get_category_progress(self) -> bool:
        #Future Implementation
        return True
    def get_financial_charts(self, budget) -> Dict:
        chart_data = self.chartManager.get_all_chart_data(budget)
        chart_data['hover_enabled'] = True
        chart_data['tooltip_features'] = {
            'show_on_hover': True,
            'hide_on_leave': True,
            'show_delay': 100,
            'hide_delay': 300
        }
        return chart_data

    def handle_chart_hover(self, hover_data: Dict, budget: Budget) -> Dict[str, Any]:
        try:
            chart_type = hover_data.get('chart_type')
            element_index = hover_data.get('element_index', -1)
            element_data = hover_data.get('element_data', {})
            position = hover_data.get('position', {'x': 0, 'y': 0})
            action = hover_data.get('action', 'hover')
            
            if action == 'enter' and element_index >= 0:
                result = self.chartManager.handle_chart_hover(
                    chart_type, element_index, element_data, budget, position
                )
                self.active_tooltip = result.get('tooltip')
                return result
                
            elif action == 'leave':
                self.active_tooltip = None
                return {
                    'action': 'hide_tooltip',
                    'tooltip': {'visible': False}
                }
                
            elif action == 'move' and self.active_tooltip:
                self.active_tooltip['position'] = position
                return {
                    'action': 'update_tooltip',
                    'tooltip': self.active_tooltip
                }
                
        except Exception as e:
            print(f"Error handling chart hover: {e}")
            return {'error': str(e)}
        
        return {'action': 'no_action'}

    def update_chart_view(self, chart_type: str, budget) -> Dict:
        self.current_chart_view = chart_type
        
        if chart_type == 'overview':
            return self.chartManager.get_all_chart_data(budget)
        elif chart_type == 'income_vs_expenses':
            return {
                'chart_type': 'income_vs_expenses',
                'data': self.chartManager.get_income_vs_expenses_data(budget),
                'config': self.chartManager.get_interactive_chart_config(ChartType.PIE),
                'hover_support': True
            }
        elif chart_type == 'category_breakdown':
            return {
                'chart_type': 'category_breakdown',
                'data': self.chartManager.get_category_breakdown_data(budget),
                'config': self.chartManager.get_interactive_chart_config(ChartType.DONUT),
                'hover_support': True
            }
        elif chart_type == 'spending_trend':
            return {
                'chart_type': 'spending_trend',
                'data': self.chartManager.get_spending_trend_data(),
                'config': self.chartManager.get_interactive_chart_config(ChartType.LINE),
                'hover_support': True
            }
        elif chart_type == 'budget_comparison':
            return {
                'chart_type': 'budget_comparison',
                'data': self.chartManager.get_actual_vs_planned_data(budget),
                'config': self.chartManager.get_interactive_chart_config(ChartType.BAR),
                'hover_support': True
            }

    def handle_chart_interaction(self, interaction_data: Dict, budget) -> Dict:
        chart_type = interaction_data.get('chart_type')
        element_index = interaction_data.get('element_index')
        action = interaction_data.get('action', 'click')
        
        if action == 'click':
            return self.chartManager.handle_chart_interaction(chart_type, element_index, budget, 'click')
        elif action == 'hover':
            return self.handle_chart_hover(interaction_data, budget)
        
        return {'error': 'Unknown interaction'}

    def refresh_chart_data(self, budget) -> Dict:
        print("Refreshing chart data due to data changes...")
        return self.get_financial_charts(budget)

    def set_chart_preferences(self, preferences: Dict) -> bool:
        try:
            self.chartManager.update_chart_preferences(preferences)
            return True
        except Exception as e:
            print(f"Error updating chart preferences: {e}")
            return False

    def get_chart_data(self) -> Dict:
        return {
            'has_chart_data': True,
            'chart_types_available': [
                'income_vs_expenses',
                'category_breakdown', 
                'spending_trend',
                'budget_comparison',
                'expense_type_breakdown'
            ],
            'hover_tooltips_enabled': True
        }
    
 #==Part of sprint 4 by Temka, for later debugging==
    def get_spending_chart_data(self, view_type: str = 'monthly', 
                            year: int = None, month: int = None) -> dict:
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        #This would integrate with TransactionManager
        #For now, returning structure
        return {
            'view_type': view_type,
            'year': year,
            'month': month if view_type == 'monthly' else None,
            'data': {}  #Would be populated by TransactionManager
        }

    def switch_chart_view(self, view_type: str, year: int = None, 
                        month: int = None) -> dict:
        if view_type not in ['monthly', 'yearly']:
            raise ValueError("view_type must be 'monthly' or 'yearly'")
        
        chart_data = self.get_spending_chart_data(view_type, year, month)
        
        # Store user preference (Future implementation: save to database)
        print(f"Chart view switched to {view_type}")
        
        return chart_data

    def get_category_drill_down(self, categoryID: int, period_start: date, 
                            period_end: date) -> dict:
        # This would integrate with TransactionManager
        return {
            'categoryID': categoryID,
            'period_start': period_start,
            'period_end': period_end,
            'transactions': []  # Would be populated by TransactionManager
        }

    def persist_chart_preference(self, view_type: str) -> bool:
        # Future implementation: save to database
        print(f"Chart preference '{view_type}' saved for user {self.userID}")
        return True

    def get_user_chart_preference(self) -> str:
        # Future implementation: retrieve from database
        # Default to monthly
        return 'monthly'
 #==End of Part of sprint 4 by Temka, for later debugging==


    #==Part of sprint 5 by Temka, for later debugging==
    def get_budget_detail_page_data(self, budget: 'Budget', start_date: date, end_date: date) -> dict:

        spending_data = self.transactionManager.get_spending_by_category_period(start_date, end_date)
        
        comparison = budget.get_full_budget_comparison(spending_data)
        
        health = budget.get_budget_health_summary(spending_data)
        
        return {
            'budget_info': {
                'budgetID': budget.budgetID,
                'name': budget.name,
                'month': budget.month,
                'income': budget.income
            },
            'comparison': comparison,
            'health_summary': health,
            'period': {
                'start': start_date,
                'end': end_date
            }
        }
    #==End of Part of sprint 5 by Temka, for later debugging==