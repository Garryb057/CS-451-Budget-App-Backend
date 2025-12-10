from typing import Dict, List, Optional, Tuple, Any
from datetime import date, datetime, timedelta
from enum import Enum
from budget import *
from Money import *
import json

class ChartType(Enum):
    PIE = "pie"
    BAR = "bar"
    LINE = "line"
    DONUT = "donut"

class ChartTheme(Enum):
    LIGHT = "light"
    DARK = "dark"
    COLORFUL = "colorful"

class TooltipManager:
    def __init__(self):
        self.activeTooltip = None
        self.tooltipTimeout = None
    
    def create_tooltip_data(self, chartType: str, elementIndex: int, elementData: Dict, budget: Budget) -> Dict[str, Any]:
        tooltip_data = {
            'chart_type': chartType,
            'element_index': elementIndex,
            'visible': True,
            'position': {'x': 0, 'y': 0},  # Will be set by frontend
            'content': {}
        }
        
        if chartType == 'category_breakdown':
            return self.get_category_tooltip(elementIndex, elementData, budget)
        elif chartType == 'income_vs_expenses':
            return self.get_income_expenses_tooltip(elementIndex, elementData, budget)
        elif chartType == 'actual_vs_planned':
            return self.get_budget_comparison_tooltip(elementIndex, elementData, budget)
        elif chartType == 'expense_type_breakdown':
            return self.get_expense_type_tooltip(elementIndex, elementData)
        elif chartType == 'spending_trend':
            return self.get_trend_tooltip(elementIndex, elementData)
        
        return tooltip_data
    
    def get_category_tooltip(self, elementIndex: int, elementData: Dict, budget: Budget) -> Dict[str, Any]:
        if elementIndex < len(budget.categories):
            category = budget.categories[elementIndex]
            totalBudget = sum(cat.plannedAmnt for cat in budget.categories)
            percentage = (category.plannedAmnt / totalBudget * 100) if totalBudget > 0 else 0
            
            return {
                'title': category.name,
                'amount': f"${category.plannedAmnt:.2f}",
                'percentage': f"{percentage:.1f}%",
                'type': category.type,
                'details': f"Planned amount: ${category.plannedAmnt:.2f}",
                'color': elementData.get('color', '#cccccc')
            }
        return {'error': 'Category not found'}
    
    def get_income_expenses_tooltip(self, elementIndex: int, elementData: Dict, budget: Budget) -> Dict[str, Any]:
        totalIncome = budget.income
        totalExpenses = sum(cat.plannedAmnt for cat in budget.categories)
        remaining = max(0, totalIncome - totalExpenses)
        
        elements = [
            {
                'title': 'Total Income',
                'amount': f"${totalIncome:.2f}",
                'details': 'Your total monthly income',
                'color': '#4CAF50'
            },
            {
                'title': 'Total Expenses',
                'amount': f"${totalExpenses:.2f}",
                'details': 'Your planned monthly expenses',
                'color': '#F44336'
            },
            {
                'title': 'Remaining Balance',
                'amount': f"${remaining:.2f}",
                'details': 'Income minus expenses',
                'color': '#2196F3'
            }
        ]
        
        if elementIndex < len(elements):
            return elements[elementIndex]
        return {'error': 'Element not found'}
    
    def get_budget_comparison_tooltip(self, elementIndex: int, elementData: Dict, budget: Budget) -> Dict[str, Any]:
        if elementIndex < len(budget.categories):
            category = budget.categories[elementIndex]
            
            return {
                'title': category.name,
                'planned': f"${category.plannedAmnt:.2f}",
                'actual': f"${category.plannedAmnt * 0.8:.2f}",  # Placeholder
                'variance': f"${category.plannedAmnt * 0.2:.2f}",
                'details': f"Planned: ${category.plannedAmnt:.2f} | Used: ${category.plannedAmnt * 0.8:.2f}",
                'color': elementData.get('color', '#cccccc')
            }
        return {'error': 'Category not found'}
    
    def get_expense_type_tooltip(self, elementIndex: int, elementData: Dict) -> Dict[str, Any]:
        expense_types = [
            {
                'title': 'Fixed Expenses',
                'amount': elementData.get('fixed_amount', 0),
                'details': 'Regular, predictable expenses',
                'color': '#FF9800'
            },
            {
                'title': 'Variable Expenses',
                'amount': elementData.get('variable_amount', 0),
                'details': 'Changing, discretionary expenses',
                'color': '#9C27B0'
            }
        ]
        
        if elementIndex < len(expense_types):
            tooltip = expense_types[elementIndex]
            tooltip['amount'] = f"${tooltip['amount']:.2f}"
            return tooltip
        return {'error': 'Expense type not found'}
    
    def get_trend_tooltip(self, elementIndex: int, elementData: Dict) -> Dict[str, Any]:
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        if elementIndex < len(months):
            return {
                'title': months[elementIndex],
                'amount': f"${elementData.get('amount', 0):.2f}",
                'details': f"Total spending in {months[elementIndex]}",
                'color': '#F44336'
            }
        return {'error': 'Month not found'}
    
    def hide_tooltip(self) -> Dict[str, Any]:
        return {
            'visible': False,
            'action': 'hide'
        }

