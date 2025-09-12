import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, date
import json
import base64
from io import BytesIO
import plotly.express as px
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:5000/api"

# Custom CSS for better styling
st.markdown("""
<style>
    /* Overall App Background */
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1588776814546-ec20b00c55b5?auto=format&fit=crop&w=1740&q=80');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Central Container */
    .block-container {
        background-color: rgba(255, 255, 255, 0.92);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        margin-top: 1rem;
    }

    /* Header Styling */
    .main-header {
        font-size: 3rem;
        color: #ffffff;
        text-align: center;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.6);
    }

    /* Metric Styling */
    .stMetric {
        background-color: #ecf4fc;
        border-left: 5px solid #3498db;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Form Input Styling */
    input, textarea, select {
        border-radius: 6px !important;
        padding: 8px !important;
        border: 1px solid #ccc !important;
    }

    /* Button Styling */
    button[kind="primary"] {
        background-color: #3498db !important;
        color: white !important;
        border: none !important;
        padding: 10px 16px !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: 0.3s ease-in-out;
    }
    button[kind="primary"]:hover {
        background-color: #217dbb !important;
    }

    button[kind="secondary"] {
        background-color: #e74c3c !important;
        color: white !important;
        border: none !important;
        padding: 10px 16px !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }

    /* Expander Section Styling */
    .st-expander > summary {
        background-color: #2980b9 !important;
        color: white !important;
        padding: 10px;
        border-radius: 10px;
        font-weight: 600;
    }

    /* Alert messages */
    .stAlert {
        border-radius: 10px;
        font-size: 1rem;
    }

    /* Scrollbar Customization */
    ::-webkit-scrollbar {
        width: 10px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background-color: rgba(52, 152, 219, 0.6);
        border-radius: 5px;
    }

</style>py
""", unsafe_allow_html=True)

# Helper Functions
def make_api_request(endpoint, method="GET", data=None, params=None):
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def format_currency(amount):
    """Format amount as currency"""
    return f"₹{amount:,.2f}"

def get_categories():
    """Get predefined categories"""
    return [
        "Food", "Transport", "Entertainment", "Shopping", 
        "Healthcare", "Utilities", "Rent", "Education", 
        "Personal Care", "Others"
    ]

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Sidebar Navigation
st.sidebar.title("💰 Expense Tracker")
st.sidebar.markdown("---")

pages = {
    "📊 Dashboard": "Dashboard",
    "💸 Expenses": "Expenses", 
    "💰 Cash Management": "Cash Management",
    "📈 Analytics": "Analytics",
    "🎯 Goals": "Goals",
    "⚙️ Settings": "Settings"
}

for display_name, page_name in pages.items():
    if st.sidebar.button(display_name, key=f"nav_{page_name}"):
        st.session_state.current_page = page_name

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip**: Use AI-powered category detection for smart expense tracking!")

# Main Content Area
current_page = st.session_state.current_page

