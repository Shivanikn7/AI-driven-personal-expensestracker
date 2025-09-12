#!/usr/bin/env python3
"""
Personal Expense Tracker - Application Launcher
This script helps you start both the Flask API and Streamlit frontend
"""

import subprocess
import sys
import time
import os
import threading
from pathlib import Path

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'streamlit', 'flask', 'flask-cors', 'pandas', 
        'numpy', 'matplotlib', 'seaborn', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print("   pip install -r requirements.txt\n")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def start_flask_api():
    """Start the Flask API server"""
    print("🚀 Starting Flask API server...")
    try:
        # Import here to avoid import errors if dependencies are missing
        from database import db_manager
        
        # Initialize database
        print("📊 Initializing database...")
        
        # Load sample data if database is empty
        expenses_count = db_manager.execute_query("SELECT COUNT(*) as count FROM expenses")
        if expenses_count.iloc[0]['count'] == 0:
            print("📥 Loading sample data...")
            success = db_manager.load_sample_data('sample_expenses.csv')
            if success:
                print("✅ Sample data loaded successfully!")
            else:
                print("⚠️ Sample data file not found. You can add expenses manually.")
        
        # Start Flask app
        from api import app
        print("🌐 Flask API starting on http://localhost:5000")
        app.run(debug=False, port=5000, use_reloader=False)
        
    except Exception as e:
        print(f"❌ Error starting Flask API: {str(e)}")
        sys.exit(1)

def start_streamlit_app():
    """Start the Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")
    try:
        # Wait a bit for Flask to start
        time.sleep(3)
        
        # Start Streamlit
        print("🌐 Streamlit app starting on http://localhost:8501")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], 
                      check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Streamlit: {str(e)}")
    except KeyboardInterrupt:
        print("\n🛑 Streamlit stopped by user")

def main():
    """Main function to orchestrate the application startup"""
    print("💰 Personal Expense Tracker - Application Launcher")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app.py").exists() or not Path("api.py").exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   Make sure app.py and api.py are in the current directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("\n🎯 Starting the expense tracker application...")
    print("   - Flask API will start on: http://localhost:5000")
    print("   - Streamlit app will start on: http://localhost:8501")
    print("   - Press Ctrl+C to stop both servers\n")
    
    try:
        # Start Flask API in a separate thread
        flask_thread = threading.Thread(target=start_flask_api, daemon=True)
        flask_thread.start()
        
        # Wait a moment for Flask to start
        time.sleep(2)
        
        # Start Streamlit in main thread
        start_streamlit_app()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down expense tracker...")
        print("✅ Thank you for using Personal Expense Tracker!")

if __name__ == "__main__":
    main()