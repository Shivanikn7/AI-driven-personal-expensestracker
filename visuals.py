
import matplotlib
# Set the backend to 'Agg' which doesn't require a GUI
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import base64
from io import BytesIO
import pandas as pd
import numpy as np
from datetime import datetime
import seaborn as sns

# Set the style for better looking plots
plt.style.use('default')
sns.set_palette("husl")

class ChartGenerator:
    """Generate various charts for expense tracking"""

    def __init__(self):
        # Set default figure parameters
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['font.size'] = 10
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
    
    def _fig_to_base64(self, fig):
        """Convert matplotlib figure to base64 string for embedding in HTML"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)  # Close the figure to free memory
        return f"data:image/png;base64,{image_base64}"
    
    def _create_empty_chart(self, message="No data available"):
        """Create an empty chart with a message when no data is available"""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=14)
        ax.set_axis_off()
        return self._fig_to_base64(fig)
    
    def create_pie_chart(self, data, title="Category Distribution", figsize=(8, 6)):
        """Create a pie chart for expense categories"""
        if data.empty:
            return self._create_empty_chart("No data available for pie chart")
            
        fig, ax = plt.subplots(figsize=figsize)
        
        # Prepare data
        categories = data['category'].tolist()
        amounts = data['total_amount'].tolist()
        colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            amounts,
            labels=None,  # We'll add a legend instead
            autopct='%1.1f%%',
            startangle=90,
            shadow=False,
            colors=colors,
            wedgeprops={'edgecolor': 'w', 'linewidth': 1}
        )
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        
        # Add title
        plt.title(title, fontsize=16, pad=20)
        
        # Add legend
        plt.legend(
            wedges, 
            categories,
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )
        
        # Set font color for percentage labels
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
        
        # Add total in center
        total_amount = sum(amounts)
        ax.text(0, 0, f'Total\n₹{total_amount:,.2f}',
                ha='center', va='center', fontsize=12, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))
        
        return self._fig_to_base64(fig)
    
    def create_monthly_spending_bar_chart(self, spending_data, budget_data=None, title="Monthly Spending", figsize=(10, 6)):
        """Create a bar chart comparing monthly spending with budget"""
        if spending_data.empty:
            return self._create_empty_chart("No spending data available")
            
        fig, ax = plt.subplots(figsize=figsize)
        
        # Prepare data
        months = spending_data['month'].tolist()
        amounts = spending_data['total_amount'].tolist()
        
        # Format month labels (e.g., "2023-01" to "Jan 2023")
        month_labels = [datetime.strptime(month, '%Y-%m').strftime('%b %Y') for month in months]
        
        # Create bar chart
        x = np.arange(len(months))
        bar_width = 0.35
        
        # Spending bars
        spending_colors = ['red' if budget_data is not None and i < len(budget_data) and amounts[i] > budget_data.iloc[i]['budget']
                           else 'green' for i in range(len(amounts))]
        
        bars = ax.bar(
            x - bar_width/2 if budget_data is not None else x, 
            amounts, 
            bar_width, 
            label='Spending',
            color=spending_colors,
            alpha=0.8
        )
        
        # Budget line if available
        if budget_data is not None and not budget_data.empty:
            budget = budget_data['budget'].tolist()
            budget_bars = ax.bar(
                x + bar_width/2, 
                budget,
                bar_width, 
                label='Budget',
                color='blue',
                alpha=0.6
            )
            
            # Add value labels on budget bars
            for i, bar in enumerate(budget_bars):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height + max(amounts) * 0.01,
                        f'₹{height:,.0f}', ha='center', va='bottom', fontsize=8)
        
        # Add value labels on spending bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f'₹{int(height):,}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', 
                va='bottom',
                fontsize=9
            )
        
        # Add labels and title
        ax.set_xlabel('Month', fontweight='bold')
        ax.set_ylabel('Amount (₹)', fontweight='bold')
        ax.set_title(title, fontsize=16, pad=20)
        
        # Set x-axis ticks
        ax.set_xticks(x)
        ax.set_xticklabels(month_labels, rotation=45)
        
        # Add legend
        ax.legend()
        
        # Add grid
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def create_savings_trend_chart(self, data, title="Savings Trend", figsize=(10, 6)):
        """Create a line chart showing savings trend over time"""
        if data.empty:
            return self._create_empty_chart("No savings data available")
            
        fig, ax = plt.subplots(figsize=figsize)
        
        # Prepare data
        months = data['month']
        savings = data['savings']
        
        # Format month labels
        month_labels = []
        for month_str in months:
            year, month = month_str.split('-')
            month_name = pd.to_datetime(f"{year}-{month}-01").strftime('%b %Y')
            month_labels.append(month_name)
        
        # Create line chart
        ax.plot(
            month_labels, 
            savings, 
            'o-', 
            linewidth=2,
            color='blue'
        )
        
        # Fill area under the line
        ax.fill_between(
            month_labels, 
            savings, 
            color='lightblue', 
            alpha=0.4
        )
        
        # Add labels and title
        ax.set_xlabel('Month', fontweight='bold')
        ax.set_ylabel('Savings Amount (₹)', fontweight='bold')
        ax.set_title(title, fontsize=16, pad=20)
        
        # Rotate x-axis labels
        plt.xticks(rotation=45)
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add value labels
        for i, value in enumerate(savings):
            ax.annotate(
                f'₹{int(value):,}',
                xy=(i, value),
                xytext=(0, 10),
                textcoords="offset points",
                ha='center',
                fontsize=9
            )
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
        
    def create_category_spending_bar_chart(self, data, title="Category-wise Spending", figsize=(12, 8)):
        """Create a horizontal bar chart for category spending"""
        if data.empty:
            return self._create_empty_chart("No category data available")
            
        fig, ax = plt.subplots(figsize=figsize)
        data_sorted = data.sort_values('total_amount', ascending=True)
        categories = data_sorted['category'].tolist()
        amounts = data_sorted['total_amount'].tolist()
        colors = plt.cm.viridis(np.linspace(0, 1, len(categories)))

        bars = ax.barh(categories, amounts, color=colors, alpha=0.8)
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + max(amounts) * 0.01, bar.get_y() + bar.get_height() / 2.,
                    f'₹{width:,.0f}', ha='left', va='center', fontweight='bold')

        ax.set_xlabel('Amount (₹)', fontweight='bold')
        ax.set_ylabel('Category', fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='x')
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
        plt.tight_layout()
        return self._fig_to_base64(fig)
        
    def create_daily_spending_chart(self, daily_data, title="Daily Spending Pattern", figsize=(14, 8)):
        """Create a line chart for daily spending patterns"""
        if daily_data.empty:
            return self._create_empty_chart("No daily spending data available")
            
        fig, ax = plt.subplots(figsize=figsize)
        dates = pd.to_datetime(daily_data['date'])
        amounts = daily_data['total_amount'].tolist()

        ax.plot(dates, amounts, marker='o', linewidth=2, markersize=4, color='purple', alpha=0.8)
        ax.fill_between(dates, amounts, alpha=0.3, color='purple')

      
        # Add trend line if we have enough data points
        if len(dates) > 3:
            z = np.polyfit(range(len(dates)), amounts, 1)
            p = np.poly1d(z)
            ax.plot(dates, p(range(len(dates))), "r--", linewidth=1, alpha=0.8, label="Trend")
            
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Add labels and title
        ax.set_xlabel('Date', fontweight='bold')
        ax.set_ylabel('Amount (₹)', fontweight='bold')
        ax.set_title(title, fontsize=16, pad=20)
        
        # Add grid
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
        
        # Rotate x-axis labels
        plt.xticks(rotation=45)
        
        # Add value labels
        for i, (date, amount) in enumerate(zip(dates, amounts)):
            ax.annotate(
                f'₹{int(amount):,}',
                xy=(date, amount),
                xytext=(0, 10),
                textcoords="offset points",
                ha='center',
                fontsize=8
            )
        
        plt.tight_layout()
        return self._fig_to_base64(fig)

# Initialize chart generator
chart_generator = ChartGenerator()  # Add trend line if we have enough data points