#!/usr/bin/env python3
import os
import sys
import subprocess

def run_test_lab():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_script = os.path.join(root_dir, "tools/test_lab/backend.py")
    
    print("🚀 Starting LYNK Test Lab...")
    print("📍 Access it at: http://localhost:8000")
    print("----------------------------------------")
    
    # Check dependencies
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print("⚠️  Missing dependencies. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])

    # Run the backend
    try:
        subprocess.check_call([sys.executable, backend_script])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped.")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")

if __name__ == "__main__":
    run_test_lab()
