"""Vercel Serverless Function for ApplyPilot.
This serves as a proxy to Streamlit Cloud or provides a lightweight web interface.
"""

from http.server import BaseHTTPRequestHandler
import json
import os

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ApplyPilot - AI Job Application Assistant</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 2rem;
                    line-height: 1.6;
                    color: #333;
                }
                .header {
                    text-align: center;
                    margin-bottom: 3rem;
                }
                .logo {
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: #2563eb;
                    margin-bottom: 1rem;
                }
                .tagline {
                    font-size: 1.2rem;
                    color: #666;
                    margin-bottom: 2rem;
                }
                .card {
                    background: #f8fafc;
                    border-radius: 12px;
                    padding: 2rem;
                    margin-bottom: 2rem;
                    border: 1px solid #e2e8f0;
                }
                .card h2 {
                    margin-top: 0;
                    color: #1e293b;
                }
                .features {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 1.5rem;
                    margin: 2rem 0;
                }
                .feature {
                    background: white;
                    padding: 1.5rem;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .feature h3 {
                    margin-top: 0;
                    color: #2563eb;
                }
                .cta-button {
                    display: inline-block;
                    background: #2563eb;
                    color: white;
                    padding: 1rem 2rem;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    margin-top: 1rem;
                    transition: background 0.2s;
                }
                .cta-button:hover {
                    background: #1d4ed8;
                }
                .deployment-links {
                    display: flex;
                    gap: 1rem;
                    flex-wrap: wrap;
                    margin-top: 2rem;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">📋 ApplyPilot</div>
                <div class="tagline">AI-powered Job Application Assistant</div>
                <p>Applied to 1,000 jobs in 2 days. Fully autonomous. Open source.</p>
            </div>
            
            <div class="card">
                <h2>What It Does</h2>
                <p>ApplyPilot is a 6-stage autonomous job application pipeline. It discovers jobs across 5+ boards, scores them against your resume with AI, tailors your resume per job, writes cover letters, and submits applications for you.</p>
                
                <div class="features">
                    <div class="feature">
                        <h3>🔍 Job Discovery</h3>
                        <p>Finds relevant jobs across multiple job boards automatically.</p>
                    </div>
                    <div class="feature">
                        <h3>📊 AI Scoring</h3>
                        <p>Scores jobs against your resume using AI to find the best matches.</p>
                    </div>
                    <div class="feature">
                        <h3>✂️ Resume Tailoring</h3>
                        <p>Customizes your resume for each job application automatically.</p>
                    </div>
                    <div class="feature">
                        <h3>📝 Cover Letters</h3>
                        <p>Generates personalized cover letters for each application.</p>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Try ApplyPilot</h2>
                <p>For the full interactive experience with the Streamlit dashboard, please use one of these deployment options:</p>
                
                <div class="deployment-links">
                    <a href="https://share.streamlit.io" class="cta-button">🚀 Streamlit Cloud</a>
                    <a href="https://render.com" class="cta-button">☁️ Render.com</a>
                    <a href="https://railway.app" class="cta-button">🚂 Railway.app</a>
                </div>
                
                <p style="margin-top: 2rem;">
                    <strong>Quick local setup:</strong><br>
                    <code>pip install applypilot</code><br>
                    <code>applypilot init</code><br>
                    <code>applypilot run</code>
                </p>
            </div>
            
            <div class="card">
                <h2>Open Source</h2>
                <p>ApplyPilot is open source under the AGPL-3.0 license. Contribute, fork, or star the project on GitHub.</p>
                <a href="https://github.com/Pickle-Pixel/ApplyPilot" class="cta-button">⭐ GitHub Repository</a>
            </div>
            
            <footer style="text-align: center; margin-top: 3rem; color: #666; font-size: 0.9rem;">
                <p>© 2026 ApplyPilot Project. Created by Pickle-Pixel.</p>
            </footer>
        </body>
        </html>
        """
        
        self.wfile.write(html_content.encode('utf-8'))

# Vercel requires this to be callable
def handler(request, context):
    return Handler()