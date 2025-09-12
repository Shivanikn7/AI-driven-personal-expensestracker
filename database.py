import sqlite3
import pandas as pd
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path='expense_tracker.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                date DATE NOT NULL,
                category TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create cashout table for tracking cash balance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cashout (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('add', 'remove')),
                amount REAL NOT NULL,
                description TEXT,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create budget table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monthly_budget REAL NOT NULL,
                category_budgets TEXT, -- JSON string for category-wise budgets
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create future goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS future_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                target_date DATE NOT NULL,
                saved_amount REAL DEFAULT 0,
                monthly_savings REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create user settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monthly_income REAL DEFAULT 0,
                cash_balance REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize default settings if not exists
        self.init_default_settings()
    
    def init_default_settings(self):
        """Initialize default user settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM user_settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO user_settings (monthly_income, cash_balance)
                VALUES (50000, 10000)
            ''')
            conn.commit()
        
        conn.close()
    
    def load_sample_data(self, csv_file='sample_expenses.csv'):
        """Load sample data from CSV file"""
        if not os.path.exists(csv_file):
            return False
        
        try:
            df = pd.read_csv(csv_file)
            conn = self.get_connection()
            
            # Clear existing data
            cursor = conn.cursor()
            cursor.execute('DELETE FROM expenses')
            conn.commit()
            
            # Insert sample data
            df.to_sql('expenses', conn, if_exists='append', index=False)
            conn.close()
            return True
        except Exception as e:
            print(f"Error loading sample data: {e}")
            return False
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        conn = self.get_connection()
        try:
            if params:
                result = pd.read_sql_query(query, conn, params=params)
            else:
                result = pd.read_sql_query(query, conn)
            return result
        finally:
            conn.close()
    
    def execute_update(self, query, params=None):
        """Execute an update/insert/delete query"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

# Initialize database when module is imported
db_manager = DatabaseManager()