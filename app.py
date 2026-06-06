"""ApplyPilot — AI Job Application Assistant (Vercel Deployment).

This is the main entry point for Vercel deployment.
It imports and runs the Streamlit app from the web_app/frontend directory.
"""

import os
import sys

# Add the web_app/frontend directory to the Python path
frontend_path = os.path.join(os.path.dirname(__file__), "web_app", "frontend")
sys.path.insert(0, frontend_path)

# Import the Streamlit app
try:
    from streamlit_app import main
except ImportError:
    # Fallback to the regular app if streamlit_app is not available
    from app import main

# Vercel requires a callable application
# Streamlit apps are typically run via command line, but we can create a simple wrapper
def handler(event, context):
    """Vercel serverless function handler."""
    # This is a placeholder - Streamlit doesn't work well with serverless functions
    # We'll need to use a different approach
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": "<html><body><h1>ApplyPilot AI Job Assistant</h1><p>Please use the Streamlit Cloud deployment for full functionality.</p></body></html>"
    }

# For local testing
if __name__ == "__main__":
    print("ApplyPilot - AI Job Application Assistant")
    print("For Vercel deployment, please use the web_app/frontend/streamlit_app.py file directly.")