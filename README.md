# 🔒 AFRACORE - Advanced IP & Geolocation Tracker

> Modern tracking system with Ngrok integration for authorized security research

[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-green?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-red?style=flat-square)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-Afra4509-black?style=flat-square&logo=github)](https://github.com/Afra4509)

## ⚡ Fitur Utama

- 🌍 **Geolocation Tracking** - Lacak lokasi pengunjung secara real-time
- 📊 **Interactive Dashboard** - Dashboard modern dengan statistik lengkap
- 🔐 **Secure Admin Panel** - Login password-protected dengan session management
- 🛡️ **Advanced Fingerprinting** - Browser fingerprinting untuk identifikasi unik
- 🚀 **Ngrok Integration** - Auto-start ngrok tunnel untuk akses publik
- 💾 **Database Caching** - SQLite dengan optimisasi cache
- 📱 **Responsive Design** - UI yang indah dan responsive
- 📤 **Data Export** - Export semua data ke format JSON
- ⚙️ **Rate Limiting** - Proteksi dari brute force dan spam
- 🎯 **Flexible Redirect** - Custom URL redirect setelah tracking

## 📋 Requirement

- **Python 3.9+**
- **pip** (Python package manager)
- **ngrok** (optional, untuk public URL)

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Afra4509/afracore.git
cd afracore
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Atau install manual:

```bash
pip install flask requests
```

### 3. Konfigurasi (Optional)

Edit file `afracore.py` dan sesuaikan CONFIG:

```python
CONFIG = {
    'port': 8080,                          # Port aplikasi
    'admin_password': 'ShadowCore@2024',   # Ganti password admin
    'redirect_url': 'https://www.google.com',  # URL redirect
    'ngrok_region': 'us',                  # us, eu, au, ap, sa, jp, in
}
```

### 4. Run Aplikasi

```bash
python afracore.py
```

Output akan menampilkan:

```
╔═══════════════════════════════════════════════════════════════╗
║                SHADOW CORE TRACKER v2.0                       ║
║               NGROK OPTIMIZED EDITION                         ║
║           Advanced IP/Geo-Location Tracking                   ║
║         FOR AUTHORIZED SECURITY RESEARCH ONLY                 ║
║                    Powered by afratech                        ║
╚═══════════════════════════════════════════════════════════════╝

[✓] Dependencies: Flask, requests

[+] Local Access:
    • Dashboard: http://127.0.0.1:8080/login
    • Tracking:  http://127.0.0.1:8080/

[+] Public Access (via Ngrok):
    • Dashboard: https://xxxx-xx-xxx-xxx.ngrok.io/login
    • Tracking:  https://xxxx-xx-xxx-xxx.ngrok.io/
```

## 🎯 Penggunaan

### Dashboard Admin

1. Akses `http://localhost:8080/login`
2. Masukkan password admin (default: `ShadowCore@2024`)
3. Lihat statistik real-time tracking data

### Tracking Link

Share URL tracking kepada target:

```
http://localhost:8080/
atau
https://xxxx-xx-xxx-xxx.ngrok.io/  (jika menggunakan ngrok)
```

### API Endpoints

| Endpoint | Method | Deskripsi |
|----------|--------|-----------|
| `/` | GET | Main tracking endpoint |
| `/login` | GET, POST | Admin login page |
| `/dashboard` | GET | Admin dashboard |
| `/api/stats` | GET | JSON statistics (requires auth) |
| `/export` | GET | Download data as JSON (requires auth) |
| `/clear` | POST | Clear all data (requires auth) |
| `/logout` | GET | Admin logout |

## ⚙️ Konfigurasi Lanjutan

### API Keys

Dapatkan API key dari [ipinfo.io](https://ipinfo.io):

```python
CONFIG = {
    'api_keys': {
        'ipinfo': "YOUR_API_KEY_HERE",  # Ganti dengan key Anda
        'ipapi': None
    }
}
```

### Ngrok Configuration

```python
CONFIG = {
    'ngrok_autostart': True,        # Auto-start ngrok
    'ngrok_auth_token': 'YOUR_TOKEN',  # Opsional untuk paid plan
    'ngrok_region': 'us',
    'ngrok_subdomain': None,        # Memerlukan paid plan
}
```

### Security Settings

```python
CONFIG = {
    'admin_password': 'ShadowCore@2024',  # Ganti dengan password kuat
    'session_timeout': 7200,              # 2 jam
    'rate_limit_per_ip': 30,              # Request per menit
    'block_private_ips': False,           # Block private IP ranges
    'enable_captcha': False,              # CAPTCHA protection
}
```

## 📊 Database Schema

### Visits Table

Menyimpan data setiap kunjungan:

```
- id (Primary Key)
- timestamp
- ip_address
- country, region, city, postal
- latitude, longitude
- isp, hostname
- user_agent, referrer
- unique_id, session_id
- success, flagged
```

### Fingerprints Table

Menyimpan data fingerprint browser:

```
- id (Primary Key)
- visit_id (Foreign Key)
- browser, platform, languages
- timezone, screen_width, screen_height
- color_depth, hardware_concurrency
- device_memory, canvas_hash
```

## 🔐 Security Features

✅ **Session Management** - Secure cookie-based sessions  
✅ **Password Protection** - Admin panel memerlukan password  
✅ **Rate Limiting** - Proteksi dari spam/brute force  
✅ **Input Validation** - Validasi IP address  
✅ **Bot Detection** - Filter bot/crawler di blocklist  
✅ **HTTPS Support** - Works dengan SSL/TLS (melalui ngrok)

## 🚨 Security Disclaimer

> ⚠️ **IMPORTANT**: Tool ini hanya untuk **authorized security research** dan **educational purposes**.
>
> Penggunaan tanpa izin untuk tracking aktivitas orang lain ADALAH ILEGAL dan dapat mengakibatkan:
> - Tuntutan hukum sipil
> - Tuntutan hukum pidana
> - Pelanggaran privacy laws (GDPR, CCPA, dll)
>
> Selalu dapatkan **informed consent** sebelum tracking apapun.

## 📦 File Structure

```
afracore/
├── afracore.py              # Main application file
├── shadow_tracker.db        # SQLite database (auto-created)
├── shadow_system.log        # Application log (auto-created)
├── README.md                # Documentation
└── requirements.txt         # Python dependencies
```

## 🛠️ Troubleshooting

### Ngrok tidak ditemukan

```bash
# Windows (dengan Chocolatey)
choco install ngrok

# Mac
brew install ngrok

# Linux
https://ngrok.com/download
```

### Port 8080 sudah digunakan

Edit CONFIG dan gunakan port lain:

```python
CONFIG = {
    'port': 8888,  # Port berbeda
}
```

### Database error

Delete `shadow_tracker.db` dan run ulang:

```bash
rm shadow_tracker.db
python afracore.py
```

### Memory leak atau performance issue

Restart aplikasi atau increase `cache_time` untuk geolocation:

```python
geolocator = GeoLocator()
geolocator.cache_time = 7200  # 2 hours
```

## 📚 Dokumentasi API

### GET /

Main tracking endpoint - logs visitor data dan redirect ke URL

```bash
curl http://localhost:8080/
```

### POST /collect

Collect fingerprint data via AJAX:

```bash
curl -X POST http://localhost:8080/collect \
  -H "Content-Type: application/json" \
  -d '{"unique_id":"xxx","fingerprint":{...}}'
```

### GET /api/stats

Get statistics (requires admin session):

```bash
curl -H "Cookie: admin_session=xxx" \
  http://localhost:8080/api/stats
```

## 🎨 Customization

### Custom Branding

Edit LOGIN_TEMPLATE dan DASHBOARD_TEMPLATE untuk styling custom:

```python
LOGIN_TEMPLATE = """
    <!DOCTYPE html>
    <!-- Custom HTML -->
"""
```

### Custom Redirect URL

```python
CONFIG = {
    'redirect_url': 'https://your-website.com'
}
```

### Custom Logo/Icon

Edit bagian `.logo` di CSS template untuk mengganti emoji/logo.

## 📝 License

MIT License - Free untuk penggunaan commercial dan personal

```
Created by: afrafdhma
Powered by: afratech
```

## 👨‍💻 Author

**Afra4509** - [GitHub Profile](https://github.com/Afra4509)

## 🙏 Credits

- Original concept by **aefera**
- Enhanced & modernized by **afrafdhma**
- UI/UX by **afratech**

## 📞 Support

Jika ada pertanyaan atau issue:

1. Cek [Issues](https://github.com/Afra4509/afracore/issues)
2. Buat issue baru dengan detail lengkap
3. Atau hubungi langsung melalui GitHub

## 🌟 Star & Fork

Jika project ini membantu, jangan lupa star ⭐ dan fork 🍴!

---

<div align="center">

Made with ❤️ by **afratech**

**[⬆ Kembali ke atas](#-afracore---advanced-ip--geolocation-tracker)**

</div>