# DASHBOARD PAGE
if current_page == "Dashboard":
    st.markdown('<h1 class="main-header">💰 Personal Expense Tracker</h1>', unsafe_allow_html=True)
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    
    # Get current month data
    current_date = datetime.now()
    monthly_savings = make_api_request(
        "/analytics/monthly-savings", 
        params={"year": current_date.year, "month": current_date.month}
    )
    
    if monthly_savings and monthly_savings['status'] == 'success':
        data = monthly_savings['data']
        
        with col1:
            st.metric(
                label="Monthly Income",
                value=format_currency(data['income']),
                delta=None
            )
        
        with col2:
            st.metric(
                label="Monthly Expenses",
                value=format_currency(data['expense']),
                delta=None
            )
        
        with col3:
            savings_color = "normal" if data['savings'] >= 0 else "inverse"
            st.metric(
                label="Monthly Savings",
                value=format_currency(data['savings']),
                delta=f"{data['savings_rate']:.1f}% of income"
            )
        
        with col4:
            # Get cash balance
            settings_response = make_api_request("/settings")
            cash_balance = 0
            if settings_response and settings_response['status'] == 'success':
                cash_balance = settings_response['data'].get('cash_balance', 0)
            
            st.metric(
                label="Cash Balance",
                value=format_currency(cash_balance),
                delta=None
            )
    
    st.markdown("---")
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Monthly Expense Distribution")
        pie_chart_response = make_api_request("/charts/pie-chart", params={
            "year": current_date.year, 
            "month": current_date.month
        })
        
        if pie_chart_response and pie_chart_response['status'] == 'success':
            chart_data = pie_chart_response['data']['chart']
            st.markdown(f'<img src="{chart_data}" style="width:100%">', unsafe_allow_html=True)
        else:
            st.info("No expense data available for this month")
    
    with col2:
        st.subheader("📈 Monthly Spending Trend")
        spending_chart_response = make_api_request("/charts/monthly-spending", params={"months": 6})
        
        if spending_chart_response and spending_chart_response['status'] == 'success':
            chart_data = spending_chart_response['data']['chart']
            st.markdown(f'<img src="{chart_data}" style="width:100%">', unsafe_allow_html=True)
        else:
            st.info("No spending trend data available")
    
    # Recent Expenses
    st.subheader("🕒 Recent Expenses")
    recent_expenses = make_api_request("/expenses", params={"limit": 10})
    
    if recent_expenses and recent_expenses['status'] == 'success':
        expenses_df = pd.DataFrame(recent_expenses['data'])
        if not expenses_df.empty:
            expenses_df['amount'] = expenses_df['amount'].apply(format_currency)
            st.dataframe(
                expenses_df[['date', 'description', 'category', 'amount']], 
                use_container_width=True
            )
        else:
            st.info("No recent expenses found")
    
    # AI Suggestions
    st.subheader("🤖 AI Savings Suggestions")
    suggestions_response = make_api_request("/analytics/suggestions", params={
        "year": current_date.year, 
        "month": current_date.month
    })
    
    if suggestions_response and suggestions_response['status'] == 'success':
        suggestions = suggestions_response['data']
        
        for suggestion in suggestions:
            if suggestion['type'] == 'alert':
                st.error(suggestion['message'])
            elif suggestion['type'] == 'warning':
                st.warning(suggestion['message'])
            elif suggestion['type'] == 'success':
                st.success(suggestion['message'])
            else:
                st.info(suggestion['message'])

