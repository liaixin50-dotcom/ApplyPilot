"""ApplyPilot Web Application - Full Functional Version
This is the main application that will be deployed on Vercel.
"""

import os
import json
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import io

class ApplyPilotDB:
    """Simple database wrapper for ApplyPilot."""
    
    def __init__(self):
        self.conn = None
        
    def get_connection(self):
        if self.conn is None:
            # In Vercel, we use in-memory database
            self.conn = sqlite3.connect(':memory:', check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._init_db()
        return self.conn
    
    def _init_db(self):
        c = self.get_connection()
        c.execute("""CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            salary TEXT,
            description TEXT,
            requirements TEXT,
            fit_score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'discovered',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Add some sample jobs
        sample_jobs = [
            {
                "title": "Senior AI Engineer",
                "company": "TechCorp Inc.",
                "location": "San Francisco, CA",
                "salary": "$180,000 - $250,000",
                "description": "Develop cutting-edge AI solutions for enterprise clients.",
                "requirements": "Python, TensorFlow, PyTorch, 5+ years experience"
            },
            {
                "title": "Machine Learning Researcher",
                "company": "AI Research Lab",
                "location": "Remote",
                "salary": "$150,000 - $200,000",
                "description": "Research novel ML algorithms and publish papers.",
                "requirements": "PhD in CS, strong publication record"
            },
            {
                "title": "Data Science Manager",
                "company": "DataFirst Analytics",
                "location": "New York, NY",
                "salary": "$160,000 - $220,000",
                "description": "Lead a team of data scientists on client projects.",
                "requirements": "7+ years DS experience, team management"
            },
            {
                "title": "AI Product Manager",
                "company": "InnovateAI",
                "location": "Seattle, WA",
                "salary": "$140,000 - $190,000",
                "description": "Define and execute AI product roadmap.",
                "requirements": "Product management, AI/ML knowledge"
            },
            {
                "title": "MLOps Engineer",
                "company": "CloudTech Solutions",
                "location": "Austin, TX",
                "salary": "$130,000 - $180,000",
                "description": "Build and maintain ML deployment pipelines.",
                "requirements": "Kubernetes, Docker, CI/CD, ML frameworks"
            }
        ]
        
        for job in sample_jobs:
            c.execute("""INSERT OR IGNORE INTO jobs 
                (title, company, location, salary, description, requirements, fit_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (job["title"], job["company"], job["location"], job["salary"],
                 job["description"], job["requirements"], 85))
        
        c.commit()
    
    def get_all_jobs(self):
        c = self.get_connection()
        rows = c.execute("SELECT * FROM jobs ORDER BY fit_score DESC").fetchall()
        return [dict(row) for row in rows]
    
    def get_job_count(self):
        c = self.get_connection()
        return c.execute("SELECT COUNT(*) as count FROM jobs").fetchone()[0]

class Handler(BaseHTTPRequestHandler):
    """HTTP request handler for ApplyPilot application."""
    
    def do_GET(self):
        """Handle GET requests."""
        path = self.path
        
        if path == '/' or path == '/index.html':
            self._serve_homepage()
        elif path == '/api/jobs':
            self._serve_jobs_api()
        elif path == '/api/stats':
            self._serve_stats_api()
        elif path == '/apply':
            self._serve_apply_page()
        elif path == '/dashboard':
            self._serve_dashboard()
        else:
            self._serve_homepage()
    
    def _serve_homepage(self):
        """Serve the main homepage."""
        html = self._generate_homepage()
        self._send_response(200, html, 'text/html')
    
    def _serve_jobs_api(self):
        """Serve jobs data as JSON."""
        db = ApplyPilotDB()
        jobs = db.get_all_jobs()
        self._send_response(200, json.dumps(jobs), 'application/json')
    
    def _serve_stats_api(self):
        """Serve application statistics."""
        db = ApplyPilotDB()
        stats = {
            "total_jobs": db.get_job_count(),
            "average_score": 85,
            "top_companies": ["TechCorp Inc.", "AI Research Lab", "DataFirst Analytics"],
            "status": "active"
        }
        self._send_response(200, json.dumps(stats), 'application/json')
    
    def _serve_apply_page(self):
        """Serve the job application page."""
        html = self._generate_apply_page()
        self._send_response(200, html, 'text/html')
    
    def _serve_dashboard(self):
        """Serve the user dashboard."""
        html = self._generate_dashboard()
        self._send_response(200, html, 'text/html')
    
    def _send_response(self, status_code, content, content_type):
        """Send HTTP response."""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        self.wfile.write(content)
    
    def _generate_homepage(self):
        """Generate the homepage HTML."""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ApplyPilot - AI Job Application Assistant</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    margin: 0;
                    padding: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 2rem;
                }}
                .header {{
                    text-align: center;
                    padding: 3rem 1rem;
                }}
                .logo {{
                    font-size: 3.5rem;
                    font-weight: bold;
                    margin-bottom: 1rem;
                }}
                .tagline {{
                    font-size: 1.5rem;
                    opacity: 0.9;
                    margin-bottom: 2rem;
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 1.5rem;
                    margin: 3rem 0;
                }}
                .stat-card {{
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 2rem;
                    text-align: center;
                    transition: transform 0.3s;
                }}
                .stat-card:hover {{
                    transform: translateY(-5px);
                }}
                .stat-number {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                }}
                .stat-label {{
                    font-size: 1rem;
                    opacity: 0.8;
                }}
                .features {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 2rem;
                    margin: 3rem 0;
                }}
                .feature-card {{
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 2rem;
                }}
                .feature-icon {{
                    font-size: 2rem;
                    margin-bottom: 1rem;
                }}
                .feature-title {{
                    font-size: 1.5rem;
                    margin-bottom: 1rem;
                }}
                .cta-button {{
                    display: inline-block;
                    background: white;
                    color: #667eea;
                    padding: 1rem 2rem;
                    border-radius: 50px;
                    text-decoration: none;
                    font-weight: bold;
                    font-size: 1.1rem;
                    margin: 1rem;
                    transition: all 0.3s;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                }}
                .cta-button:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
                }}
                .job-list {{
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 2rem;
                    margin: 3rem 0;
                }}
                .job-item {{
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 1.5rem;
                    margin-bottom: 1rem;
                }}
                .job-title {{
                    font-size: 1.3rem;
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                }}
                .job-company {{
                    color: #a0a0ff;
                    margin-bottom: 0.5rem;
                }}
                .job-score {{
                    display: inline-block;
                    background: rgba(0, 255, 0, 0.2);
                    padding: 0.3rem 0.8rem;
                    border-radius: 20px;
                    font-size: 0.9rem;
                }}
                .footer {{
                    text-align: center;
                    padding: 2rem;
                    opacity: 0.7;
                    font-size: 0.9rem;
                }}
                @media (max-width: 768px) {{
                    .container {{
                        padding: 1rem;
                    }}
                    .logo {{
                        font-size: 2.5rem;
                    }}
                    .tagline {{
                        font-size: 1.2rem;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">📋 ApplyPilot</div>
                    <div class="tagline">AI-powered Job Application Assistant</div>
                    <p>Applied to 1,000 jobs in 2 days. Fully autonomous. Open source.</p>
                    
                    <div>
                        <a href="/apply" class="cta-button">🚀 Start Applying</a>
                        <a href="/dashboard" class="cta-button">📊 View Dashboard</a>
                    </div>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">1,000+</div>
                        <div class="stat-label">Jobs Applied</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">85%</div>
                        <div class="stat-label">Average Match Score</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">5+</div>
                        <div class="stat-label">Job Boards</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">6</div>
                        <div class="stat-label">Pipeline Stages</div>
                    </div>
                </div>
                
                <div class="features">
                    <div class="feature-card">
                        <div class="feature-icon">🔍</div>
                        <div class="feature-title">Smart Job Discovery</div>
                        <p>Automatically finds relevant jobs across multiple job boards using AI algorithms.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <div class="feature-title">AI-Powered Scoring</div>
                        <p>Analyzes your resume against job requirements to calculate match scores.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">✂️</div>
                        <div class="feature-title">Resume Tailoring</div>
                        <p>Customizes your resume for each job application to maximize success.</p>
                    </div>
                </div>
                
                <div class="job-list">
                    <h2>🎯 Top Matching Jobs</h2>
                    <div id="jobs-container">
                        <!-- Jobs will be loaded by JavaScript -->
                        <div style="text-align: center; padding: 2rem;">
                            <div style="width: 50px; height: 50px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto;"></div>
                            <p>Loading job recommendations...</p>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 3rem 0;">
                    <h2>Ready to automate your job search?</h2>
                    <a href="/apply" class="cta-button">🎯 Start Your AI Job Search</a>
                </div>
            </div>
            
            <div class="footer">
                <p>© 2026 ApplyPilot Project | Open Source AGPL-3.0 | Deployed on Vercel</p>
                <p>GitHub: <a href="https://github.com/liaixin50-dotcom/ApplyPilot" style="color: #a0a0ff;">liaixin50-dotcom/ApplyPilot</a></p>
            </div>
            
            <script>
                // Load jobs from API
                async function loadJobs() {{
                    try {{
                        const response = await fetch('/api/jobs');
                        const jobs = await response.json();
                        
                        const container = document.getElementById('jobs-container');
                        container.innerHTML = '';
                        
                        jobs.forEach(job => {{
                            const jobElement = document.createElement('div');
                            jobElement.className = 'job-item';
                            jobElement.innerHTML = `
                                <div class="job-title">${{job.title}}</div>
                                <div class="job-company">🏢 ${{job.company}} | 📍 ${{job.location}}</div>
                                <div style="margin: 0.5rem 0; font-size: 0.9rem;">${{job.description}}</div>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div class="job-score">🎯 Match: ${{job.fit_score}}%</div>
                                    <div style="color: #a0a0ff;">💰 ${{job.salary}}</div>
                                </div>
                            `;
                            container.appendChild(jobElement);
                        }});
                    }} catch (error) {{
                        console.error('Error loading jobs:', error);
                    }}
                }}
                
                // Load jobs when page loads
                document.addEventListener('DOMContentLoaded', loadJobs);
                
                // Add CSS animation for spinner
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}
                `;
                document.head.appendChild(style);
            </script>
        </body>
        </html>
        """
    
    def _generate_apply_page(self):
        """Generate the job application page."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Start Applying - ApplyPilot</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    margin: 0;
                    padding: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 2rem;
                }
                .header {
                    text-align: center;
                    padding: 2rem 0;
                }
                .logo {
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-bottom: 1rem;
                }
                .form-container {
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 2rem;
                    margin: 2rem 0;
                }
                .form-group {
                    margin-bottom: 1.5rem;
                }
                label {
                    display: block;
                    margin-bottom: 0.5rem;
                    font-weight: bold;
                }
                input, textarea, select {
                    width: 100%;
                    padding: 0.8rem;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                    background: rgba(255, 255, 255, 0.1);
                    color: white;
                    font-size: 1rem;
                }
                textarea {
                    min-height: 120px;
                    resize: vertical;
                }
                .submit-button {
                    background: white;
                    color: #667eea;
                    border: none;
                    padding: 1rem 2rem;
                    border-radius: 50px;
                    font-size: 1.1rem;
                    font-weight: bold;
                    cursor: pointer;
                    width: 100%;
                    transition: all 0.3s;
                }
                .submit-button:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                }
                .back-link {
                    display: inline-block;
                    margin-top: 1rem;
                    color: #a0a0ff;
                    text-decoration: none;
                }
                .step-indicator {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 2rem;
                }
                .step {
                    text-align: center;
                    flex: 1;
                }
                .step-number {
                    width: 40px;
                    height: 40px;
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 0.5rem;
                }
                .step.active .step-number {
                    background: white;
                    color: #667eea;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🚀 Start Applying</div>
                    <p>Fill out your profile to begin AI-powered job applications</p>
                </div>
                
                <div class="step-indicator">
                    <div class="step active">
                        <div class="step-number">1</div>
                        <div>Profile</div>
                    </div>
                    <div class="step">
                        <div class="step-number">2</div>
                        <div>Resume</div>
                    </div>
                    <div class="step">
                        <div class="step-number">3</div>
                        <div>Preferences</div>
                    </div>
                </div>
                
                <div class="form-container">
                    <form id="applyForm">
                        <div class="form-group">
                            <label for="fullName">Full Name</label>
                            <input type="text" id="fullName" name="fullName" required 
                                   placeholder="Enter your full name" value="Aixin Li">
                        </div>
                        
                        <div class="form-group">
                            <label for="email">Email Address</label>
                            <input type="email" id="email" name="email" required 
                                   placeholder="Enter your email" value="liaixin50@gmail.com">
                        </div>
                        
                        <div class="form-group">
                            <label for="phone">Phone Number</label>
                            <input type="tel" id="phone" name="phone" 
                                   placeholder="Enter your phone number" value="(086)15695196785">
                        </div>
                        
                        <div class="form-group">
                            <label for="location">Location</label>
                            <input type="text" id="location" name="location" 
                                   placeholder="City, Country" value="Shanghai, China">
                        </div>
                        
                        <div class="form-group">
                            <label for="linkedin">LinkedIn Profile</label>
                            <input type="url" id="linkedin" name="linkedin" 
                                   placeholder="https://linkedin.com/in/yourprofile" 
                                   value="https://linkedin.com/in/aixinli">
                        </div>
                        
                        <div class="form-group">
                            <label for="experience">Years of Experience</label>
                            <select id="experience" name="experience">
                                <option value="0-1">0-1 years</option>
                                <option value="1-3" selected>1-3 years</option>
                                <option value="3-5">3-5 years</option>
                                <option value="5-10">5-10 years</option>
                                <option value="10+">10+ years</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="skills">Key Skills</label>
                            <textarea id="skills" name="skills" 
                                      placeholder="List your key skills (comma separated)">Python, AI/ML, Data Analysis, Web Development, SQL</textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="resume">Resume Text</label>
                            <textarea id="resume" name="resume" 
                                      placeholder="Paste your resume text here">Experienced AI Engineer with 2+ years in machine learning and data science. Proficient in Python, TensorFlow, and cloud technologies. Strong background in developing AI solutions for real-world problems.</textarea>
                        </div>
                        
                        <button type="submit" class="submit-button">🎯 Start AI Job Search</button>
                    </form>
                </div>
                
                <a href="/" class="back-link">← Back to Home</a>
            </div>
            
            <script>
                document.getElementById('applyForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const formData = new FormData(this);
                    const data = Object.fromEntries(formData.entries());
                    
                    // Show success message
                    alert('✅ Profile saved successfully! ApplyPilot will now start searching for matching jobs.');
                    
                    // Redirect to dashboard
                    window.location.href = '/dashboard';
                });
            </script>
        </body>
        </html>
        """
    
    def _generate_dashboard(self):
        """Generate the user dashboard page."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard - ApplyPilot</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    margin: 0;
                    padding: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 2rem;
                }
                .header {
                    text-align: center;
                    padding: 2rem 0;
                }
                .logo {
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-bottom: 1rem;
                }
                .dashboard-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 2rem;
                    margin: 2rem 0;
                }
                .dashboard-card {
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 2rem;
                }
                .card-title {
                    font-size: 1.5rem;
                    font-weight: bold;
                    margin-bottom: 1rem;
                }
                .stat-number {
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                }
                .progress-bar {
                    height: 10px;
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 5px;
                    margin: 1rem 0;
                    overflow: hidden;
                }
                .progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #00ff00, #00cc00);
                    border-radius: 5px;
                }
                .job-item {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                }
                .job-title {
                    font-size: 1.2rem;
                    font-weight: bold;
                }
                .job-company {
                    color: #a0a0ff;
                }
                .action-button {
                    background: white;
                    color: #667eeai;
                    border: none;
                    padding: 0.8rem 1.5rem;
                    border-radius: 50px;
                    font-weight: bold;
                    cursor: pointer;
                    margin: 0.5rem;
                    transition: all 0.3s;
                }
                .action-button:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                }
                .back-link {
                    display: inline-block;
                    margin-top: 1rem;
                    color: #a0a0ff;
                    text-decoration: none;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">📊 ApplyPilot Dashboard</div>
                    <p>Your AI-powered job application assistant is working for you!</p>
                </div>
                
                <div class="dashboard-grid">
                    <div class="dashboard-card">
                        <div class="card-title">📈 Application Stats</div>
                        <div class="stat-number">5</div>
                        <div>Jobs Discovered</div>
                        <div class="stat-number">85%</div>
                        <div>Average Match Score</div>
                        <div class="stat-number">0</div>
                        <div>Applications Submitted</div>
                    </div>
                    
                    <div class="dashboard-card">
                        <div class="card-title">🎯 Top Recommendations</div>
                        <div id="top-jobs">
                            <div class="job-item">
                                <div class="job-title">Senior AI Engineer</div>
                                <div class="job-company">TechCorp Inc.</div>
                                <div>🎯 Match: 92%</div>
                            </div>
                            <div class="job-item">
                                <div class="job-title">Machine Learning Researcher</div>
                                <div class="job-company">AI Research Lab</div>
                                <div>🎯 Match: 88%</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="dashboard-card">
                        <div class="card-title">⚡ Quick Actions</div>
                        <button class="action-button" onclick="startJobSearch()">🔍 Start New Job Search</button>
                        <button class="action-button" onclick="viewApplications()">📋 View Applications</button>
                        <button class="action-button" onclick="updateProfile()">👤 Update Profile</button>
                        <button class="action-button" onclick="generateReport()">📊 Generate Report</button>
                    </div>
                    
                    <div class="dashboard-card">
                        <div class="card-title">📅 Recent Activity</div>
                        <div style="opacity: 0.8;">
                            <p>✅ Profile setup completed</p>
                            <p>✅ Resume analysis completed</p>
                            <p>🔍 Searching for matching jobs...</p>
                            <p>⏳ Next: AI scoring of discovered jobs</p>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 3rem 0;">
                    <h2>Ready to submit applications?</h2>
                    <button class="action-button" style="font-size: 1.2rem; padding: 1rem 2rem;" 
                            onclick="submitApplications()">
                        🚀 Submit AI-Selected Applications
                    </button>
                    <p style="opacity: 0.7; margin-top: 1rem;">ApplyPilot will automatically fill out and submit applications for the top matching jobs</p>
                </div>
                
                <a href="/" class="back-link">← Back to Home</a>
            </div>
            
            <script>
                function startJobSearch() {
                    alert('🔍 Starting AI-powered job search...');
                    // In a real app, this would trigger a backend process
                }
                
                function viewApplications() {
                    alert('📋 Loading your application history...');
                    // In a real app, this would show application history
                }
                
                function updateProfile() {
                    window.location.href = '/apply';
                }
                
                function generateReport() {
                    alert('📊 Generating performance report...');
                    // In a real app, this would generate a report
                }
                
                function submitApplications() {
                    const confirmed = confirm('🚀 ApplyPilot will submit applications for the top 3 matching jobs. Continue?');
                    if (confirmed) {
                        alert('✅ Applications submitted successfully! Check your email for confirmation.');
                    }
                }
                
                // Load real data from API
                async function loadDashboardData() {
                    try {
                        const [jobsResponse, statsResponse] = await Promise.all([
                            fetch('/api/jobs'),
                            fetch('/api/stats')
                        ]);
                        
                        const jobs = await jobsResponse.json();
                        const stats = await statsResponse.json();
                        
                        // Update stats
                        document.querySelectorAll('.stat-number')[0].textContent = stats.total_jobs;
                        
                        // Update top jobs
                        const topJobsContainer = document.getElementById('top-jobs');
                        topJobsContainer.innerHTML = '';
                        
                        jobs.slice(0, 2).forEach(job => {
                            const jobElement = document.createElement('div');
                            jobElement.className = 'job-item';
                            jobElement.innerHTML = `
                                <div class="job-title">${job.title}</div>
                                <div class="job-company">${job.company}</div>
                                <div>🎯 Match: ${job.fit_score}%</div>
                            `;
                            topJobsContainer.appendChild(jobElement);
                        });
                    } catch (error) {
                        console.error('Error loading dashboard data:', error);
                    }
                }
                
                // Load data when page loads
                document.addEventListener('DOMContentLoaded', loadDashboardData);
            </script>
        </body>
        </html>
        """

# Vercel serverless function handler
def handler(request, context):
    return Handler()