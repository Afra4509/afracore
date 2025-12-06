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
        'ipinfo': "isisendiri",  # Your ipinfo.io token
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
                        print(f"[+] Ngrok URL: {self.public_url}")
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
    
    def get_advanced_stats(self):
        """Get advanced analytics data"""
        with self.lock:
            c = self.conn.cursor()
            stats = {}
            
            # Flagged visits
            c.execute('SELECT COUNT(*) FROM visits WHERE flagged = 1')
            stats['flagged_visits'] = c.fetchone()[0]
            
            # Top ISPs
            c.execute('''SELECT isp, COUNT(*) as count 
                         FROM visits WHERE isp != "Unknown" 
                         GROUP BY isp ORDER BY count DESC LIMIT 5''')
            stats['top_isps'] = [dict(row) for row in c.fetchall()]
            
            # Top user agents
            c.execute('''SELECT user_agent, COUNT(*) as count 
                         FROM visits WHERE user_agent != "" 
                         GROUP BY user_agent ORDER BY count DESC LIMIT 5''')
            stats['top_ua'] = [dict(row) for row in c.fetchall()]
            
            # Return visitors (same IP, multiple sessions)
            c.execute('''SELECT ip_address, COUNT(DISTINCT session_id) as visits, 
                                COUNT(*) as total_hits
                         FROM visits GROUP BY ip_address 
                         HAVING COUNT(DISTINCT session_id) > 1 
                         ORDER BY total_hits DESC LIMIT 10''')
            stats['return_visitors'] = [dict(row) for row in c.fetchall()]
            
            # Last 24h by hour
            c.execute('''SELECT strftime('%H:00', timestamp) as hour, COUNT(*) as count
                         FROM visits WHERE timestamp > datetime('now', '-24 hours')
                         GROUP BY hour ORDER BY hour''')
            stats['hourly_24h'] = [dict(row) for row in c.fetchall()]
            
            # Countries with coordinates (for potential mapping)
            c.execute('''SELECT DISTINCT country, city, AVG(latitude) as lat, AVG(longitude) as lon, COUNT(*) as count
                         FROM visits WHERE latitude != 0 AND longitude != 0
                         GROUP BY country, city ORDER BY count DESC LIMIT 15''')
            stats['geo_data'] = [dict(row) for row in c.fetchall()]
            
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

# ===================== RATE LIMITING & SECURITY =====================
class RateLimiter:
    """Manage rate limiting with thread safety"""
    def __init__(self):
        self.limits = {}
        self.lock = threading.Lock()
    
    def check(self, ip_address, max_requests=30, window_seconds=60):
        """Check if IP is within rate limit"""
        if max_requests <= 0:
            return True
        
        current_time = time.time()
        with self.lock:
            if ip_address not in self.limits:
                self.limits[ip_address] = []
            
            # Clean old requests outside window
            self.limits[ip_address] = [
                t for t in self.limits[ip_address] 
                if current_time - t < window_seconds
            ]
            
            # Check if over limit
            if len(self.limits[ip_address]) >= max_requests:
                return False
            
            # Add current request
            self.limits[ip_address].append(current_time)
            return True
    
    def reset(self, ip_address=None):
        """Reset limits for IP or all IPs"""
        with self.lock:
            if ip_address:
                self.limits.pop(ip_address, None)
            else:
                self.limits.clear()

rate_limiter = RateLimiter()

# ===================== FLASK APPLICATION =====================
app = Flask(__name__)
app.secret_key = os.urandom(32)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template_string(
        '<html><body style="background:#0f172a; color:#e2e8f0; font-family:monospace; text-align:center; padding-top:100px;">'
        '<h1>404</h1><p>The page you are looking for does not exist.</p>'
        '<a href="/" style="color:#22c55e;">← Return to tracking page</a>'
        '</body></html>'
    ), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {error}")
    return render_template_string(
        '<html><body style="background:#0f172a; color:#e2e8f0; font-family:monospace; text-align:center; padding-top:100px;">'
        '<h1>500</h1><p>Internal server error occurred.</p>'
        '<a href="/login" style="color:#22c55e;">← Return to login</a>'
        '</body></html>'
    ), 500

