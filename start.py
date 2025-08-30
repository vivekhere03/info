#!/usr/bin/env python3
"""
Unified startup script for free hosting platforms
Combines admin panel and proxy management in one service
"""
import os
import sys
import threading
import time
import subprocess
from flask import Flask

# Import our existing app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app, init_db

def start_proxy_server():
    """Start the mitmdump proxy server in background"""
    try:
        # Wait a bit for the main app to start
        time.sleep(5)
        
        print("🔄 Starting proxy server...")
        # Start mitmdump with minimal output
        subprocess.run([
            'mitmdump', 
            '-s', 'bypass.py', 
            '--listen-port', '8080',
            '--set', 'confdir=~/.mitmproxy',
            '--quiet'
        ])
    except Exception as e:
        print(f"❌ Proxy server error: {e}")

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    print("🚀 Starting UID Bypass Service...")
    print("📱 Admin Panel: Available on main port")
    print("🔧 Proxy Server: Starting on port 8080")
    
    # Start proxy server in background thread
    proxy_thread = threading.Thread(target=start_proxy_server, daemon=True)
    proxy_thread.start()
    
    # Get port from environment
    port = int(os.environ.get('PORT', 5000))
    
    # Start Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )