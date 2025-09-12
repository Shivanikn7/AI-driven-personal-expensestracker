import requests
import random
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api/expenses"

categories = ['Food', 'Transport', 'Shopping', 'Bills', 'Entertainment', 'Groceries']
descriptions = {
    'Food': ['Lunch at restaurant', 'Dinner with friends', 'Snacks', 'Café coffee'],
    'Transport': ['Bus ticket', 'Cab ride', 'Train pass', 'Fuel refill'],
    'Shopping': ['T-shirt', 'Jeans', 'Shoes', 'Online order'],
    'Bills': ['Electricity bill', 'Phone recharge', 'Wi-Fi subscription'],
    'Entertainment': ['Movie ticket', 'Concert', 'Streaming service'],
    'Groceries': ['Vegetables', 'Milk and eggs', 'Monthly grocery']
}

def generate_expense():
    category = random.choice(categories)
    description = random.choice(descriptions[category])
    amount = round(random.uniform(50, 2000), 2)
    date = (datetime.now() - timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d')
    return {
        "description": description,
        "amount": amount,
        "date": date,
        "category": category
    }

def post_expenses(n=20):
    for _ in range(n):
        expense = generate_expense()
        res = requests.post(BASE_URL, json=expense)
        if res.status_code == 200:
            print("✅ Added:", expense)
        else:
            print("❌ Failed:", expense, res.text)

if __name__ == "__main__":
    post_expenses()