# ===================== ROUTES =====================
@app.route('/')
def index():
    """Main tracking endpoint - Collects visitor information
    
    Performs the following:
    1. Validates client IP and security checks
    2. Rate limiting enforcement
    3. Bot/crawler detection
    4. Geolocation lookup
    5. Device fingerprinting collection
    6. Session tracking
    7. Returns processing page with redirect
    """
    try:
        client_ip = get_client_ip()
        
        # SECURITY: IP blocking
        if is_blocked_ip(client_ip):
            logger.warning(f"Blocked IP access: {client_ip}")
            return render_template_string(VICTIM_TEMPLATE, error="Access denied", redirect_url=CONFIG['redirect_url'], city="Unknown", country="Unknown", unique_id=""), 403
        
        # SECURITY: Rate limiting
        if not rate_limiter.check(client_ip, CONFIG['rate_limit_per_ip']):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return render_template_string(VICTIM_TEMPLATE, error="Too many requests", redirect_url=CONFIG['redirect_url'], city="Unknown", country="Unknown", unique_id=""), 429
        
        # DATA COLLECTION: User agent
        user_agent = request.user_agent.string if CONFIG['collect_user_agent'] else ''
        if is_blocked_user_agent(user_agent):
            logger.debug(f"Blocked bot/crawler: {user_agent[:50]}")
            return render_template_string(VICTIM_TEMPLATE, error="Access denied", redirect_url=CONFIG['redirect_url'], city="Unknown", country="Unknown", unique_id=""), 403
        
        # DATA COLLECTION: Referrer
        referrer = request.referrer if CONFIG['collect_referrer'] else ''
        if is_blocked_referrer(referrer):
            logger.debug(f"Blocked referrer: {referrer}")
            return render_template_string(VICTIM_TEMPLATE, error="Access denied", redirect_url=CONFIG['redirect_url'], city="Unknown", country="Unknown", unique_id=""), 403
        
        # TRACKING: Generate unique IDs
        unique_id = str(uuid.uuid4())
        session_id = request.cookies.get('shadow_session')
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # GEOLOCATION: Get location data
        geo_data = geolocator.get_location(client_ip)
        
        # PREPARE VISIT DATA
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
            'session_id': session_id,
            'flagged': 0
        }
        
        # FLAG SUSPICIOUS ACTIVITY
        if is_blocked_user_agent(user_agent) or is_blocked_referrer(referrer):
            visit_data['flagged'] = 1
        
        # SAVE TO DATABASE
        visit_id = db.add_visit(visit_data)
        
        if visit_id:
            location = f"{geo_data['city']}, {geo_data['country']}" if geo_data['success'] else "Unknown"
            logger.info(f"[+] Visit #{visit_id}: {client_ip} from {location} | Sessions: {request.cookies.get('shadow_session', 'NEW')[:8]}")
        
        # RESPONSE: Create tracking page with cookies
        response = make_response(render_template_string(
            VICTIM_TEMPLATE,
            redirect_url=CONFIG['redirect_url'],
            unique_id=unique_id,
            country=geo_data['country'],
            city=geo_data['city']
        ))
        
        # Set tracking cookies
        response.set_cookie(
            'shadow_session',
            session_id,
            max_age=2592000,  # 30 days
            httponly=True,
            samesite='Lax'
        )
        
        response.set_cookie(
            'tracking_id',
            unique_id,
            max_age=2592000,
            httponly=True,
            samesite='Lax'
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Tracking endpoint error: {e}", exc_info=True)
        return render_template_string(VICTIM_TEMPLATE, error="Processing error", redirect_url=CONFIG['redirect_url'], city="Unknown", country="Unknown", unique_id=""), 500

@app.route('/collect', methods=['POST'])
def collect():
    """Collect additional device fingerprint data via AJAX
    
    Expects JSON:
    {
        'unique_id': 'visitor-uuid',
        'fingerprint': {
            'browser': user agent,
            'platform': platform info,
            'timezone': timezone,
            'screen_width': width,
            'screen_height': height,
            ...
        }
    }
    """
    try:
        data = request.json
        unique_id = data.get('unique_id')
        
        if not unique_id:
            return jsonify({'status': 'error', 'message': 'No unique_id'}), 400
        
        if CONFIG['enable_fingerprinting']:
            # Find visit by unique_id
            c = db.conn.cursor()
            c.execute('SELECT id FROM visits WHERE unique_id = ?', (unique_id,))
            row = c.fetchone()
            
            if row:
                visit_id = row[0]
                fingerprint = data.get('fingerprint', {})
                db.add_fingerprint(visit_id, fingerprint)
                logger.debug(f"Fingerprint collected for visit {visit_id}")
                return jsonify({'status': 'success'})
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Collection error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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

@app.route('/api/advanced-stats')
def api_advanced_stats():
    """API endpoint for advanced analytics"""
    if not check_admin_session():
        return jsonify({'error': 'Unauthorized'}), 401
    
    stats = db.get_advanced_stats()
    return jsonify(stats)

@app.route('/api/visits')
def api_visits():
    """API endpoint to get filtered visits"""
    if not check_admin_session():
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Query parameters for filtering
    limit = request.args.get('limit', 100, type=int)
    country = request.args.get('country')
    ip = request.args.get('ip')
    
    c = db.conn.cursor()
    
    # Build query
    query = 'SELECT * FROM visits WHERE 1=1'
    params = []
    
    if country:
        query += ' AND country = ?'
        params.append(country)
    
    if ip:
        query += ' AND ip_address = ?'
        params.append(ip)
    
    query += ' ORDER BY timestamp DESC LIMIT ?'
    params.append(limit)
    
    c.execute(query, params)
    columns = [col[0] for col in c.description]
    visits = [dict(zip(columns, row)) for row in c.fetchall()]
    
    return jsonify({'status': 'success', 'visits': visits, 'count': len(visits)})

@app.route('/api/search')
def api_search():
    """Search visits by IP, country, or domain"""
    if not check_admin_session():
        return jsonify({'error': 'Unauthorized'}), 401
    
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'error': 'Query too short'}), 400
    
    c = db.conn.cursor()
    
    # Search in IP, country, city, ISP
    search_pattern = f'%{query}%'
    c.execute('''SELECT * FROM visits 
                 WHERE ip_address LIKE ? OR country LIKE ? OR city LIKE ? OR isp LIKE ?
                 ORDER BY timestamp DESC LIMIT 50''',
             (search_pattern, search_pattern, search_pattern, search_pattern))
    
    columns = [col[0] for col in c.description]
    results = [dict(zip(columns, row)) for row in c.fetchall()]
    
    return jsonify({'status': 'success', 'results': results, 'count': len(results)})

@app.route('/api/block-ip', methods=['POST'])
def api_block_ip():
    """Block an IP address (add to blacklist)"""
    if not check_admin_session():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    ip_address = data.get('ip')
    
    if not ip_address:
        return jsonify({'error': 'No IP provided'}), 400
    
    # Add to blocked list in config (would need persistence)
    logger.warning(f"IP blocked: {ip_address}")
    return jsonify({'status': 'success', 'message': f'IP {ip_address} blocked'})

@app.route('/api/stats-by-country')
def api_stats_by_country():
    """Get detailed stats for a specific country"""
    if not check_admin_session():
        return jsonify({'error': 'Unauthorized'}), 401
    
    country = request.args.get('country')
    if not country:
        return jsonify({'error': 'No country specified'}), 400
    
    c = db.conn.cursor()
    
    # Country stats
    c.execute('''SELECT COUNT(*) as visits, COUNT(DISTINCT ip_address) as unique_ips,
                        COUNT(DISTINCT city) as cities, AVG(latitude) as avg_lat, AVG(longitude) as avg_lon
                 FROM visits WHERE country = ?''', (country,))
    country_stats = dict(zip([col[0] for col in c.description], c.fetchone()))
    
    # Top cities in country
    c.execute('''SELECT city, COUNT(*) as count FROM visits WHERE country = ?
                 GROUP BY city ORDER BY count DESC LIMIT 10''', (country,))
    top_cities = [dict(row) for row in c.fetchall()]
    
    return jsonify({
        'status': 'success',
        'country': country,
        'stats': country_stats,
        'top_cities': top_cities
    })