class BudgetChartManager:
    def __init__(self, budgetManager, transactionManager):
        self.budgetManager = budgetManager
        self.transactionManager = transactionManager
        self.tooltipManager = TooltipManager()
        self.chartPreferences = {
            'default_type': ChartType.PIE,
            'theme': ChartTheme.COLORFUL,
            'animate': True,
            'interactive': True,
            'tooltip_delay': 300  # ms delay before showing tooltip
        }
    
    def get_income_vs_expenses_data(self, budget: 'Budget') -> dict:
        totalIncome = budget.income
        totalExpenses = sum(cat.plannedAmnt for cat in budget.categories)
        
        return {
            'labels': ['Income', 'Expenses', 'Remaining'],
            'datasets': [{
                'data': [totalIncome, totalExpenses, max(0, totalIncome - totalExpenses)],
                'backgroundColor': ['#4CAF50', '#F44336', '#2196F3'],
                'borderColor': ['#45a049', '#d32f2f', '#1976d2'],
                'borderWidth': 2,
                'hoverBackgroundColor': ['#66BB6A', '#EF5350', '#42A5F5'],
                'hoverBorderColor': ['#4CAF50', '#F44336', '#2196F3'],
                'hoverBorderWidth': 3
            }]
        }
    
    def get_category_breakdown_data(self, budget: 'Budget') -> dict:
        categories = []
        amounts = []
        colors = self.generate_colors(len(budget.categories))
        hoverColors = [self._lighten_color(color) for color in colors]
        
        for i, category in enumerate(budget.categories):
            if category.plannedAmnt > 0:
                categories.append(category.name)
                amounts.append(category.plannedAmnt)
        
        return {
            'labels': categories,
            'datasets': [{
                'data': amounts,
                'backgroundColor': colors,
                'borderColor': [self.darken_color(color) for color in colors],
                'borderWidth': 2,
                'hoverOffset': 15,
                'hoverBackgroundColor': hoverColors,
                'hoverBorderColor': [self.darken_color(color) for color in colors],
                'hoverBorderWidth': 3
            }]
        }
    
    def get_spending_trend_data(self, months: int = 6) -> dict:
        endDate = date.today()
        startDate = endDate - timedelta(days=30*months)
        
        monthlyData = {}
        current = startDate
        
        while current <= endDate:
            monthKey = current.strftime("%Y-%m")
            monthlyData[monthKey] = {
                'income': 0.0,
                'expenses': 0.0,
                'date': current
            }

            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        transactions = self.transactionManager.get_transactions_by_date_range(
            startDate, endDate
        )
        
        for transaction in transactions:
            monthKey = transaction.date.strftime("%Y-%m")
            if monthKey in monthlyData:
                monthlyData[monthKey]['expenses'] += transaction.total
        
        sorted_months = sorted(monthlyData.keys())
        
        return {
            'labels': [month.replace('-', '/') for month in sorted_months],
            'datasets': [
                {
                    'label': 'Expenses',
                    'data': [monthlyData[month]['expenses'] for month in sorted_months],
                    'borderColor': '#F44336',
                    'backgroundColor': 'rgba(244, 67, 54, 0.1)',
                    'tension': 0.4,
                    'fill': True,
                    'pointBackgroundColor': '#F44336',
                    'pointBorderColor': '#ffffff',
                    'pointHoverBackgroundColor': '#EF5350',
                    'pointHoverBorderColor': '#ffffff',
                    'pointHoverRadius': 6,
                    'pointHitRadius': 10
                }
            ]
        }
    
    def get_actual_vs_planned_data(self, budget: 'Budget') -> dict:
        actualSpending = self.budget_manager.get_spending_by_category()
        
        categories = []
        planned = []
        actual = []
        
        for category in budget.categories:
            if category.plannedAmnt > 0:
                categories.append(category.name)
                planned.append(category.plannedAmnt)
                actual.append(actualSpending.get(category.categoryID, 0.0))
        
        return {
            'labels': categories,
            'datasets': [
                {
                    'label': 'Planned',
                    'data': planned,
                    'backgroundColor': 'rgba(54, 162, 235, 0.7)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1,
                    'hoverBackgroundColor': 'rgba(54, 162, 235, 0.9)',
                    'hoverBorderColor': 'rgba(54, 162, 235, 1)'
                },
                {
                    'label': 'Actual',
                    'data': actual,
                    'backgroundColor': 'rgba(255, 99, 132, 0.7)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 1,
                    'hoverBackgroundColor': 'rgba(255, 99, 132, 0.9)',
                    'hoverBorderColor': 'rgba(255, 99, 132, 1)'
                }
            ]
        }
    
    def get_expense_type_breakdown(self) -> dict:
        stats = self.transactionManager.get_expense_type_stats()
        
        return {
            'labels': ['Fixed Expenses', 'Variable Expenses'],
            'datasets': [{
                'data': [
                    stats['fixed_amount'],
                    stats['variable_amount']
                ],
                'backgroundColor': ['#FF9800', '#9C27B0'],
                'borderColor': ['#F57C00', '#7B1FA2'],
                'borderWidth': 2,
                'hoverBackgroundColor': ['#FFB74D', '#BA68C8'],
                'hoverBorderColor': ['#FF9800', '#9C27B0']
            }]
        }
    
    def get_interactive_chart_config(self, chartType: ChartType) -> dict:
        baseConfig = {
            'responsive': True,
            'maintainAspectRatio': False,
            'interaction': {
                'intersect': False,
                'mode': 'nearest'
            },
            'plugins': {
                'legend': {
                    'position': 'top',
                    'labels': {
                        'usePointStyle': True,
                        'padding': 20,
                        'font': {
                            'size': 12
                        }
                    }
                },
                'tooltip': {
                    'enabled': True,
                    'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                    'titleColor': '#ffffff',
                    'bodyColor': '#ffffff',
                    'borderColor': 'rgba(255, 255, 255, 0.2)',
                    'borderWidth': 1,
                    'cornerRadius': 8,
                    'padding': 12,
                    'displayColors': True,
                    'usePointStyle': True,
                    'callbacks': {
                        'label': 'function(context) { return self.getTooltipLabel(context); }'
                    }
                }
            },
            'hover': {
                'animationDuration': 300,
                'onHover': 'function(event, elements) { self.handleChartHover(event, elements); }'
            }
        }
        
        if chartType in [ChartType.PIE, ChartType.DONUT]:
            baseConfig['plugins']['tooltip']['callbacks']['label'] = (
                'function(context) { '
                'const label = context.label || ""; '
                'const value = context.parsed || context.raw; '
                'const total = context.dataset.data.reduce((a, b) => a + b, 0); '
                'const percentage = Math.round((value / total) * 100); '
                'return `${label}: $${value.toFixed(2)} (${percentage}%)`; '
                '}'
            )
        elif chartType == ChartType.BAR:
            baseConfig['plugins']['tooltip']['callbacks']['label'] = (
                'function(context) { '
                'const datasetLabel = context.dataset.label || ""; '
                'const value = context.parsed.y || context.raw; '
                'return `${datasetLabel}: $${value.toFixed(2)}`; '
                '}'
            )
        elif chartType == ChartType.LINE:
            baseConfig['plugins']['tooltip']['callbacks']['label'] = (
                'function(context) { '
                'const datasetLabel = context.dataset.label || ""; '
                'const value = context.parsed.y || context.raw; '
                'return `${datasetLabel}: $${value.toFixed(2)}`; '
                '}'
            )
        
        return baseConfig
    
    def handle_chart_hover(self, chartType: str, elementIndex: int, elementData: Dict, budget: Budget, position: Dict) -> Dict[str, Any]:
        if elementIndex >= 0:  # Valid element hovered
            tooltipData = self.tooltipManager.create_tooltip_data(
                chartType, elementIndex, elementData, budget
            )
            tooltipData['position'] = position
            return {
                'action': 'show_tooltip',
                'tooltip': tooltipData,
                'chart_type': chartType,
                'element_index': elementIndex
            }
        else:  # No element hovered (pointer left)
            return {
                'action': 'hide_tooltip',
                'tooltip': self.tooltipManager.hide_tooltip()
            }
    
    def handle_chart_interaction(self, chartType: str, elementIndex: int, budget: 'Budget', interactionType: str = 'click') -> dict:
        if interactionType == 'hover':
            if chartType == 'category_breakdown' and elementIndex < len(budget.categories):
                category = budget.categories[elementIndex]
                return {
                    'action': 'hover',
                    'category_name': category.name,
                    'amount': category.plannedAmnt,
                    'type': category.type
                }
        
        elif interactionType == 'click':
            if chartType == 'category_breakdown':
                if elementIndex < len(budget.categories):
                    category = budget.categories[elementIndex]
                    return self.get_category_details(category)
            
            elif chartType == 'income_vs_expenses':
                elements = ['income', 'expenses', 'remaining']
                if elementIndex < len(elements):
                    return self.get_financial_overview(budget, elements[elementIndex])
        
        return {'message': 'Interaction handled', 'element_index': elementIndex}
    
    def get_category_details(self, category: 'Category') -> dict:
        category_transactions = self.transactionManager.get_category_transactions(
            category.categoryID
        )
        
        totalSpent = sum(t.total for t in category_transactions)
        remaining = category.plannedAmnt - totalSpent
        utilization = (totalSpent / category.plannedAmnt * 100) if category.plannedAmnt > 0 else 0
        
        return {
            'category_name': category.name,
            'planned_amount': category.plannedAmnt,
            'total_spent': totalSpent,
            'remaining_budget': remaining,
            'utilization_rate': round(utilization, 1),
            'transaction_count': len(category_transactions),
            'status': 'over_budget' if totalSpent > category.plannedAmnt else 'within_budget'
        }
    
    def get_financial_overview(self, budget: 'Budget', elementType: str) -> dict:
        totalExpenses = sum(cat.plannedAmnt for cat in budget.categories)
        remaining = budget.income - totalExpenses
        
        if elementType == 'income':
            return {
                'type': 'income',
                'amount': budget.income,
                'description': f'Total monthly income for {budget.month}',
                'recommendation': 'Consider increasing income sources if expenses are consistently high'
            }
        elif elementType == 'expenses':
            return {
                'type': 'expenses',
                'amount': totalExpenses,
                'description': f'Total planned expenses for {budget.month}',
                'recommendation': 'Review variable expenses for potential savings'
            }
        else:  # remaining
            status = 'healthy' if remaining >= 0 else 'deficit'
            return {
                'type': 'remaining',
                'amount': remaining,
                'description': f'Remaining funds after expenses for {budget.month}',
                'status': status,
                'recommendation': 'Consider saving or investing remaining funds' if remaining > 0 else 'Review expenses to eliminate deficit'
            }
    
    def generate_colors(self, count: int) -> List[str]:
        colorPalettes = {
            ChartTheme.COLORFUL: [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
            ],
            ChartTheme.LIGHT: [
                '#E8F4FD', '#FDECEF', '#FEF7E0', '#E8F7F7', '#F2EFFD',
                '#FFF0E6', '#E6F4EA', '#FCE8F3', '#E8F4FD', '#F0F4FF'
            ],
            ChartTheme.DARK: [
                '#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1C32',
                '#6B8F71', '#9C7CA5', '#2A4D14', '#5D5D81', '#8F754F'
            ]
        }
        
        palette = colorPalettes[self.chart_preferences['theme']]
        return [palette[i % len(palette)] for i in range(count)]
    
    def darken_color(self, color: str) -> str:
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            r = max(0, r - 30)
            g = max(0, g - 30)
            b = max(0, b - 30)
            return f'#{r:02x}{g:02x}{b:02x}'
        return color
    
    def lighten_color(self, color: str) -> str:
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            r = min(255, r + 30)
            g = min(255, g + 30)
            b = min(255, b + 30)
            return f'#{r:02x}{g:02x}{b:02x}'
        return color
    
    def update_chart_preferences(self, preferences: dict):
        if 'default_type' in preferences:
            self.chartPreferences['default_type'] = ChartType(preferences['default_type'])
        if 'theme' in preferences:
            self.chartPreferences['theme'] = ChartTheme(preferences['theme'])
        if 'animate' in preferences:
            self.chartPreferences['animate'] = bool(preferences['animate'])
        if 'interactive' in preferences:
            self.chartPreferences['interactive'] = bool(preferences['interactive'])
        if 'tooltip_delay' in preferences:
            self.chartPreferences['tooltip_delay'] = int(preferences['tooltip_delay'])
    
    def get_all_chart_data(self, budget: 'Budget') -> dict:
        return {
            'income_vs_expenses': self.get_income_vs_expenses_data(budget),
            'category_breakdown': self.get_category_breakdown_data(budget),
            'spending_trend': self.get_spending_trend_data(),
            'actual_vs_planned': self.get_actual_vs_planned_data(budget),
            'expense_type_breakdown': self.get_expense_type_breakdown(),
            'chart_configs': {
                'pie': self.get_interactive_chart_config(ChartType.PIE),
                'bar': self.get_interactive_chart_config(ChartType.BAR),
                'line': self.get_interactive_chart_config(ChartType.LINE),
                'donut': self.get_interactive_chart_config(ChartType.DONUT)
            },
            'preferences': {
                'default_type': self.chartPreferences['default_type'].value,
                'theme': self.chartPreferences['theme'].value,
                'animate': self.chartPreferences['animate'],
                'interactive': self.chartPreferences['interactive'],
                'tooltip_delay': self.chartPreferences['tooltip_delay']
            },
            'tooltip_support': True
        }