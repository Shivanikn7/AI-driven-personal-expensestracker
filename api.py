from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from datetime import datetime, timedelta
import json
from database import db_manager
from utils import classifier, SavingsAnalyzer, ExpensePredictor
from visuals import chart_generator

app = Flask(__name__)
CORS(app)  # Enable CORS for Streamlit integration

# Initialize analyzers
savings_analyzer = SavingsAnalyzer(db_manager)
expense_predictor = ExpensePredictor(db_manager)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# ============ EXPENSE MANAGEMENT ENDPOINTS ============

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    """Get all expenses with optional filtering"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        limit = request.args.get('limit', type=int)
        
        # Build query
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY date DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        expenses = db_manager.execute_query(query, params if params else None)
        
        return jsonify({
            'status': 'success',
            'data': expenses.to_dict('records'),
            'total': len(expenses)
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    """Add a new expense"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['description', 'amount', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
        
        description = data['description']
        amount = float(data['amount'])
        date = data['date']
        
        # Auto-detect category if not provided
        if 'category' not in data or not data['category']:
            suggested_category, is_confident = classifier.suggest_category(description, amount)
            category = suggested_category
        else:
            category = data['category']
            is_confident = True
        
        # Insert expense
        query = """
            INSERT INTO expenses (description, amount, date, category)
            VALUES (?, ?, ?, ?)
        """
        expense_id = db_manager.execute_update(query, (description, amount, date, category))
        
        return jsonify({
            'status': 'success',
            'message': 'Expense added successfully',
            'data': {
                'id': expense_id,
                'description': description,
                'amount': amount,
                'date': date,
                'category': category,
                'auto_categorized': not is_confident
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """Update an existing expense"""
    try:
        data = request.get_json()
        
        # Build update query dynamically
        fields = []
        params = []
        
        if 'description' in data:
            fields.append('description = ?')
            params.append(data['description'])
        
        if 'amount' in data:
            fields.append('amount = ?')
            params.append(float(data['amount']))
        
        if 'date' in data:
            fields.append('date = ?')
            params.append(data['date'])
        
        if 'category' in data:
            fields.append('category = ?')
            params.append(data['category'])
        
        if not fields:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400
        
        params.append(expense_id)
        query = f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?"
        
        db_manager.execute_update(query, params)
        
        return jsonify({
            'status': 'success',
            'message': 'Expense updated successfully'
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        query = "DELETE FROM expenses WHERE id = ?"
        db_manager.execute_update(query, (expense_id,))
        
        return jsonify({
            'status': 'success',
            'message': 'Expense deleted successfully'
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/expenses/suggest-category', methods=['POST'])
def suggest_category():
    """Suggest category for expense description"""
    try:
        data = request.get_json()
        description = data.get('description', '')
        amount = data.get('amount')
        
        if amount:
            amount = float(amount)
        
        suggested_category, is_confident = classifier.suggest_category(description, amount)
        
        return jsonify({
            'status': 'success',
            'data': {
                'suggested_category': suggested_category,
                'is_confident': is_confident,
                'confidence_level': 'high' if is_confident else 'low'
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============ CASHOUT MANAGEMENT ENDPOINTS ============

@app.route('/api/cashout', methods=['GET'])
def get_cashout_history():
    """Get cashout history"""
    try:
        query = "SELECT * FROM cashout ORDER BY date DESC LIMIT 50"
        history = db_manager.execute_query(query)
        
        # Get current balance
        balance_query = "SELECT cash_balance FROM user_settings ORDER BY updated_at DESC LIMIT 1"
        balance_result = db_manager.execute_query(balance_query)
        current_balance = balance_result['cash_balance'].iloc[0] if not balance_result.empty else 0
        
        return jsonify({
            'status': 'success',
            'data': {
                'history': history.to_dict('records'),
                'current_balance': current_balance
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/cashout', methods=['POST'])
def manage_cashout():
    """Add or remove cash"""
    try:
        data = request.get_json()
        
        required_fields = ['type', 'amount', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
        
        cashout_type = data['type']  # 'add' or 'remove'
        amount = float(data['amount'])
        date = data['date']
        description = data.get('description', '')
        
        if cashout_type not in ['add', 'remove']:
            return jsonify({'status': 'error', 'message': 'Type must be either "add" or "remove"'}), 400
        
        # Get current balance
        balance_query = "SELECT cash_balance FROM user_settings ORDER BY updated_at DESC LIMIT 1"
        balance_result = db_manager.execute_query(balance_query)
        current_balance = balance_result['cash_balance'].iloc[0] if not balance_result.empty else 0
        
        # Calculate new balance
        if cashout_type == 'add':
            new_balance = current_balance + amount
        else:
            new_balance = current_balance - amount
            if new_balance < 0:
                return jsonify({'status': 'error', 'message': 'Insufficient cash balance'}), 400
        
        # Insert cashout record
        cashout_query = """
            INSERT INTO cashout (type, amount, description, date)
            VALUES (?, ?, ?, ?)
        """
        db_manager.execute_update(cashout_query, (cashout_type, amount, description, date))
        
        # Update cash balance
        balance_update_query = """
            UPDATE user_settings SET cash_balance = ?, updated_at = CURRENT_TIMESTAMP
        """
        db_manager.execute_update(balance_update_query, (new_balance,))
        
        return jsonify({
            'status': 'success',
            'message': f'Cash {"added" if cashout_type == "add" else "removed"} successfully',
            'data': {
                'old_balance': current_balance,
                'new_balance': new_balance,
                'amount': amount,
                'type': cashout_type
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============ ANALYTICS ENDPOINTS ============

@app.route('/api/analytics/monthly-savings', methods=['GET'])
def get_monthly_savings():
    """Get monthly savings analysis"""
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        savings_data = savings_analyzer.get_monthly_savings(year, month)
        
        return jsonify({
            'status': 'success',
            'data': savings_data
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/analytics/category-analysis', methods=['GET'])
def get_category_analysis():
    """Get category-wise spending analysis"""
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        category_data = savings_analyzer.get_category_analysis(year, month)
        
        return jsonify({
            'status': 'success',
            'data': category_data.to_dict('records')
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/analytics/suggestions', methods=['GET'])
def get_savings_suggestions():
    """Get AI-powered savings suggestions"""
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        suggestions = savings_analyzer.generate_savings_suggestions(year, month)
        
        return jsonify({
            'status': 'success',
            'data': suggestions
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/analytics/spending-trends', methods=['GET'])
def get_spending_trends():
    """Get spending trends over time"""
    try:
        months = request.args.get('months', 6, type=int)
        
        trends = expense_predictor.get_spending_trends(months)
        
        return jsonify({
            'status': 'success',
            'data': trends.to_dict('records')
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/analytics/predict-expense', methods=['GET'])
def predict_expense():
    """Predict next month's expenses"""    
    try:
        category = request.args.get('category')
        
        predicted_amount = expense_predictor.predict_monthly_expense(category)
        
        return jsonify({
            'status': 'success',
            'data': {
                'predicted_amount': predicted_amount,
                'category': category if category else 'all'
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============ CHART GENERATION ENDPOINTS ============

@app.route('/api/charts/pie-chart', methods=['GET'])
def generate_pie_chart():
    """Generate pie chart for category distribution"""
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        category_data = savings_analyzer.get_category_analysis(year, month)
        
        if category_data.empty:
            return jsonify({'status': 'error', 'message': 'No data available for chart'}), 404
        
        chart_base64 = chart_generator.create_pie_chart(
            category_data, 
            title=f"Expense Distribution - {datetime(year, month, 1).strftime('%B %Y')}"
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'chart': chart_base64,
                'title': f"Expense Distribution - {datetime(year, month, 1).strftime('%B %Y')}"
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/charts/monthly-spending', methods=['GET'])
def generate_monthly_spending_chart():
    """Generate monthly spending vs budget chart"""
    try:
        months = request.args.get('months', 6, type=int)
        
        # Get monthly spending data
        spending_query = """
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(amount) as total_amount
            FROM expenses 
            WHERE date >= date('now', '-{} months')
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        """.format(months)
        
        spending_data = db_manager.execute_query(spending_query)
        
        if spending_data.empty:
            return jsonify({'status': 'error', 'message': 'No spending data available'}), 404
        
        # For now, we'll use a fixed budget. In a real app, this would come from user settings
        budget_amount = 40000  # Default budget
        budget_data = pd.DataFrame({
            'month': spending_data['month'],
            'budget': [budget_amount] * len(spending_data)
        })
        
        chart_base64 = chart_generator.create_monthly_spending_bar_chart(
            spending_data, 
            budget_data,
            title="Monthly Spending vs Budget"
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'chart': chart_base64,
                'title': "Monthly Spending vs Budget"
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/charts/savings-trend', methods=['GET'])
def generate_savings_trend_chart():
    """Generate savings trend chart"""
    try:
        months = request.args.get('months', 6, type=int)
        
        # Get monthly data
        query = """
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(amount) as expense
            FROM expenses 
            WHERE date >= date('now', '-{} months')
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        """.format(months)
        
        expense_data = db_manager.execute_query(query)
        
        if expense_data.empty:
            return jsonify({'status': 'error', 'message': 'No data available for savings trend'}), 404
        
        # Get income (assuming fixed for now)
        income_query = "SELECT monthly_income FROM user_settings ORDER BY updated_at DESC LIMIT 1"
        income_result = db_manager.execute_query(income_query)
        monthly_income = income_result['monthly_income'].iloc[0] if not income_result.empty else 50000
        
        # Calculate savings
        savings_data = expense_data.copy()
        savings_data['income'] = monthly_income
        savings_data['savings'] = savings_data['income'] - savings_data['expense']
        
        chart_base64 = chart_generator.create_savings_trend_chart(
            savings_data,
            title="Monthly Savings Trend"
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'chart': chart_base64,
                'title': "Monthly Savings Trend"
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============ FUTURE GOALS ENDPOINTS ============

@app.route('/api/goals', methods=['GET'])
def get_goals():
    """Get all financial goals"""
    try:
        query = "SELECT * FROM future_goals WHERE is_active = 1 ORDER BY target_date"
        goals = db_manager.execute_query(query)
        
        return jsonify({
            'status': 'success',
            'data': goals.to_dict('records')
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/goals', methods=['POST'])
def add_goal():
    """Add a new financial goal"""
    try:
        data = request.get_json()
        
        required_fields = ['goal_name', 'target_amount', 'target_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
        
        goal_name = data['goal_name']
        target_amount = float(data['target_amount'])
        target_date = data['target_date']
        saved_amount = float(data.get('saved_amount', 0))
        
        # Calculate required monthly savings
        goal_plan = savings_analyzer.calculate_goal_plan(target_amount, target_date, saved_amount)
        monthly_savings = goal_plan['monthly_required']
        
        query = """
            INSERT INTO future_goals (goal_name, target_amount, target_date, saved_amount, monthly_savings)
            VALUES (?, ?, ?, ?, ?)
        """
        goal_id = db_manager.execute_update(query, (goal_name, target_amount, target_date, saved_amount, monthly_savings))
        
        return jsonify({
            'status': 'success',
            'message': 'Goal added successfully',
            'data': {
                'id': goal_id,
                'goal_plan': goal_plan
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/goals/<int:goal_id>/plan', methods=['GET'])
def get_goal_plan(goal_id):
    """Get detailed plan for a specific goal"""
    try:
        # Get goal details
        query = "SELECT * FROM future_goals WHERE id = ?"
        goal_result = db_manager.execute_query(query, (goal_id,))
        
        if goal_result.empty:
            return jsonify({'status': 'error', 'message': 'Goal not found'}), 404
        
        goal = goal_result.iloc[0]
        
        # Calculate plan
        goal_plan = savings_analyzer.calculate_goal_plan(
            goal['target_amount'], 
            goal['target_date'], 
            goal['saved_amount']
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'goal': goal.to_dict(),
                'plan': goal_plan
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============ USER SETTINGS ENDPOINTS ============

@app.route('/api/settings', methods=['GET'])
def get_user_settings():
    """Get user settings"""
    try:
        query = "SELECT * FROM user_settings ORDER BY updated_at DESC LIMIT 1"
        settings = db_manager.execute_query(query)
        
        if settings.empty:
            return jsonify({'status': 'error', 'message': 'No settings found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': settings.iloc[0].to_dict()
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def update_user_settings():
    """Update user settings"""
    try:
        data = request.get_json()
        
        fields = []
        params = []
        
        if 'monthly_income' in data:
            fields.append('monthly_income = ?')
            params.append(float(data['monthly_income']))
        
        if 'cash_balance' in data:
            fields.append('cash_balance = ?')
            params.append(float(data['cash_balance']))
        
        if not fields:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400
        
        fields.append('updated_at = CURRENT_TIMESTAMP')
        
        query = f"UPDATE user_settings SET {', '.join(fields)}"
        db_manager.execute_update(query, params)
        
        return jsonify({
            'status': 'success',
            'message': 'Settings updated successfully'
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    