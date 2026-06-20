"""Entry point for the Multi-Agent Travel Planning System."""
import subprocess
import sys
import os

if __name__ == "__main__":
    ui_path = os.path.join(os.path.dirname(__file__), "ui", "streamlit_app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", ui_path], check=True)
