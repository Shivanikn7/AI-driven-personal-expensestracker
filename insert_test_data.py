import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('expense_tracker.db')
cursor = conn.cursor()

# Insert a test expense for September 2025
cursor.execute('''
    INSERT INTO expenses (description, amount, date, category)
    VALUES (?, ?, ?, ?)
''', (
    'Test Grocery', 1500, '2025-09-10', 'Food'
))

# Ensure user_settings has a monthly_income value
cursor.execute('''
    UPDATE user_settings SET monthly_income = 50000, updated_at = ?
''', (datetime.now().isoformat(),))

conn.commit()
conn.close()
print('Test data inserted for September 2025.')