# ===================== TEMPLATES =====================
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SHADOW CORE - Admin Login</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Poppins:wght@400;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: #0f172a;
            font-family: 'Poppins', sans-serif;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            color: #e2e8f0;
        }
        
        /* Advanced animated background */
        .bg-elements {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            overflow: hidden;
        }
        
        /* Floating mesh network background */
        .mesh-bg {
            position: absolute;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 45%, rgba(59, 130, 246, 0.03) 45%, rgba(59, 130, 246, 0.03) 55%, transparent 55%, transparent);
            background-size: 100px 100px;
            animation: meshShift 20s linear infinite;
            opacity: 0.5;
        }
        
        @keyframes meshShift {
            0% { transform: translate(0, 0); }
            100% { transform: translate(100px, 100px); }
        }
        
        /* Animated particles */
        .particles {
            position: absolute;
            width: 100%;
            height: 100%;
        }
        
        .particle {
            position: absolute;
            width: 2px;
            height: 2px;
            background: rgba(59, 130, 246, 0.5);
            border-radius: 50%;
            animation: particleFloat 20s infinite;
            opacity: 0.6;
        }
        
        @keyframes particleFloat {
            0% {
                transform: translateY(0) translateX(0) scale(1);
                opacity: 0;
            }
            10% {
                opacity: 0.8;
            }
            90% {
                opacity: 0.8;
            }
            100% {
                transform: translateY(-100vh) translateX(100px) scale(0.5);
                opacity: 0;
            }
        }
        
        /* Liquid blob backgrounds */
        .blob {
            position: absolute;
            filter: blur(80px);
            opacity: 0.15;
            mix-blend-mode: screen;
            border-radius: 50%;
        }
        
        .blob-1 {
            width: 500px;
            height: 500px;
            background: linear-gradient(135deg, #3b82f6, #06b6d4);
            top: -100px;
            right: -100px;
            animation: blobShift1 8s ease-in-out infinite;
        }
        
        .blob-2 {
            width: 400px;
            height: 400px;
            background: linear-gradient(135deg, #22c55e, #3b82f6);
            bottom: -50px;
            left: -50px;
            animation: blobShift2 10s ease-in-out infinite;
        }
        
        .blob-3 {
            width: 350px;
            height: 350px;
            background: linear-gradient(135deg, #a855f7, #06b6d4);
            top: 50%;
            right: 10%;
            animation: blobShift3 12s ease-in-out infinite;
        }
        
        @keyframes blobShift1 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(-50px, 50px) scale(1.1); }
        }
        
        @keyframes blobShift2 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(50px, -50px) scale(0.9); }
        }
        
        @keyframes blobShift3 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(30px, 30px) scale(1.05); }
        }
        
        /* Animated gradient lines */
        .gradient-line {
            position: absolute;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(34, 197, 94, 0.8), transparent);
            width: 300px;
            animation: gradientSlide 3s ease-in-out infinite;
        }
        
        .line-1 {
            top: 20%;
            left: 0;
            animation-delay: 0s;
        }
        
        .line-2 {
            bottom: 30%;
            right: 0;
            animation: gradientSlide 3s ease-in-out infinite reverse;
            animation-delay: 1s;
        }
        
        .line-3 {
            top: 60%;
            left: 50%;
            animation-delay: 0.5s;
        }
        
        @keyframes gradientSlide {
            0% { transform: translateX(-100%); opacity: 0; }
            50% { opacity: 1; }
            100% { transform: translateX(100vw); opacity: 0; }
        }
        
        .container {
            position: relative;
            z-index: 10;
            max-width: 480px;
            padding: 30px;
        }
        
        .login-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 20px;
            padding: 60px 45px;
            box-shadow: 
                0 25px 60px rgba(0, 0, 0, 0.5),
                inset 0 0 60px rgba(59, 130, 246, 0.05),
                0 0 40px rgba(59, 130, 246, 0.15);
            position: relative;
            overflow: hidden;
            animation: cardFloat 3s ease-in-out infinite;
        }
        
        @keyframes cardFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
        }
        
        /* Card shine effect */
        .login-card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent 30%,
                rgba(255, 255, 255, 0.1) 50%,
                transparent 70%
            );
            animation: shimmer 3s ease-in-out infinite;
            pointer-events: none;
        }
        
        @keyframes shimmer {
            0% { transform: translate(-100%, -100%) rotate(45deg); }
            100% { transform: translate(100%, 100%) rotate(45deg); }
        }
        
        /* Card glow effect */
        .login-card::after {
            content: '';
            position: absolute;
            top: -1px;
            left: -1px;
            right: -1px;
            bottom: -1px;
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.5), rgba(59, 130, 246, 0.5), rgba(168, 85, 247, 0.5), rgba(34, 197, 94, 0.5));
            border-radius: 20px;
            opacity: 0;
            z-index: -1;
            animation: cardGlow 3s ease-in-out infinite;
            filter: blur(10px);
        }
        
        @keyframes cardGlow {
            0%, 100% { opacity: 0; }
            50% { opacity: 0.3; }
        }
        
        .logo-section {
            text-align: center;
            margin-bottom: 50px;
            position: relative;
            z-index: 2;
        }
        
        .logo-icon {
            font-size: 48px;
            margin-bottom: 15px;
            background: linear-gradient(135deg, #3b82f6, #22c55e, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: iconPulse 2s ease-in-out infinite, iconRotate 8s linear infinite;
            display: inline-block;
        }
        
        @keyframes iconPulse {
            0%, 100% { filter: drop-shadow(0 0 5px rgba(34, 197, 94, 0.3)); }
            50% { filter: drop-shadow(0 0 20px rgba(34, 197, 94, 0.8)); }
        }
        
        @keyframes iconRotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .logo-text {
            font-size: 36px;
            font-weight: 700;
            background: linear-gradient(135deg, #3b82f6, #22c55e, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            letter-spacing: 2px;
            animation: textGlow 2s ease-in-out infinite;
        }
        
        @keyframes textGlow {
            0%, 100% { text-shadow: 0 0 10px rgba(34, 197, 94, 0.2); }
            50% { text-shadow: 0 0 20px rgba(34, 197, 94, 0.6), 0 0 30px rgba(59, 130, 246, 0.4); }
        }
        
        .logo-subtext {
            font-size: 12px;
            color: #94a3b8;
            margin-top: 10px;
            letter-spacing: 2px;
            text-transform: uppercase;
            opacity: 0;
            animation: fadeIn 1s ease-out 0.5s forwards;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .form-group {
            margin-bottom: 28px;
            position: relative;
            z-index: 2;
            opacity: 0;
            animation: slideInUp 0.8s ease-out 0.3s forwards;
        }
        
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .input-label {
            display: block;
            font-size: 12px;
            color: #3b82f6;
            margin-bottom: 10px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(30, 41, 59, 0.7);
            border: 2px solid rgba(59, 130, 246, 0.3);
            border-radius: 10px;
            color: #e2e8f0;
            font-size: 14px;
            font-family: 'JetBrains Mono', monospace;
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            backdrop-filter: blur(10px);
            position: relative;
        }
        
        input::placeholder {
            color: #64748b;
        }
        
        input:focus {
            outline: none;
            border-color: #22c55e;
            background: rgba(34, 197, 94, 0.08);
            box-shadow: 
                0 0 0 3px rgba(34, 197, 94, 0.1),
                0 0 20px rgba(34, 197, 94, 0.3),
                inset 0 0 20px rgba(34, 197, 94, 0.08);
            transform: translateY(-2px);
        }
        
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            border: none;
            border-radius: 10px;
            color: white;
            font-size: 14px;
            font-weight: 700;
            font-family: 'Poppins', sans-serif;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            z-index: 2;
            box-shadow: 0 8px 20px rgba(34, 197, 94, 0.3);
            opacity: 0;
            animation: slideInUp 0.8s ease-out 0.4s forwards;
            overflow: hidden;
        }
        
        button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        button:hover {
            transform: translateY(-4px);
            box-shadow: 0 15px 40px rgba(34, 197, 94, 0.5);
            background: linear-gradient(135deg, #16a34a, #15803d);
        }
        
        button:hover::before {
            width: 300px;
            height: 300px;
        }
        
        button:active {
            transform: translateY(-2px);
        }
        
        .error {
            color: #ef4444;
            margin-top: 25px;
            text-align: center;
            font-size: 13px;
            background: rgba(239, 68, 68, 0.15);
            border: 1.5px solid rgba(239, 68, 68, 0.5);
            padding: 14px;
            border-radius: 10px;
            position: relative;
            z-index: 2;
            backdrop-filter: blur(10px);
            animation: shake 0.5s ease-in-out, slideInUp 0.8s ease-out;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        .footer {
            color: #94a3b8;
            font-size: 11px;
            text-align: center;
            margin-top: 30px;
            position: relative;
            z-index: 2;
            letter-spacing: 1px;
            font-family: 'JetBrains Mono', monospace;
            opacity: 0;
            animation: fadeIn 1s ease-out 1s forwards;
        }
        
        .footer span {
            opacity: 0.7;
            display: block;
            margin-top: 10px;
            font-size: 10px;
        }
        
        @media (max-width: 480px) {
            .login-card { 
                padding: 40px 25px;
                border-radius: 16px;
            }
            .logo-text { font-size: 28px; }
            .container { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="bg-elements">
        <div class="mesh-bg"></div>
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
        <div class="gradient-line line-1"></div>
        <div class="gradient-line line-2"></div>
        <div class="gradient-line line-3"></div>
        <div class="particles" id="particles"></div>
    </div>
    
    <div class="container">
        <div class="login-card">
            <div class="logo-section">
                <div class="logo-icon">⚡</div>
                <h1 class="logo-text">SHADOW</h1>
                <div class="logo-subtext">Authentication Required</div>
            </div>
            
            <form method="POST" action="/login">
                <div class="form-group">
                    <label class="input-label"><i class="fas fa-lock"></i> Access Code</label>
                    <input type="password" name="password" placeholder="Enter your access code" required autofocus>
                </div>
                
                <button type="submit"><i class="fas fa-sign-in-alt"></i> Authenticate</button>
            </form>
            
            {% if error %}
            <div class="error"><i class="fas fa-exclamation-circle"></i> {{ error }}</div>
            {% endif %}
            
            <div class="footer">
                v2.0 | ngrok optimized | secure
                <span>© 2025 AFRAFDHMA</span>
            </div>
        </div>
    </div>
    
    <script>
        // Generate particle background
        function createParticles() {
            const container = document.getElementById('particles');
            const particleCount = 30;
            
            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 20 + 's';
                particle.style.animationDuration = (15 + Math.random() * 10) + 's';
                container.appendChild(particle);
            }
        }
        
        createParticles();
        
        // Enhanced button ripple effect
        const button = document.querySelector('button');
        if (button) {
            button.addEventListener('click', function(e) {
                const ripple = document.createElement('span');
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = x + 'px';
                ripple.style.top = y + 'px';
            });
        }
        
        // Add input focus animation trigger
        const input = document.querySelector('input');
        if (input) {
            input.addEventListener('focus', function() {
                this.style.animation = 'none';
                setTimeout(() => {
                    this.style.animation = '';
                }, 10);
            });
        }
    </script>
</body>
</html>
"""

VICTIM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Processing...</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Poppins:wght@400;600;700&display=swap');
        
        * { 
            margin: 0;
            padding: 0;
            box-sizing: border-box; 
        }
        
        body {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #0f172a 50%, #1a1f3a 100%);
            background-size: 400% 400%;
            animation: gradientShift 8s ease infinite;
            font-family: 'Poppins', sans-serif;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            color: #e2e8f0;
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        /* Animated background elements */
        .bg-elements {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            overflow: hidden;
        }
        
        .glow-orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(60px);
        }
        
        .orb-1 {
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.2), transparent);
            top: -100px;
            right: -100px;
            animation: float 8s ease-in-out infinite;
        }
        
        .orb-2 {
            width: 250px;
            height: 250px;
            background: radial-gradient(circle, rgba(34, 197, 94, 0.15), transparent);
            bottom: -80px;
            left: -80px;
            animation: float 10s ease-in-out infinite reverse;
        }
        
        .orb-3 {
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(168, 85, 247, 0.1), transparent);
            top: 50%;
            right: 10%;
            animation: float 12s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(30px); }
        }
        
        /* Grid background */
        .grid {
            position: absolute;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(59, 130, 246, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(59, 130, 246, 0.05) 1px, transparent 1px);
            background-size: 50px 50px;
            opacity: 0.5;
        }
        
        .container {
            position: relative;
            z-index: 10;
            text-align: center;
            max-width: 700px;
            padding: 30px;
        }
        
        /* Card styling */
        .card {
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 20px;
            padding: 50px 40px;
            box-shadow: 
                0 25px 50px rgba(0, 0, 0, 0.3),
                inset 0 0 60px rgba(59, 130, 246, 0.05);
            animation: slideUp 0.8s ease-out;
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(34, 197, 94, 0.1), transparent);
            border-radius: 50%;
            animation: pulse 3s ease-in-out infinite;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.1; }
            50% { transform: scale(1.1); opacity: 0.15; }
        }
        
        /* Loader animation */
        .loader {
            position: relative;
            width: 60px;
            height: 60px;
            margin: 0 auto 40px;
        }
        
        .loader::before {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border: 3px solid transparent;
            border-top-color: #3b82f6;
            border-right-color: #22c55e;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            box-shadow: inset 0 0 20px rgba(59, 130, 246, 0.3);
        }
        
        .loader::after {
            content: '';
            position: absolute;
            width: 80%;
            height: 80%;
            top: 10%;
            left: 10%;
            border: 2px solid transparent;
            border-bottom-color: #a855f7;
            border-left-color: #06b6d4;
            border-radius: 50%;
            animation: spin 2s linear infinite reverse;
            box-shadow: inset 0 0 20px rgba(168, 85, 247, 0.2);
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Text styling */
        h1 {
            font-size: 42px;
            font-weight: 700;
            background: linear-gradient(135deg, #3b82f6, #22c55e, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 15px 0;
            letter-spacing: 2px;
            text-shadow: 0 0 30px rgba(59, 130, 246, 0.2);
            animation: fadeIn 0.8s ease-in 0.2s both;
            position: relative;
            z-index: 1;
        }
        
        .subtitle {
            font-size: 16px;
            color: #cbd5e0;
            margin-bottom: 35px;
            animation: fadeIn 0.8s ease-in 0.4s both;
            position: relative;
            z-index: 1;
            letter-spacing: 1px;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        /* Info section */
        .info-section {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(34, 197, 94, 0.05));
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 15px;
            padding: 30px;
            margin: 30px 0;
            animation: slideUp 0.8s ease-out 0.6s both;
            position: relative;
            z-index: 1;
            backdrop-filter: blur(10px);
        }
        
        .info-header {
            font-size: 13px;
            color: #3b82f6;
            font-weight: 600;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .info-header::before {
            content: '';
            width: 2px;
            height: 20px;
            background: linear-gradient(180deg, #3b82f6, transparent);
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
        }
        
        .info-item {
            text-align: left;
        }
        
        .info-label {
            font-size: 11px;
            color: #64748b;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        
        .info-value {
            font-size: 14px;
            color: #e2e8f0;
            font-weight: 600;
            word-break: break-all;
            font-family: 'JetBrains Mono', monospace;
            color: #22c55e;
        }
        
        .redirect-box {
            margin-top: 40px;
            animation: slideUp 0.8s ease-out 0.8s both;
            position: relative;
            z-index: 1;
        }
        
        .countdown {
            font-size: 18px;
            color: #3b82f6;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 10px;
            animation: pulse 1s ease-in-out infinite;
        }
        
        .redirect-text {
            font-size: 14px;
            color: #cbd5e0;
            margin-bottom: 15px;
        }
        
        .progress-bar {
            width: 100%;
            height: 3px;
            background: rgba(59, 130, 246, 0.1);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 15px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3b82f6, #22c55e, #06b6d4);
            animation: progress 3s ease-out forwards;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }
        
        @keyframes progress {
            0% { width: 0%; }
            100% { width: 100%; }
        }
        
        .footer {
            margin-top: 30px;
            font-size: 11px;
            color: #64748b;
            letter-spacing: 1px;
            animation: fadeIn 1s ease-in 1s both;
            position: relative;
            z-index: 1;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .card { padding: 40px 25px; }
            h1 { font-size: 32px; }
            .subtitle { font-size: 14px; }
            .info-grid { grid-template-columns: 1fr 1fr; }
            .container { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="bg-elements">
        <div class="grid"></div>
        <div class="glow-orb orb-1"></div>
        <div class="glow-orb orb-2"></div>
        <div class="glow-orb orb-3"></div>
    </div>
    
    <div class="container">
        <div class="card">
            <div class="loader"></div>
            
            <h1>⚡ Processing</h1>
            <p class="subtitle">Initializing secure connection</p>
            
            <div class="info-section">
                <div class="info-header">
                    <i class="fas fa-lock"></i> Session Information
                </div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">📍 Location</div>
                        <div class="info-value">{{ city }}, {{ country }}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">🔐 Session</div>
                        <div class="info-value">{{ unique_id[:12] }}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">✓ Status</div>
                        <div class="info-value" style="color: #22c55e;">Connected</div>
                    </div>
                </div>
            </div>
            
            <div class="redirect-box">
                <div class="countdown" id="countdown">3</div>
                <p class="redirect-text">Redirecting to destination in <strong id="timer">3</strong> seconds...</p>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
            </div>
            
            <div class="footer">
                © 2025 • Processing Complete • All Systems Nominal
            </div>
        </div>
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
        
        // Countdown timer
        let timeLeft = 3;
        const countdownEl = document.getElementById('countdown');
        const timerEl = document.getElementById('timer');
        
        const interval = setInterval(() => {
            timeLeft--;
            if (countdownEl) countdownEl.textContent = timeLeft;
            if (timerEl) timerEl.textContent = timeLeft;
            
            if (timeLeft <= 0) {
                clearInterval(interval);
                window.location.href = '{{ redirect_url }}';
            }
        }, 1000);
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
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Poppins:wght@400;600;700&display=swap');
        
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --border: #1e293b;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --accent-green: #22c55e;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-purple: #a855f7;
            --accent-orange: #f59e0b;
            --accent-red: #ef4444;
        }
        
        * { box-sizing: border-box; }
        
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            color: var(--text-primary);
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
            line-height: 1.6;
        }
        
        /* Loading Screen */
        .loading-screen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            animation: loadingFadeOut 0.6s ease-out 2.5s forwards;
            pointer-events: none;
        }
        
        @keyframes loadingFadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        
        .loading-container {
            text-align: center;
            position: relative;
        }
        
        .loading-icon {
            font-size: 72px;
            margin-bottom: 30px;
            background: linear-gradient(135deg, #22c55e, #3b82f6, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: spinPulse 2s ease-in-out infinite;
            display: inline-block;
        }
        
        @keyframes spinPulse {
            0% { transform: rotate(0deg) scale(1); filter: drop-shadow(0 0 5px rgba(34, 197, 94, 0.3)); }
            50% { transform: rotate(180deg) scale(1.1); filter: drop-shadow(0 0 20px rgba(34, 197, 94, 0.8)); }
            100% { transform: rotate(360deg) scale(1); filter: drop-shadow(0 0 5px rgba(34, 197, 94, 0.3)); }
        }
        
        .loading-text {
            font-size: 20px;
            font-weight: 700;
            color: var(--accent-cyan);
            margin-bottom: 25px;
            letter-spacing: 3px;
            text-transform: uppercase;
            animation: textFlicker 1.5s ease-in-out infinite;
        }
        
        @keyframes textFlicker {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        
        .loading-dots {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-top: 15px;
        }
        
        .dot {
            width: 12px;
            height: 12px;
            background: var(--accent-green);
            border-radius: 50%;
            box-shadow: 0 0 15px var(--accent-green);
            animation: dotBounce 1.4s infinite;
        }
        
        .dot:nth-child(1) { animation-delay: 0s; }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes dotBounce {
            0%, 100% { transform: translateY(0) scale(1); opacity: 0.6; }
            50% { transform: translateY(-15px) scale(1.2); opacity: 1; }
        }
        
        .loading-bar {
            width: 200px;
            height: 3px;
            background: rgba(59, 130, 246, 0.2);
            border-radius: 10px;
            margin: 25px auto 0;
            overflow: hidden;
        }
        
        .loading-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-green), var(--accent-blue), var(--accent-cyan));
            border-radius: 10px;
            animation: barFill 2.5s ease-in-out infinite;
        }
        
        @keyframes barFill {
            0% { width: 0%; }
            50% { width: 100%; }
            100% { width: 100%; }
        }
        
        .container {
            max-width: 1800px;
            margin: 0 auto;
            padding: 30px 20px;
        }
        
        .header {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(51, 65, 85, 0.6));
            backdrop-filter: blur(20px);
            padding: 35px;
            border-radius: 18px;
            margin-bottom: 35px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 25px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3), inset 0 0 60px rgba(59, 130, 246, 0.05);
            animation: slideDown 0.6s ease-out;
        }
        
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .header-left h1 {
            margin: 0;
            font-size: 40px;
            font-weight: 800;
            background: linear-gradient(135deg, #3b82f6, #22c55e, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: 2px;
        }
        
        .header-info {
            color: var(--text-secondary);
            font-size: 13px;
            margin-top: 12px;
            display: flex;
            gap: 25px;
            flex-wrap: wrap;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .header-info span {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: var(--accent-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
            box-shadow: 0 0 15px var(--accent-green);
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; box-shadow: 0 0 15px var(--accent-green); }
            50% { opacity: 0.5; box-shadow: 0 0 25px var(--accent-green); }
        }
        
        .header-right {
            text-align: right;
            color: var(--text-secondary);
            font-size: 13px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .header-right > div {
            margin-bottom: 8px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 35px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.7));
            backdrop-filter: blur(20px);
            padding: 28px;
            border-radius: 15px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
            overflow: hidden;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2), inset 0 0 40px rgba(59, 130, 246, 0.03);
            opacity: 0;
            animation: cardSlideUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }
        
        .stat-card:nth-child(1) { animation-delay: 2.5s; }
        .stat-card:nth-child(2) { animation-delay: 2.7s; }
        .stat-card:nth-child(3) { animation-delay: 2.9s; }
        .stat-card:nth-child(4) { animation-delay: 3.1s; }
        
        @keyframes cardSlideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-green), transparent);
            animation: topBorderGlow 2s ease-in-out infinite;
        }
        
        @keyframes topBorderGlow {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; box-shadow: 0 0 15px var(--accent-green); }
        }
        
        .stat-card::after {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.1), transparent);
            border-radius: 50%;
            animation: float 6s ease-in-out infinite;
            z-index: 0;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(25px); }
        }
        
        .stat-card:hover {
            transform: translateY(-8px);
            border-color: var(--accent-green);
            box-shadow: 0 25px 60px rgba(34, 197, 94, 0.25), inset 0 0 40px rgba(59, 130, 246, 0.08), 0 0 20px rgba(34, 197, 94, 0.15);
        }
        
        .stat-card h3 {
            margin: 0 0 12px 0;
            color: var(--text-secondary);
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            position: relative;
            z-index: 1;
        }
        
        .stat-value {
            display: flex;
            align-items: baseline;
            gap: 12px;
            position: relative;
            z-index: 1;
        }
        
        .stat-card .number {
            font-size: 38px;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-green), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: 'JetBrains Mono', monospace;
            animation: numberFlip 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 3.1s both;
        }
        
        @keyframes numberFlip {
            from {
                opacity: 0;
                transform: rotateY(90deg);
            }
            to {
                opacity: 1;
                transform: rotateY(0deg);
            }
        }
        
        .section {
            margin-bottom: 35px;
            opacity: 0;
            animation: fadeInScale 0.6s ease-out 3.5s forwards;
        }
        
        @keyframes fadeInScale {
            from {
                opacity: 0;
                transform: scale(0.95);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }.section-title {
            font-size: 17px;
            font-weight: 800;
            color: var(--accent-cyan);
            margin: 0 0 20px 0;
            padding: 0 0 12px 0;
            border-bottom: 2px solid rgba(59, 130, 246, 0.3);
            letter-spacing: 1.5px;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .url-box {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.7));
            backdrop-filter: blur(20px);
            padding: 32px;
            border-radius: 15px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2), inset 0 0 40px rgba(59, 130, 246, 0.03);
            opacity: 0;
            animation: slideInUp 0.6s ease-out 3.7s forwards;
            position: relative;
            overflow: hidden;
        }
        
        .url-box::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue));
            animation: slideInBorder 0.8s ease-out 3.7s forwards;
        }
        
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideInBorder {
            from { width: 0; }
            to { width: 100%; }
        }
        
        .url-box h3 {
            margin: 0 0 16px 0;
            color: var(--accent-cyan);
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 1px;
            position: relative;
            z-index: 1;
        }
        
        .url-box code {
            display: block;
            background: rgba(0, 0, 0, 0.4);
            padding: 16px;
            border-radius: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            margin: 14px 0;
            border: 1px solid rgba(59, 130, 246, 0.1);
            color: var(--accent-green);
            word-break: break-all;
            overflow-x: auto;
            line-height: 1.6;
            position: relative;
            z-index: 1;
            transition: all 0.3s ease;
        }
        
        .url-box code:hover {
            background: rgba(0, 0, 0, 0.6);
            border-color: var(--accent-cyan);
            box-shadow: 0 0 20px rgba(6, 182, 212, 0.2);
        }
        
        .url-box small {
            color: var(--text-secondary);
            font-size: 12px;
            opacity: 0.85;
            position: relative;
            z-index: 1;
        }
        
        .url-actions {
            display: flex;
            gap: 12px;
            margin-top: 18px;
            flex-wrap: wrap;
            position: relative;
            z-index: 1;
        }
        
        .chart-container {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.7));
            backdrop-filter: blur(20px);
            padding: 28px;
            border-radius: 15px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            margin-bottom: 35px;
            position: relative;
            height: 380px;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
            opacity: 0;
            animation: fadeInScale 0.6s ease-out 3.9s forwards;
        }
        
        .chart-title {
            position: absolute;
            top: 20px;
            left: 28px;
            font-size: 13px;
            color: var(--accent-cyan);
            font-weight: 700;
            z-index: 10;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        .table-container {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.7));
            backdrop-filter: blur(20px);
            border-radius: 15px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            overflow: hidden;
            margin-bottom: 35px;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
        }
        
        .table-wrapper {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: rgba(0, 0, 0, 0.3);
            color: var(--accent-green);
            text-align: left;
            padding: 15px 24px;
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            border-bottom: 1px solid rgba(59, 130, 246, 0.1);
            font-family: 'JetBrains Mono', monospace;
        }
        
        td {
            padding: 15px 24px;
            border-bottom: 1px solid rgba(59, 130, 246, 0.05);
            font-size: 13px;
        }
        
        tbody tr {
            transition: all 0.3s ease;
        }
        
        tbody tr:hover {
            background: rgba(59, 130, 246, 0.08);
            border-left: 3px solid var(--accent-green);
        }
        
        .ip-cell {
            font-family: 'JetBrains Mono', monospace;
            color: var(--accent-orange);
            font-weight: 700;
            font-size: 11px;
        }
        
        .location-cell {
            color: var(--text-primary);
            font-weight: 500;
        }
        
        .location-cell.unknown {
            color: var(--text-secondary);
        }
        
        .isp-cell {
            font-size: 12px;
            color: var(--text-secondary);
            font-family: 'JetBrains Mono', monospace;
        }
        
        .ua-cell {
            font-size: 12px;
            color: var(--text-secondary);
            max-width: 280px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .actions {
            display: flex;
            gap: 12px;
            margin-bottom: 35px;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 12px 26px;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.7));
            color: var(--text-primary);
            text-decoration: none;
            border-radius: 10px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            font-weight: 700;
            font-size: 12px;
            transition: all 0.3s ease;
            cursor: pointer;
            font-family: 'Poppins', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            backdrop-filter: blur(10px);
        }
        
        .btn:hover {
            transform: translateY(-3px);
            border-color: var(--accent-green);
            box-shadow: 0 10px 30px rgba(34, 197, 94, 0.2);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            border: none;
            box-shadow: 0 8px 20px rgba(34, 197, 94, 0.3);
        }
        
        .btn-primary:hover {
            box-shadow: 0 15px 40px rgba(34, 197, 94, 0.4);
            transform: translateY(-4px);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            border: none;
            box-shadow: 0 8px 20px rgba(239, 68, 68, 0.3);
        }
        
        .btn-danger:hover {
            box-shadow: 0 15px 40px rgba(239, 68, 68, 0.4);
            transform: translateY(-4px);
        }
        
        .btn-export {
            background: linear-gradient(135deg, #06b6d4, #0891b2);
            color: white;
            border: none;
            box-shadow: 0 8px 20px rgba(6, 182, 212, 0.3);
        }
        
        .btn-export:hover {
            box-shadow: 0 15px 40px rgba(6, 182, 212, 0.4);
            transform: translateY(-4px);
        }
        
        .footer {
            text-align: center;
            color: var(--text-secondary);
            font-size: 11px;
            margin-top: 45px;
            padding: 35px 20px;
            border-top: 1px solid rgba(59, 130, 246, 0.1);
            letter-spacing: 1px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 25px;
            margin-bottom: 35px;
            opacity: 0;
            animation: fadeInScale 0.6s ease-out 4.1s forwards;
        }
        
        .table-container {
            opacity: 0;
            animation: slideInUp 0.6s ease-out 4.3s forwards;
        }
        
        .empty-state {
            text-align: center;
            padding: 50px 35px;
            color: var(--text-secondary);
            opacity: 0;
            animation: fadeInScale 0.6s ease-out 4.3s forwards;
        }
        
        .empty-state p {
            margin: 0;
            font-size: 14px;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(4px);
        }
        
        .modal-content {
            background: var(--bg-secondary);
            margin: 10% auto;
            padding: 30px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 15px;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5);
            animation: modalSlide 0.3s ease-out;
        }
        
        @keyframes modalSlide {
            from { opacity: 0; transform: translateY(-50px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .modal-close {
            color: var(--text-secondary);
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            transition: color 0.3s;
        }
        
        .modal-close:hover {
            color: var(--accent-red);
        }
        
        @media (max-width: 1024px) {
            .grid-2 { grid-template-columns: 1fr; }
        }
        
        @media (max-width: 768px) {
            .container { padding: 16px; }
            .header { 
                flex-direction: column; 
                align-items: flex-start; 
                padding: 20px;
            }
            .header-right { text-align: left; }
            .stats-grid { grid-template-columns: 1fr 1fr; gap: 14px; }
            .actions { flex-direction: column; }
            .btn { width: 100%; justify-content: center; font-size: 11px; }
            .table-wrapper { font-size: 12px; }
            td, th { padding: 12px 16px; font-size: 11px; }
            .stat-card { padding: 18px; }
            .url-box { padding: 20px; }
            .section-title { font-size: 14px; }
        }
    </style>
</head>
<body>
    <!-- Loading Screen -->
    <div class="loading-screen">
        <div class="loading-container">
            <div class="loading-icon">⚡</div>
            <div class="loading-text">SHADOW CORE</div>
            <div class="loading-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
            <div class="loading-bar">
                <div class="loading-bar-fill"></div>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>⚡ SHADOW CORE</h1>
                <div class="header-info">
                    <span><span class="status-dot"></span>ACTIVE</span>
                    <span>📊 {{ stats.total_visits }} VISITS</span>
                    <span>🌍 {{ stats.unique_ips }} IPs</span>
                </div>
            </div>
            <div class="header-right">
                <div><strong>TRACKING URL:</strong></div>
                <div style="color: var(--accent-green); word-break: break-all;">{{ public_url }}</div>
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
                <h3>📈 Today</h3>
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
                <h3><i class="fas fa-link"></i> SHARE THIS URL</h3>
                <code id="trackingUrl">{{ public_url }}</code>
                <small>All device information and geo-location data will be automatically logged.</small>
                <div class="url-actions">
                    <button class="btn btn-primary" onclick="copyToClipboard()"><i class="fas fa-copy"></i> Copy</button>
                    <button class="btn" onclick="newTab()"><i class="fas fa-external-link-alt"></i> Open</button>
                </div>
            </div>
        </div>
        
        <div class="grid-2">
            <div class="section">
                <h2 class="section-title">📊 RECENT VISITS</h2>
                <div class="table-container">
                    {% if stats.recent_visits %}
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>TIME</th>
                                    <th>IP</th>
                                    <th>LOCATION</th>
                                    <th>ISP</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for visit in stats.recent_visits[:10] %}
                                <tr>
                                    <td>{{ visit.timestamp[11:19] }}</td>
                                    <td class="ip-cell">{{ visit.ip_address }}</td>
                                    <td class="location-cell {% if visit.country == 'Unknown' %}unknown{% endif %}">
                                        {% if visit.country != 'Unknown' %}{{ visit.city }}, {{ visit.country }}{% else %}Unknown{% endif %}
                                    </td>
                                    <td class="isp-cell">{{ visit.isp[:20] }}{% if visit.isp|length > 20 %}...{% endif %}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% else %}
                    <div class="empty-state">
                        <p>🔍 No visits yet. Share your tracking link to start collecting data.</p>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">🌍 TOP COUNTRIES</h2>
                <div class="table-container">
                    {% if stats.top_countries %}
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>COUNTRY</th>
                                    <th>VISITS</th>
                                    <th>%</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for country in stats.top_countries[:8] %}
                                <tr>
                                    <td><strong>{{ country.country }}</strong></td>
                                    <td style="color: var(--accent-cyan); font-weight: 700;">{{ country.count }}</td>
                                    <td style="color: var(--accent-green); font-weight: 700;">
                                        {% if stats.total_visits > 0 %}{{ ((country.count / stats.total_visits) * 100)|round(1) }}%{% else %}0%{% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% else %}
                    <div class="empty-state">
                        <p>🌐 No country data yet.</p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <div class="actions">
            <a href="/export" class="btn btn-export"><i class="fas fa-download"></i> EXPORT JSON</a>
            <button class="btn btn-danger" onclick="clearData()"><i class="fas fa-trash"></i> CLEAR DATA</button>
            <a href="/logout" class="btn"><i class="fas fa-sign-out-alt"></i> LOGOUT</a>
        </div>
        
        <div class="footer">
            ⚡ SHADOW CORE v2.0 | {{ stats.total_visits }} TOTAL VISITS | {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}
            <br>© 2025 AFRAFDHMA
        </div>
    </div>
    
    <script>
        function copyToClipboard() {
            const url = document.getElementById('trackingUrl').textContent;
            navigator.clipboard.writeText(url).then(() => {
                const btn = event.target.closest('.btn');
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => { btn.innerHTML = originalText; }, 2000);
            }).catch(() => {
                const textarea = document.createElement('textarea');
                textarea.value = url;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
            });
        }
        
        function newTab() {
            const url = document.getElementById('trackingUrl').textContent;
            window.open(url, '_blank');
        }
        
        function clearData() {
            if (confirm('⚠️ WARNING: Delete ALL tracking data?\n\nThis action CANNOT be undone.')) {
                const userInput = prompt('Type "DELETE" to confirm:');
                if (userInput === 'DELETE') {
                    fetch('/clear', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            alert('[OK] All data cleared!');
                            location.reload();
                        }
                    })
                    .catch(error => console.error('Error:', error));
                } else {
                    alert('❌ Cancelled');
                }
            }
        }
        
        // Enhanced animations on page load
        document.addEventListener('DOMContentLoaded', function() {
            // Animate stat cards with counter effect
            const statNumbers = document.querySelectorAll('.stat-card .number');
            statNumbers.forEach((el, index) => {
                const finalValue = parseInt(el.textContent);
                setTimeout(() => {
                    if (!isNaN(finalValue)) {
                        let currentValue = 0;
                        const increment = Math.ceil(finalValue / 40);
                        const interval = setInterval(() => {
                            currentValue += increment;
                            if (currentValue >= finalValue) {
                                el.textContent = finalValue.toLocaleString();
                                clearInterval(interval);
                            } else {
                                el.textContent = currentValue.toLocaleString();
                            }
                        }, 30);
                    }
                }, 3100 + index * 200);
            });
            
            // Add glow effect to interactive buttons on hover
            const buttons = document.querySelectorAll('.btn');
            buttons.forEach(btn => {
                btn.addEventListener('mouseenter', function() {
                    this.style.textShadow = '0 0 15px rgba(255, 255, 255, 0.5)';
                });
                btn.addEventListener('mouseleave', function() {
                    this.style.textShadow = 'none';
                });
            });
            
            // Table row stagger animation
            const rows = document.querySelectorAll('tbody tr');
            rows.forEach((row, index) => {
                row.style.opacity = '0';
                row.style.animation = `slideInUp 0.4s ease-out ${4.5 + index * 0.08}s forwards`;
            });
            
            // Add sparkle effect to header on interaction
            const header = document.querySelector('.header');
            if (header) {
                header.addEventListener('click', function() {
                    this.style.animation = 'none';
                    setTimeout(() => {
                        this.style.animation = 'headerSparkle 0.6s ease-out';
                    }, 10);
                });
            }
        });
        
        // Header sparkle animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes headerSparkle {
                0% { box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3), inset 0 0 60px rgba(59, 130, 246, 0.05); }
                50% { box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3), inset 0 0 60px rgba(34, 197, 94, 0.15), 0 0 40px rgba(34, 197, 94, 0.3); }
                100% { box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3), inset 0 0 60px rgba(59, 130, 246, 0.05); }
            }
        `;
        document.head.appendChild(style);
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
    =======================================================================
    |       SHADOW CORE TRACKER v2.0 - ENHANCED EDITION                   |
    |                  NGROK OPTIMIZED DEPLOYMENT                         |
    |              Advanced IP/Geolocation Tracking System                |
    |             WITH ADVANCED ANALYTICS & ENTERPRISE FEATURES           |
    |                     FOR AUTHORIZED USE ONLY                         |
    |                                                                     |
    | Developed by: AFRAFDHMA (2025)                                      |
    |                                                                     |
    | Features:                                                           |
    |  [+] Real-time visit tracking                                       |
    |  [+] Advanced geolocation (IP to Coordinates)                       |
    |  [+] Device fingerprinting                                          |
    |  [+] Rate limiting & IP blocking                                    |
    |  [+] Return visitor detection                                       |
    |  [+] Advanced analytics API                                         |
    |  [+] Search & filter capabilities                                   |
    |  [+] Responsive modern dashboard                                    |
    |  [+] Secure session management                                      |
    |  [+] Data export (JSON format)                                      |
    =======================================================================
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
        print("[+] Dependencies: Flask, requests")
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
    
    print(f"\n[+] ADVANCED FEATURES:")
    print(f"    • Advanced Analytics:    /api/advanced-stats")
    print(f"    • Visit Search:          /api/search?q=<query>")
    print(f"    • Filtered Visits:       /api/visits?limit=100&country=US")
    print(f"    • Country Statistics:    /api/stats-by-country?country=US")
    print(f"    • IP Management:         /api/block-ip (POST)")
    
    print(f"\n[+] DASHBOARD FEATURES:")
    print(f"    • Real-time stats       • Advanced analytics      • Return visitor detection")
    print(f"    • Geographic heatmap    • Device fingerprinting   • Export data (JSON)")
    print(f"    • Search functionality  • Rate limiting           • Responsive design")
    
    print(f"\n[+] SECURITY CONFIGURATION:")
    print(f"    • Admin Password: {CONFIG['admin_password']}")
    print(f"    • Session Timeout: {CONFIG['session_timeout']} seconds")
    print(f"    • Rate Limit: {CONFIG['rate_limit_per_ip']} requests/minute")
    print(f"    • Block Private IPs: {'Yes' if CONFIG['block_private_ips'] else 'No'}")
    print(f"    • Fingerprinting: {'Enabled' if CONFIG['enable_fingerprinting'] else 'Disabled'}")
    
    print(f"\n[+] DATABASE OPTIMIZATION:")
    print(f"    • Auto-indexed fields: ip_address, timestamp, country, session_id")
    print(f"    • Database file: {CONFIG['db_file']}")
    print(f"    • Log file: {CONFIG['log_file']}")
    print(f"    • Max visits display: {CONFIG['max_visits_display']}")
    
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