# EXPENSES PAGE
elif current_page == "Expenses":
    st.header("💸 Expense Management")
    
    # Add New Expense
    with st.expander("➕ Add New Expense", expanded=False):
     with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            description = st.text_input("Description*", placeholder="e.g., KFC lunch")
            amount = st.number_input("Amount*", min_value=0.01, step=0.01)
            expense_date = st.date_input("Date*", value=date.today())

        with col2:
            categories = get_categories()
            default_index = len(categories) - 1  # default to "Others"
            category = st.selectbox("Category*", categories, index=default_index)

        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            suggest_category = st.form_submit_button("🤖 Suggest Category")

        with col_btn2:
            submit_expense = st.form_submit_button("💾 Add Expense")

        # Handle Suggest Category
        if suggest_category and description:
            category_response = make_api_request("/expenses/suggest-category", 
                                                 method="POST", 
                                                 data={"description": description, "amount": amount})
            if category_response and category_response['status'] == 'success':
                suggested_category = category_response['data']['suggested_category']
                confidence = category_response['data']['confidence_level']
                st.info(f"Suggested: {suggested_category} (Confidence: {confidence})")

        # Handle Expense Submission
        if submit_expense:
            if description and amount > 0:
                expense_data = {
                    "description": description,
                    "amount": amount,
                    "date": expense_date.isoformat(),
                    "category": category
                }

                response = make_api_request("/expenses", method="POST", data=expense_data)

                if response and response['status'] == 'success':
                    st.success("✅ Expense added successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Failed to add expense")
            else:
                st.error("❌ Please fill all required fields")

    # Expense Filters
    st.subheader("🔍 Filter Expenses")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        start_date = st.date_input("From Date", value=date.today() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("To Date", value=date.today())
    
    with col3:
        filter_category = st.selectbox("Category", ["All"] + get_categories())
    
    with col4:
        st.write("")  # Space
        if st.button("🔍 Apply Filters"):
            st.session_state.apply_filters = True
    
    # Get and Display Expenses
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
    
    if filter_category != "All":
        params["category"] = filter_category
    
    expenses_response = make_api_request("/expenses", params=params)
    
    if expenses_response and expenses_response['status'] == 'success':
        expenses_data = expenses_response['data']
        
        if expenses_data:
            expenses_df = pd.DataFrame(expenses_data)
            
            # Display summary
            total_amount = expenses_df['amount'].sum()
            total_count = len(expenses_df)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Expenses", format_currency(total_amount))
            with col2:
                st.metric("Number of Transactions", total_count)
            with col3:
                avg_amount = total_amount / total_count if total_count > 0 else 0
                st.metric("Average Amount", format_currency(avg_amount))
            
            # Display expenses table with edit/delete options
            st.subheader("📋 Expense List")
            
            for idx, expense in expenses_df.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
                    
                    with col1:
                        st.write(f"**{expense['description']}**")
                    with col2:
                        st.write(f"**{format_currency(expense['amount'])}**")
                    with col3:
                        st.write(expense['category'])
                    with col4:
                        st.write(expense['date'])
                    with col5:
                        if st.button("✏️", key=f"edit_{expense['id']}", help="Edit"):
                            st.session_state[f"edit_expense_{expense['id']}"] = True
                    with col6:
                        if st.button("🗑️", key=f"delete_{expense['id']}", help="Delete"):
                            delete_response = make_api_request(f"/expenses/{expense['id']}", method="DELETE")
                            if delete_response and delete_response['status'] == 'success':
                                st.success("Expense deleted!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to delete expense")
                    
                    # Edit form (if edit button clicked)
                    if st.session_state.get(f"edit_expense_{expense['id']}", False):
                        with st.form(f"edit_form_{expense['id']}"):
                            edit_col1, edit_col2 = st.columns(2)
                            
                            with edit_col1:
                                edit_description = st.text_input("Description", value=expense['description'])
                                edit_amount = st.number_input("Amount", value=float(expense['amount']), min_value=0.01)
                            
                            with edit_col2:
                                edit_date = st.date_input("Date", value=pd.to_datetime(expense['date']).date())
                                categories = get_categories()
                                current_cat_index = categories.index(expense['category']) if expense['category'] in categories else 0
                                edit_category = st.selectbox("Category", categories, index=current_cat_index)
                            
                            edit_col1, edit_col2 = st.columns(2)
                            with edit_col1:
                                if st.form_submit_button("💾 Update"):
                                    update_data = {
                                        "description": edit_description,
                                        "amount": edit_amount,
                                        "date": edit_date.isoformat(),
                                        "category": edit_category
                                    }
                                    
                                    update_response = make_api_request(
                                        f"/expenses/{expense['id']}", 
                                        method="PUT", 
                                        data=update_data
                                    )
                                    
                                    if update_response and update_response['status'] == 'success':
                                        st.success("Expense updated!")
                                        st.session_state[f"edit_expense_{expense['id']}"] = False
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Failed to update expense")
                            
                            with edit_col2:
                                if st.form_submit_button("❌ Cancel"):
                                    st.session_state[f"edit_expense_{expense['id']}"] = False
                                    st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("No expenses found for the selected filters")

# CASH MANAGEMENT PAGE
elif current_page == "Cash Management":
    st.header("💰 Cash Management")
    
    # Get current cash balance
    settings_response = make_api_request("/settings")
    current_balance = 0
    if settings_response and settings_response['status'] == 'success':
        current_balance = settings_response['data'].get('cash_balance', 0)
    
    # Display current balance
    st.metric("💵 Current Cash Balance", format_currency(current_balance))
    
    # Add/Remove Cash
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("➕ Add Cash")
        with st.form("add_cash_form"):
            add_amount = st.number_input("Amount to Add", min_value=0.01, step=0.01)
            add_description = st.text_input("Description", placeholder="e.g., ATM withdrawal")
            add_date = st.date_input("Date", value=date.today())
            
            if st.form_submit_button("💰 Add Cash", type="primary"):
                if add_amount > 0:
                    cash_data = {
                        "type": "add",
                        "amount": add_amount,
                        "description": add_description,
                        "date": add_date.isoformat()
                    }
                    
                    response = make_api_request("/cashout", method="POST", data=cash_data)
                    
                    if response and response['status'] == 'success':
                        st.success(f"✅ Added {format_currency(add_amount)} to cash balance!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to add cash")
                else:
                    st.error("❌ Please enter a valid amount")
    
    with col2:
        st.subheader("➖ Remove Cash")
        with st.form("remove_cash_form"):
            remove_amount = st.number_input("Amount to Remove", min_value=0.01, step=0.01, max_value=current_balance)
            remove_description = st.text_input("Description", placeholder="e.g., Cash payment")
            remove_date = st.date_input("Date", value=date.today(), key="remove_date")
            
            if st.form_submit_button("💸 Remove Cash", type="secondary"):
                if remove_amount > 0:
                    if remove_amount <= current_balance:
                        cash_data = {
                            "type": "remove",
                            "amount": remove_amount,
                            "description": remove_description,
                            "date": remove_date.isoformat()
                        }
                        
                        response = make_api_request("/cashout", method="POST", data=cash_data)
                        
                        if response and response['status'] == 'success':
                            st.success(f"✅ Removed {format_currency(remove_amount)} from cash balance!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to remove cash")
                    else:
                        st.error("❌ Insufficient cash balance")
                else:
                    st.error("❌ Please enter a valid amount")
    
    # Cash Transaction History
    st.subheader("📋 Cash Transaction History")
    
    cashout_response = make_api_request("/cashout")
    
    if cashout_response and cashout_response['status'] == 'success':
        history_data = cashout_response['data']['history']
        
        if history_data:
            history_df = pd.DataFrame(history_data)
            
            # Format the display
            for idx, transaction in history_df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    
                    with col1:
                        st.write(f"**{transaction['description']}**")
                    with col2:
                        amount_str = f"+{format_currency(transaction['amount'])}" if transaction['type'] == 'add' else f"-{format_currency(transaction['amount'])}"
                        color = "green" if transaction['type'] == 'add' else "red"
                        st.markdown(f"<span style='color: {color}; font-weight: bold'>{amount_str}</span>", unsafe_allow_html=True)
                    with col3:
                        st.write(transaction['type'].title())
                    with col4:
                        st.write(transaction['date'])
                    
                    st.markdown("---")
        else:
            st.info("No cash transactions found")

# ANALYTICS PAGE
elif current_page == "Analytics":
    st.header("📈 Analytics & Insights")
    
    # Date range selector for analytics
    col1, col2 = st.columns(2)
    with col1:
        analysis_start_date = st.date_input("Analysis Start Date", value=date.today() - timedelta(days=180))
    with col2:
        analysis_end_date = st.date_input("Analysis End Date", value=date.today())
    
    # Monthly Savings Analysis
    st.subheader("💰 Monthly Savings Analysis")
    
    current_date = datetime.now()
    monthly_savings = make_api_request(
        "/analytics/monthly-savings", 
        params={"year": current_date.year, "month": current_date.month}
    )
    
    if monthly_savings and monthly_savings['status'] == 'success':
        data = monthly_savings['data']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Monthly Income", format_currency(data['income']))
        with col2:
            st.metric("Monthly Expenses", format_currency(data['expense']))
        with col3:
            savings_delta = f"{data['savings_rate']:.1f}% savings rate"
            st.metric("Monthly Savings", format_currency(data['savings']), delta=savings_delta)
    
    # Category Analysis
    st.subheader("📊 Category-wise Analysis")
    
    category_response = make_api_request("/analytics/category-analysis", params={
        "year": current_date.year, 
        "month": current_date.month
    })
    
    if category_response and category_response['status'] == 'success':
        category_data = category_response['data']
        
        if category_data:
            category_df = pd.DataFrame(category_data)
            
            # Create two columns for different views
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart view
                st.write("**Expense Distribution**")
                pie_chart_response = make_api_request("/charts/pie-chart", params={
                    "year": current_date.year, 
                    "month": current_date.month
                })
                
                if pie_chart_response and pie_chart_response['status'] == 'success':
                    chart_data = pie_chart_response['data']['chart']
                    st.markdown(f'<img src="{chart_data}" style="width:100%">', unsafe_allow_html=True)
            
            with col2:
                # Table view
                st.write("**Category Details**")
                display_df = category_df.copy()
                display_df['total_amount'] = display_df['total_amount'].apply(format_currency)
                display_df['avg_per_transaction'] = (category_df['total_amount'] / category_df['count']).apply(format_currency)
                
                st.dataframe(
                    display_df[['category', 'total_amount', 'count', 'avg_per_transaction']],
                    column_config={
                        "category": "Category",
                        "total_amount": "Total Amount",
                        "count": "Transactions",
                        "avg_per_transaction": "Avg per Transaction"
                    },
                    use_container_width=True
                )
    
    # Spending Trends
    st.subheader("📈 Spending Trends")
    
    spending_chart_response = make_api_request("/charts/monthly-spending", params={"months": 6})
    
    if spending_chart_response and spending_chart_response['status'] == 'success':
        chart_data = spending_chart_response['data']['chart']
        st.markdown(f'<img src="{chart_data}" style="width:100%">', unsafe_allow_html=True)
    
    # Savings Trend
    st.subheader("💹 Savings Trend")
    
    savings_trend_response = make_api_request("/charts/savings-trend", params={"months": 6})
    
    if savings_trend_response and savings_trend_response['status'] == 'success':
        chart_data = savings_trend_response['data']['chart']
        st.markdown(f'<img src="{chart_data}" style="width:100%">', unsafe_allow_html=True)
    
    # Predictions
    st.subheader("🔮 Expense Predictions")
    
    prediction_response = make_api_request("/analytics/predict-expense")
    
    if prediction_response and prediction_response['status'] == 'success':
        predicted_amount = prediction_response['data']['predicted_amount']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Predicted Next Month Expense", format_currency(predicted_amount))
        with col2:
            # Compare with current month
            if monthly_savings and monthly_savings['status'] == 'success':
                current_expense = monthly_savings['data']['expense']
                difference = predicted_amount - current_expense
                delta_text = f"{format_currency(abs(difference))} {'increase' if difference > 0 else 'decrease'}"
                st.metric("Compared to Current Month", format_currency(difference), delta=delta_text)

# GOALS PAGE
elif current_page == "Goals":
    st.header("🎯 Financial Goals")
    
    # Add New Goal
    with st.expander("➕ Add New Financial Goal", expanded=False):
        with st.form("add_goal_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                goal_name = st.text_input("Goal Name*", placeholder="e.g., New Car")
                target_amount = st.number_input("Target Amount*", min_value=1.0, step=100.0)
            
            with col2:
                target_date = st.date_input("Target Date*", min_value=date.today())
                saved_amount = st.number_input("Already Saved", min_value=0.0, step=100.0)
            
            if st.form_submit_button("🎯 Add Goal", type="primary"):
                if goal_name and target_amount > 0:
                    goal_data = {
                        "goal_name": goal_name,
                        "target_amount": target_amount,
                        "target_date": target_date.isoformat(),
                        "saved_amount": saved_amount
                    }
                    
                    response = make_api_request("/goals", method="POST", data=goal_data)
                    
                    if response and response['status'] == 'success':
                        st.success("✅ Goal added successfully!")
                        goal_plan = response['data']['goal_plan']
                        
                        st.info(f"""
                        📊 **Goal Analysis:**
                        - Monthly savings required: {format_currency(goal_plan['monthly_required'])}
                        - Months remaining: {goal_plan['months_remaining']}
                        - Feasibility: {goal_plan['feasibility']}
                        """)
                        
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Failed to add goal")
                else:
                    st.error("❌ Please fill all required fields")
    
    # Display Goals
    goals_response = make_api_request("/goals")
    
    if goals_response and goals_response['status'] == 'success':
        goals_data = goals_response['data']
        
        if goals_data:
            st.subheader("📋 Your Financial Goals")
            
            for goal in goals_data:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**🎯 {goal['goal_name']}**")
                        
                        # Progress bar
                        progress = (goal['saved_amount'] / goal['target_amount']) * 100 if goal['target_amount'] > 0 else 0
                        st.progress(progress / 100)
                        st.write(f"Progress: {progress:.1f}% ({format_currency(goal['saved_amount'])} / {format_currency(goal['target_amount'])})")
                    
                    with col2:
                        st.write("**Target Date**")
                        st.write(goal['target_date'])
                        
                        st.write("**Monthly Required**")
                        st.write(format_currency(goal['monthly_savings']))
                    
                    with col3:
                        if st.button("📊 View Plan", key=f"plan_{goal['id']}"):
                            plan_response = make_api_request(f"/goals/{goal['id']}/plan")
                            
                            if plan_response and plan_response['status'] == 'success':
                                plan = plan_response['data']['plan']
                                
                                st.write("**📊 Detailed Plan:**")
                                st.write(f"- Remaining amount: {format_currency(plan['remaining_amount'])}")
                                st.write(f"- Monthly required: {format_currency(plan['monthly_required'])}")
                                st.write(f"- Current savings capacity: {format_currency(plan['current_savings_capacity'])}")
                                st.write(f"- Feasibility: {plan['feasibility']}")
                                
                                if plan['monthly_required'] > plan['current_savings_capacity']:
                                    st.warning("⚠️ You may need to increase income or reduce expenses to meet this goal.")
                                else:
                                    st.success("✅ This goal is achievable with your current savings capacity!")
                        
                        if st.button("💰 Update Savings", key=f"update_{goal['id']}"):
                            st.session_state[f"update_goal_{goal['id']}"] = True
                    
                    # Update savings form
                    if st.session_state.get(f"update_goal_{goal['id']}", False):
                        with st.form(f"update_savings_form_{goal['id']}"):
                            new_saved_amount = st.number_input(
                                "New Saved Amount", 
                                value=float(goal['saved_amount']), 
                                min_value=0.0,
                                step=100.0
                            )
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("💾 Update"):
                                    # This would require an update goal endpoint
                                    st.success("Savings updated! (Note: Update goal endpoint needed)")
                                    st.session_state[f"update_goal_{goal['id']}"] = False
                            
                            with col2:
                                if st.form_submit_button("❌ Cancel"):
                                    st.session_state[f"update_goal_{goal['id']}"] = False
                                    st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("No financial goals set yet. Add your first goal above!")

# SETTINGS PAGE
elif current_page == "Settings":
    st.header("⚙️ Settings")
    
    # Get current settings
    settings_response = make_api_request("/settings")
    current_settings = {}
    
    if settings_response and settings_response['status'] == 'success':
        current_settings = settings_response['data']
    
    # User Settings Form
    st.subheader("👤 User Settings")
    
    with st.form("settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            monthly_income = st.number_input(
                "Monthly Income",
                value=float(current_settings.get('monthly_income', 50000)),
                min_value=0.0,
                step=1000.0,
                help="Your average monthly income"
            )
        
        with col2:
            cash_balance = st.number_input(
                "Current Cash Balance",
                value=float(current_settings.get('cash_balance', 10000)),
                min_value=0.0,
                step=100.0,
                help="Current cash in hand"
            )
        
        if st.form_submit_button("💾 Save Settings", type="primary"):
            settings_data = {
                "monthly_income": monthly_income,
                "cash_balance": cash_balance
            }
            
            response = make_api_request("/settings", method="POST", data=settings_data)
            
            if response and response['status'] == 'success':
                st.success("✅ Settings updated successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Failed to update settings")
    
    st.markdown("---")
    
    # Data Management
    st.subheader("📊 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Sample Data**")
        if st.button("📥 Load Sample Data"):
            # This would load the sample CSV data
            st.info("Sample data loading functionality would be implemented here")
    
    with col2:
        st.write("**Export Data**")
        if st.button("📤 Export Expenses"):
            # Get all expenses for export
            all_expenses = make_api_request("/expenses", params={"limit": 10000})
            
            if all_expenses and all_expenses['status'] == 'success':
                expenses_df = pd.DataFrame(all_expenses['data'])
                
                if not expenses_df.empty:
                    csv = expenses_df.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name=f"expenses_export_{date.today().isoformat()}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No expenses to export")
            else:
                st.error("Failed to fetch expenses for export")
    
    st.markdown("---")
    
    # System Information
    st.subheader("ℹ️ System Information")
    
    # API Health Check
    health_response = make_api_request("/health")
    
    if health_response and health_response['status'] == 'healthy':
        st.success("✅ API Status: Healthy")
        st.write(f"Last checked: {health_response['timestamp']}")
    else:
        st.error("❌ API Status: Unhealthy")
    
    # Category Information
    st.write("**Available Categories:**")
    categories = get_categories()
    st.write(", ".join(categories))
    
    # Tips and Help
    st.markdown("---")
    st.subheader("💡 Tips & Help")
    
    with st.expander("🤖 AI Category Detection"):
        st.write("""
        The app uses AI to automatically detect expense categories based on descriptions:
        
        - **Food**: Restaurant names, food items, grocery stores
        - **Transport**: Uber, taxi, bus, metro, fuel
        - **Entertainment**: Movies, Netflix, gaming, gym
        - **Shopping**: Amazon, Flipkart, clothes, electronics
        - **Healthcare**: Hospital, doctor, pharmacy, medicine
        - **Utilities**: Electricity, water, internet, phone bills
        - **Rent**: House rent, apartment, maintenance
        - **Education**: Books, courses, school fees
        - **Personal Care**: Salon, grooming, cosmetics
        
        If the AI is not confident, you can manually select the category.
        """)
    
    with st.expander("📊 Understanding Your Analytics"):
        st.write("""
        **Savings Rate**: Percentage of income saved each month
        - **Good**: 20% or higher ✅
        - **Average**: 10-20% ⚠️
        - **Needs Improvement**: Below 10% ❌
        
        **Category Analysis**: Shows where your money is going
        - Use this to identify areas where you can cut expenses
        - Aim to keep discretionary spending (entertainment, shopping) under control
        
        **Spending Trends**: Monthly comparison to track improvements
        - Green bars indicate you're within budget
        - Red bars show overspending months
        """)
    
    with st.expander("🎯 Setting Financial Goals"):
        st.write("""
        **Tips for Setting Realistic Goals:**
        
        1. **Emergency Fund**: 6 months of expenses
        2. **Short-term Goals**: Vacation, gadgets (3-12 months)
        3. **Medium-term Goals**: Car, wedding (1-5 years)
        4. **Long-term Goals**: House, retirement (5+ years)
        
        **Making Goals Achievable:**
        - Set specific target amounts and dates
        - Break large goals into smaller milestones
        - Review and adjust monthly savings as needed
        - Track progress regularly
        """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        💰 Personal Expense Tracker | Built with Streamlit & Flask | 
        <a href='#' style='color: #1f77b4;'>Need Help?</a>
    </div>
    """, 
    unsafe_allow_html=True
)