import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from collections import defaultdict
import json

class CategoryClassifier:
    """AI-powered category classification for expenses"""
    
    def __init__(self):
        # Define category keywords with weights
        self.category_keywords = {
            'Food': {
                'keywords': ['restaurant', 'food', 'meal', 'lunch', 'dinner', 'breakfast', 'cafe', 'coffee', 'pizza', 'burger', 'snack', 'grocery', 'supermarket', 'kfc', 'mcdonalds', 'dominos', 'zomato', 'swiggy', 'uber eats', 'kitchen', 'dining', 'bakery', 'juice', 'tea'],
                'weight': 1.0
            },
            'Transport': {
                'keywords': ['uber', 'taxi', 'bus', 'metro', 'train', 'fuel', 'petrol', 'diesel', 'parking', 'toll', 'auto', 'rickshaw', 'ola', 'transport', 'travel', 'flight', 'airline', 'ticket', 'cab', 'bike', 'car'],
                'weight': 1.0
            },
            'Entertainment': {
                'keywords': ['movie', 'cinema', 'theatre', 'netflix', 'spotify', 'amazon prime', 'gaming', 'game', 'entertainment', 'fun', 'party', 'club', 'bar', 'concert', 'show', 'sports', 'gym', 'fitness'],
                'weight': 1.0
            },
            'Shopping': {
                'keywords': ['amazon', 'flipkart', 'shopping', 'clothes', 'shoes', 'electronics', 'mobile', 'laptop', 'book', 'gift', 'online', 'store', 'mall', 'purchase', 'buy', 'myntra', 'nykaa'],
                'weight': 1.0
            },
            'Healthcare': {
                'keywords': ['doctor', 'hospital', 'medical', 'pharmacy', 'medicine', 'health', 'clinic', 'dentist', 'checkup', 'treatment', 'insurance', 'apollo', 'fortis', 'medicine', 'tablet'],
                'weight': 1.0
            },
            'Utilities': {
                'keywords': ['electricity', 'water', 'gas', 'internet', 'phone', 'mobile', 'recharge', 'bill', 'utility', 'wifi', 'broadband', 'jio', 'airtel', 'vodafone'],
                'weight': 1.0
            },
            'Rent': {
                'keywords': ['rent', 'house', 'apartment', 'flat', 'home', 'lease', 'deposit', 'maintenance', 'society'],
                'weight': 1.2  # Higher weight for rent as it's usually clear
            },
            'Education': {
                'keywords': ['school', 'college', 'university', 'course', 'training', 'book', 'education', 'tuition', 'fee', 'study', 'learning'],
                'weight': 1.0
            },
            'Personal Care': {
                'keywords': ['salon', 'haircut', 'beauty', 'cosmetics', 'personal', 'care', 'grooming', 'spa', 'massage'],
                'weight': 1.0
            },
            'Others': {
                'keywords': ['miscellaneous', 'other', 'misc', 'general', 'various'],
                'weight': 0.5
            }
        }
        
        self.confidence_threshold = 0.6
    
    def classify_expense(self, description, amount=None):
        """
        Classify expense based on description and amount
        Returns: (category, confidence_score)
        """
        if not description:
            return 'Others', 0.0
        
        description_lower = description.lower()
        scores = defaultdict(float)
        
        # Calculate scores for each category
        for category, data in self.category_keywords.items():
            keywords = data['keywords']
            weight = data['weight']
            
            for keyword in keywords:
                if keyword in description_lower:
                    # Exact match gets full score
                    if keyword == description_lower:
                        scores[category] += 2.0 * weight
                    # Partial match gets partial score
                    elif keyword in description_lower:
                        scores[category] += 1.0 * weight
        
        # Amount-based hints
        if amount:
            if amount > 20000:  # High amount might be rent
                scores['Rent'] += 0.3
            elif amount < 100:  # Small amount might be food/transport
                scores['Food'] += 0.2
                scores['Transport'] += 0.2
        
        if not scores:
            return 'Others', 0.0
        
        # Get best category
        best_category = max(scores.items(), key=lambda x: x[1])
        category, score = best_category
        
        # Normalize confidence score
        max_possible_score = 2.0 * self.category_keywords[category]['weight']
        confidence = min(score / max_possible_score, 1.0)
        
        return category, confidence
    
    def suggest_category(self, description, amount=None):
        """
        Suggest category with confidence
        Returns: (category, is_confident)
        """
        category, confidence = self.classify_expense(description, amount)
        is_confident = confidence >= self.confidence_threshold
        return category, is_confident

