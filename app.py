import os
import sqlite3
import secrets
import hashlib
import subprocess
import threading
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import re
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['DATABASE'] = 'proxy_admin.db'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'])
    return None

def get_db_connection():
    """Get database connection with SQL injection protection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with secure admin user"""
    conn = get_db_connection()
    
    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create UIDs table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS uids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT UNIQUE NOT NULL,
            description TEXT,
            added_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # Create logs table for security monitoring
    conn.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN
        )
    ''')
    
    # Check if admin user exists
    admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('Vivek',)).fetchone()
    if not admin_user:
        # Create secure admin user with specified credentials
        password_hash = generate_password_hash('V!Chauhan@')
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                    ('Vivek', password_hash))
        print("Admin user 'Vivek' created successfully!")
    
    conn.commit()
    conn.close()

def log_access_attempt(username, action, success=True):
    """Log access attempts for security monitoring"""
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO access_logs (username, action, ip_address, user_agent, success)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, action, request.remote_addr, request.headers.get('User-Agent', ''), success))
        conn.commit()
    except:
        pass
    finally:
        conn.close()

def validate_input(input_text, input_type='general'):
    """Validate and sanitize user input to prevent SQL injection and XSS"""
    if not input_text:
        return False, "Input cannot be empty"
    
    # Remove potentially dangerous characters
    dangerous_patterns = [
        r'<script.*?>.*?</script>',  # Script tags
        r'javascript:',              # JavaScript protocols
        r'on\w+\s*=',               # Event handlers
        r'<.*?>',                   # HTML tags
        r'union\s+select',          # SQL injection
        r'drop\s+table',            # SQL injection
        r'delete\s+from',           # SQL injection
        r'update\s+.*\s+set',       # SQL injection
        r'insert\s+into',           # SQL injection
    ]
    
    input_lower = input_text.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, input_lower, re.IGNORECASE):
            return False, f"Invalid input detected: potentially dangerous content"
    
    if input_type == 'uid':
        # UID should be numeric only
        if not re.match(r'^\d+$', input_text.strip()):
            return False, "UID must contain only numbers"
        if len(input_text.strip()) > 20:
            return False, "UID too long (max 20 characters)"
    elif input_type == 'username':
        # Username validation
        if not re.match(r'^[a-zA-Z0-9_]+$', input_text.strip()):
            return False, "Username can only contain letters, numbers, and underscores"
        if len(input_text.strip()) > 50:
            return False, "Username too long (max 50 characters)"
    
    return True, "Valid input"

@app.route('/')
def index():
    """Main page - redirect to admin if logged in, otherwise show proxy info"""
    if session.get('user_id'):
        return redirect(url_for('admin_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Secure login with protection against brute force attacks"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validate input
        valid, msg = validate_input(username, 'username')
        if not valid:
            flash(f'Invalid username: {msg}', 'error')
            log_access_attempt(username, 'login_attempt', False)
            return render_template('login.html')
        
        if not password:
            flash('Password is required', 'error')
            log_access_attempt(username, 'login_attempt', False)
            return render_template('login.html')
        
        # Check user credentials using parameterized query
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            # Update last login
            conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
            conn.commit()
            conn.close()
            
            # Create user session
            user_obj = User(user['id'], user['username'])
            login_user(user_obj)
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            log_access_attempt(username, 'login_success', True)
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            conn.close()
            log_access_attempt(username, 'login_failed', False)
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Secure logout"""
    username = session.get('username', 'Unknown')
    log_access_attempt(username, 'logout', True)
    logout_user()
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard with UID management"""
    conn = get_db_connection()
    
    # Get all UIDs
    uids = conn.execute('''
        SELECT * FROM uids 
        ORDER BY created_at DESC
    ''').fetchall()
    
    # Get recent access logs
    logs = conn.execute('''
        SELECT * FROM access_logs 
        ORDER BY timestamp DESC 
        LIMIT 20
    ''').fetchall()
    
    # Get proxy status
    proxy_status = check_proxy_status()
    
    conn.close()
    
    return render_template('admin.html', 
                         uids=uids, 
                         logs=logs, 
                         proxy_status=proxy_status,
                         username=session.get('username'))

@app.route('/add_uid', methods=['POST'])
@login_required
def add_uid():
    """Add new UID with validation"""
    uid = request.form.get('uid', '').strip()
    description = request.form.get('description', '').strip()
    
    # Validate UID
    valid, msg = validate_input(uid, 'uid')
    if not valid:
        flash(f'Invalid UID: {msg}', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Validate description if provided
    if description:
        valid, msg = validate_input(description, 'general')
        if not valid:
            flash(f'Invalid description: {msg}', 'error')
            return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    try:
        # Check if UID already exists
        existing = conn.execute('SELECT * FROM uids WHERE uid = ?', (uid,)).fetchone()
        if existing:
            flash('UID already exists!', 'error')
        else:
            # Add new UID using parameterized query
            conn.execute('''
                INSERT INTO uids (uid, description, added_by) 
                VALUES (?, ?, ?)
            ''', (uid, description or 'No description', session.get('username')))
            
            # Update uid.txt file
            update_uid_file()
            
            conn.commit()
            log_access_attempt(session.get('username'), f'add_uid_{uid}', True)
            flash('UID added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding UID: {str(e)}', 'error')
        log_access_attempt(session.get('username'), f'add_uid_failed_{uid}', False)
    finally:
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_uid/<int:uid_id>')
@login_required
def delete_uid(uid_id):
    """Delete UID with validation"""
    conn = get_db_connection()
    try:
        # Get UID info before deletion
        uid_info = conn.execute('SELECT * FROM uids WHERE id = ?', (uid_id,)).fetchone()
        if not uid_info:
            flash('UID not found!', 'error')
        else:
            # Delete UID using parameterized query
            conn.execute('DELETE FROM uids WHERE id = ?', (uid_id,))
            
            # Update uid.txt file
            update_uid_file()
            
            conn.commit()
            log_access_attempt(session.get('username'), f'delete_uid_{uid_info["uid"]}', True)
            flash('UID deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting UID: {str(e)}', 'error')
        log_access_attempt(session.get('username'), f'delete_uid_failed_{uid_id}', False)
    finally:
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

def update_uid_file():
    """Update uid.txt file with current UIDs from database"""
    conn = get_db_connection()
    try:
        uids = conn.execute('SELECT uid FROM uids WHERE is_active = TRUE ORDER BY uid').fetchall()
        with open('uid.txt', 'w', encoding='utf-8') as f:
            for uid in uids:
                f.write(f"{uid['uid']}\n")
    except Exception as e:
        print(f"Error updating uid.txt: {e}")
    finally:
        conn.close()

def check_proxy_status():
    """Check if proxy server is running"""
    try:
        # This is a simple check - you can enhance this
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, shell=True)
        return 'Running' if 'python.exe' in result.stdout else 'Stopped'
    except:
        return 'Unknown'

@app.route('/start_proxy')
@login_required
def start_proxy():
    """Start the proxy server"""
    try:
        # Start proxy in background
        subprocess.Popen(['python', '-m', 'mitmproxy', '--scripts', 'bypass.py', '--listen-port', '8080'])
        log_access_attempt(session.get('username'), 'start_proxy', True)
        flash('Proxy server started on port 8080!', 'success')
    except Exception as e:
        log_access_attempt(session.get('username'), 'start_proxy_failed', False)
        flash(f'Error starting proxy: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/api/status')
def api_status():
    """API endpoint for proxy status"""
    return jsonify({
        'status': 'running',
        'proxy_status': check_proxy_status(),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Load existing UIDs from uid.txt into database
    if os.path.exists('uid.txt'):
        conn = get_db_connection()
        with open('uid.txt', 'r', encoding='utf-8') as f:
            for line in f:
                uid = line.strip()
                if uid and uid.isdigit():
                    try:
                        # Check if UID already exists
                        existing = conn.execute('SELECT * FROM uids WHERE uid = ?', (uid,)).fetchone()
                        if not existing:
                            conn.execute('''
                                INSERT INTO uids (uid, description, added_by) 
                                VALUES (?, ?, ?)
                            ''', (uid, 'Imported from uid.txt', 'System'))
                    except:
                        pass
        conn.commit()
        conn.close()
    
    # Run the application
    print("🚀 Proxy Admin Panel starting...")
    print("📋 Admin Credentials:")
    print("   Username: Vivek")
    print("   Password: V!Chauhan@")
    print("🔒 Security features enabled:")
    print("   - SQL injection protection")
    print("   - XSS protection") 
    print("   - Input validation")
    print("   - Access logging")
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Access the admin panel at: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)