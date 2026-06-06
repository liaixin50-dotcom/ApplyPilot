#!/usr/bin/env python3
"""
ApplyPilot Web Application - Main Entry Point
Deploys the full Streamlit application on Vercel
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point for the application."""
    print("🚀 ApplyPilot AI Job Application Assistant")
    print("=" * 50)
    
    # Check if we're in a Vercel environment
    is_vercel = os.environ.get("VERCEL") == "1"
    
    if is_vercel:
        print("🌐 Running in Vercel environment")
        print("📊 Starting Streamlit application...")
        
        # Set up environment for Streamlit
        os.environ["STREAMLIT_SERVER_PORT"] = "8080"
        os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
        os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
        
        # Run the Streamlit app
        streamlit_app_path = Path(__file__).parent / "web_app" / "frontend" / "streamlit_app.py"
        
        if streamlit_app_path.exists():
            print(f"📁 Found Streamlit app: {streamlit_app_path}")
            
            # Start Streamlit server
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                str(streamlit_app_path),
                "--server.port", "8080",
                "--server.address", "0.0.0.0",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ]
            
            print(f"▶️  Starting: {' '.join(cmd)}")
            
            try:
                # Run the Streamlit server
                process = subprocess.Popen(cmd)
                print("✅ Streamlit server started successfully")
                print("🌍 Your application should be available at the Vercel URL")
                
                # Keep the process running
                process.wait()
                
            except Exception as e:
                print(f"❌ Error starting Streamlit: {e}")
                return 1
        else:
            print(f"❌ Streamlit app not found at: {streamlit_app_path}")
            print("📁 Available files in web_app/frontend/:")
            frontend_dir = Path(__file__).parent / "web_app" / "frontend"
            if frontend_dir.exists():
                for file in frontend_dir.iterdir():
                    print(f"  - {file.name}")
            return 1
    else:
        print("💻 Local development mode")
        print("📋 To run the full application locally:")
        print("   1. cd web_app/frontend")
        print("   2. streamlit run streamlit_app.py")
        print("\n🚀 To deploy to Vercel:")
        print("   1. Push this code to GitHub")
        print("   2. Go to https://vercel.com")
        print("   3. Import your repository")
        print("   4. Deploy!")
        
        # Offer to start the app locally
        response = input("\n▶️  Start the Streamlit app locally? (y/n): ")
        if response.lower() == 'y':
            streamlit_app_path = Path(__file__).parent / "web_app" / "frontend" / "streamlit_app.py"
            if streamlit_app_path.exists():
                print(f"🚀 Starting Streamlit app: {streamlit_app_path}")
                os.chdir(streamlit_app_path.parent)
                subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
            else:
                print("❌ Streamlit app not found")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())