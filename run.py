"""
run.py
------
Entry point CLI script to launch the Smart Blood Donation Streamlit dashboard.
Usage: python run.py
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "main.py")
    print("🩸 Starting Smart Blood Donation & Demand Forecaster...")
    print(f"📁 App: {app_path}")
    print("🌐 Opening at: http://localhost:8501")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path], check=True)