class SavingsAnalyzer:
    """Analyze savings and provide recommendations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_monthly_savings(self, year=None, month=None):
        """Calculate monthly savings"""
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        
        # Get monthly income
        income_query = "SELECT monthly_income FROM user_settings ORDER BY updated_at DESC LIMIT 1"
        income_result = self.db_manager.execute_query(income_query)
        monthly_income = income_result['monthly_income'].iloc[0] if not income_result.empty else 50000
        
        # Get monthly expenses
        expense_query = """
            SELECT COALESCE(SUM(amount), 0) as total_expense 
            FROM expenses 
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        """
        expense_result = self.db_manager.execute_query(expense_query, (str(year), f"{month:02d}"))
        total_expense = expense_result['total_expense'].iloc[0] if not expense_result.empty else 0
        
        savings = monthly_income - total_expense
        return {
            'income': monthly_income,
            'expense': total_expense,
            'savings': savings,
            'savings_rate': (savings / monthly_income * 100) if monthly_income > 0 else 0
        }
    
    def get_category_analysis(self, year=None, month=None, limit=None):
        """Analyze spending by category"""
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        
        query = """
            SELECT category, SUM(amount) as total_amount, COUNT(*) as count
            FROM expenses 
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            GROUP BY category
            ORDER BY total_amount DESC
        """
        
        params = (str(year), f"{month:02d}")
        if limit:
            query += f" LIMIT {limit}"
            
        return self.db_manager.execute_query(query, params)
    
    def generate_savings_suggestions(self, year=None, month=None):
        """Generate AI-powered savings suggestions"""
        savings_data = self.get_monthly_savings(year, month)
        category_data = self.get_category_analysis(year, month)
        
        suggestions = []
        
        # Check if overspending
        if savings_data['savings'] < 0:
            suggestions.append({
                'type': 'alert',
                'message': f"⚠️ You're overspending by ₹{abs(savings_data['savings']):,.2f} this month!"
            })
        
        # Analyze top spending categories
        if not category_data.empty:
            total_expense = category_data['total_amount'].sum()
            
            for _, row in category_data.head(3).iterrows():
                category = row['category']
                amount = row['total_amount']
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                
                if percentage > 30:  # High spending in one category
                    suggestions.append({
                        'type': 'warning',
                        'message': f"💡 {category} accounts for {percentage:.1f}% of your spending (₹{amount:,.2f}). Consider reducing expenses in this area."
                    })
                elif percentage > 20:
                    suggestions.append({
                        'type': 'info',
                        'message': f"📊 {category}: ₹{amount:,.2f} ({percentage:.1f}% of total spending)"
                    })
        
        # Savings rate suggestions
        if savings_data['savings_rate'] < 20:
            suggestions.append({
                'type': 'tip',
                'message': f"💰 Your savings rate is {savings_data['savings_rate']:.1f}%. Financial experts recommend saving at least 20% of income."
            })
        elif savings_data['savings_rate'] > 30:
            suggestions.append({
                'type': 'success',
                'message': f"🎉 Great job! Your savings rate of {savings_data['savings_rate']:.1f}% is excellent!"
            })
        
        return suggestions
    
    def calculate_goal_plan(self, target_amount, target_date, current_savings=0):
        """Calculate monthly savings needed for a goal"""
        target_datetime = datetime.strptime(target_date, '%Y-%m-%d') if isinstance(target_date, str) else target_date
        months_remaining = max(1, (target_datetime.year - datetime.now().year) * 12 + target_datetime.month - datetime.now().month)
        
        remaining_amount = target_amount - current_savings
        monthly_required = remaining_amount / months_remaining if months_remaining > 0 else remaining_amount
        
        # Get current savings capacity
        current_month_data = self.get_monthly_savings()
        current_savings_capacity = max(0, current_month_data['savings'])
        
        feasibility = "Achievable" if monthly_required <= current_savings_capacity else "Challenging"
        if monthly_required > current_savings_capacity * 1.5:
            feasibility = "Requires significant lifestyle changes"
        
        return {
            'monthly_required': monthly_required,
            'months_remaining': months_remaining,
            'remaining_amount': remaining_amount,
            'current_savings_capacity': current_savings_capacity,
            'feasibility': feasibility,
            'completion_percentage': (current_savings / target_amount * 100) if target_amount > 0 else 0
        }

class ExpensePredictor:
    """Predict future expenses and trends"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_spending_trends(self, months=6):
        """Get spending trends over last N months"""
        query = """
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(amount) as total_amount,
                category
            FROM expenses 
            WHERE date >= date('now', '-{} months')
            GROUP BY strftime('%Y-%m', date), category
            ORDER BY month, category
        """.format(months)
        
        return self.db_manager.execute_query(query)
    
    def predict_monthly_expense(self, category=None):
        """Predict next month's expenses based on historical data"""
        if category:
            query = """
                SELECT AVG(monthly_total) as predicted_amount
                FROM (
                    SELECT 
                        strftime('%Y-%m', date) as month,
                        SUM(amount) as monthly_total
                    FROM expenses 
                    WHERE category = ? AND date >= date('now', '-6 months')
                    GROUP BY strftime('%Y-%m', date)
                )
            """
            result = self.db_manager.execute_query(query, (category,))
        else:
            query = """
                SELECT AVG(monthly_total) as predicted_amount
                FROM (
                    SELECT 
                        strftime('%Y-%m', date) as month,
                        SUM(amount) as monthly_total
                    FROM expenses 
                    WHERE date >= date('now', '-6 months')
                    GROUP BY strftime('%Y-%m', date)
                )
            """
            result = self.db_manager.execute_query(query)
        
        return result['predicted_amount'].iloc[0] if not result.empty and not pd.isna(result['predicted_amount'].iloc[0]) else 0

# Initialize global instances
classifier = CategoryClassifier()