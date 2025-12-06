# 📖 PANDUAN INSTALASI AFRACORE

## Windows Installation

### 1. Install Python 3.9+

Download dari [python.org](https://www.python.org/downloads/)

Pastikan centang **"Add Python to PATH"** saat install.

Verify installation:
```bash
python --version
pip --version
```

### 2. Download AFRACORE

```bash
git clone https://github.com/Afra4509/afracore.git
cd afracore
```

Atau download ZIP dari repository.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ngrok (Optional)

Untuk public URL, install ngrok:

#### Option A: Dengan Chocolatey

```bash
choco install ngrok
```

#### Option B: Manual Download

1. Download dari https://ngrok.com/download
2. Extract ke folder (misal: `C:\ngrok`)
3. Add ke PATH atau run dari folder tersebut

### 5. Konfigurasi (Optional)

Edit `afracore.py`:

```python
CONFIG = {
    'admin_password': 'GANTI_DENGAN_PASSWORD_ANDA',
    'api_keys': {
        'ipinfo': "DAPATKAN_API_KEY_DI_ipinfo.io"
    }
}
```

### 6. Run Aplikasi

```bash
python afracore.py
```

Akses dashboard di `http://localhost:8080/login`

---

## Mac Installation

### 1. Install Python 3.9+

```bash
brew install python@3.9
```

### 2. Clone Repository

```bash
git clone https://github.com/Afra4509/afracore.git
cd afracore
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Install Ngrok

```bash
brew install ngrok
```

### 6. Run Aplikasi

```bash
python afracore.py
```

---

## Linux Installation

### Ubuntu/Debian

#### 1. Install Python & Dependencies

```bash
sudo apt-get update
sudo apt-get install python3.9 python3.9-venv python3-pip git
```

#### 2. Clone Repository

```bash
git clone https://github.com/Afra4509/afracore.git
cd afracore
```

#### 3. Create Virtual Environment

```bash
python3.9 -m venv venv
source venv/bin/activate
```

#### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 5. Install Ngrok

```bash
# Download latest version
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
unzip ngrok-stable-linux-amd64.zip
sudo mv ngrok /usr/local/bin/
```

#### 6. Run Aplikasi

```bash
python afracore.py
```

### Fedora/RHEL

```bash
sudo dnf install python3.9 python3-pip git
git clone https://github.com/Afra4509/afracore.git
cd afracore
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python afracore.py
```

---

## Docker Installation (Optional)

### 1. Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY afracore.py .

EXPOSE 8080

CMD ["python", "afracore.py"]
```

### 2. Build & Run

```bash
docker build -t afracore .
docker run -p 8080:8080 afracore
```

---

## Verify Installation

Cek apakah semua berjalan dengan baik:

```bash
# Check Python version
python --version

# Check Flask
python -c "import flask; print(flask.__version__)"

# Check Requests
python -c "import requests; print(requests.__version__)"

# Check Ngrok (optional)
ngrok --version
```

---

## Configuration untuk API Keys

### Dapatkan ipinfo.io API Key

1. Kunjungi https://ipinfo.io
2. Sign up (gratis)
3. Copy API token
4. Edit `afracore.py`:

```python
CONFIG = {
    'api_keys': {
        'ipinfo': "PASTE_YOUR_TOKEN_HERE"
    }
}
```

### Dapatkan Ngrok Auth Token (Optional)

1. Kunjungi https://dashboard.ngrok.com
2. Sign up atau login
3. Copy auth token dari dashboard
4. Edit `afracore.py`:

```python
CONFIG = {
    'ngrok_auth_token': 'PASTE_YOUR_TOKEN_HERE'
}
```

---

## Troubleshooting

### ModuleNotFoundError: No module named 'flask'

**Solusi:**
```bash
pip install flask requests
# atau
pip install -r requirements.txt
```

### ngrok command not found

**Solusi (Windows):**
1. Ensure ngrok di PATH atau jalankan dari folder ngrok
2. Atau disable `ngrok_autostart` dan jalankan manual:
   ```bash
   ngrok http 8080
   ```

**Solusi (Mac/Linux):**
```bash
which ngrok  # Check if installed
# If not installed
brew install ngrok
```

### Port 8080 already in use

**Solusi:**
```python
CONFIG = {
    'port': 8888  # Use different port
}
```

### Permission denied saat create database

**Solusi:**
```bash
chmod 755 .  # Linux/Mac
# Windows: Run as Administrator
```

### SSL/TLS Certificate Error

Jika menggunakan HTTPS, pastikan certificate valid. Untuk development, ngrok handle ini otomatis.

---

## Next Steps

1. ✅ Install selesai
2. 📖 Baca README.md untuk dokumentasi lengkap
3. ⚙️ Customize CONFIG sesuai kebutuhan
4. 🚀 Run aplikasi dan test
5. 📤 Deploy ke production (optional)

---

<div align="center">

**Need help?** Check [Issues](https://github.com/Afra4509/afracore/issues) atau buat issue baru

Made with ❤️ by afratech

</div>
