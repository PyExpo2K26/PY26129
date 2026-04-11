# Deployment Guide - Smart Irrigation System

## 📋 Project Overview
- **Framework**: Flask (Python web framework)
- **Database**: SQLite3
- **Services**: Twilio SMS integration, ESP32 IoT sensors
- **Structure**: Dashboard + Login system + API endpoints

---

## ⚡ OPTION 1: Local Server Deployment (Easiest - For Testing)

### Step 1: Prepare Your System
```bash
# Navigate to project directory
cd "C:\Users\KiTE\Documents\Final web page"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Or on Windows CMD:
venv\Scripts\activate.bat
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Verify Database Setup
```bash
# The app will auto-create the database on first run
# But ensure database folder permissions are correct
mkdir database
```

### Step 4: Secure Your Credentials
**IMPORTANT**: You have hardcoded Twilio credentials in app.py. Create `.env` file:

```bash
# Create .env file in project root
```
Create `.env`:
```
TWILIO_ACCOUNT_SID=ACb52548537ae425e91a38823937901409
TWILIO_AUTH_TOKEN=ccc42b8b4afe47a1ab1a364ff48da3e1
TWILIO_FROM_NUMBER=+17712328309
TWILIO_TO_NUMBER=+919025036336
FLASK_SECRET_KEY=your_secure_key_here
```

### Step 5: Update app.py to Use Environment Variables
At the top of app.py, replace hardcoded credentials with:
```python
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'ACb52548537ae425e91a38823937901409')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'ccc42b8b4afe47a1ab1a364ff48da3e1')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '+17712328309')
TWILIO_TO_NUMBER = os.getenv('TWILIO_TO_NUMBER', '+919025036336')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'smart_irrigation_secret_key')
```

### Step 6: Run Locally
```bash
python app.py
```
Access at: `http://localhost:5000`

---

## 🚀 OPTION 2: Heroku Deployment (Cloud - Easiest)

### Step 1: Install Heroku CLI
- Download: https://devcenter.heroku.com/articles/heroku-cli
- Verify: `heroku --version`

### Step 2: Create Deployment Files

#### Create `Procfile` (tells Heroku how to run your app):
```
web: gunicorn app:app
```

#### Create `runtime.txt` (specify Python version):
```
python-3.11.4
```

#### Create `.gitignore`:
```
venv/
*.pyc
__pycache__/
.env
*.db
.DS_Store
```

### Step 3: Initialize Git Repository
```bash
git init
git add .
git commit -m "Initial commit - Smart Irrigation System"
```

### Step 4: Deploy to Heroku
```bash
# Login to Heroku
heroku login

# Create Heroku app
heroku create your-app-name

# Add environment variables
heroku config:set TWILIO_ACCOUNT_SID=ACb52548537ae425e91a38823937901409
heroku config:set TWILIO_AUTH_TOKEN=ccc42b8b4afe47a1ab1a364ff48da3e1
heroku config:set TWILIO_FROM_NUMBER=+17712328309
heroku config:set TWILIO_TO_NUMBER=+919025036336
heroku config:set FLASK_SECRET_KEY=your_secure_random_key

# Deploy
git push heroku main

# Monitor logs
heroku logs --tail

# Open app
heroku open
```

**Note**: Heroku free tier is discontinued. Use paid plans ($7-50/month)

---

## 🖥️ OPTION 3: AWS Deployment (Elastic Beanstalk)

### Step 1: Prepare Files
Create `.ebextensions/python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:app
  aws:autoscaling:launchconfiguration:
    InstanceType: t2.micro
```

### Step 2: Install AWS CLI & EB CLI
```bash
pip install awsebcli
```

### Step 3: Initialize & Deploy
```bash
# Initialize EB environment
eb init -p python-3.11 smart-irrigation --region us-east-1

# Create environment
eb create smart-irrigation-env

# Set environment variables
eb setenv TWILIO_ACCOUNT_SID=ACb52548537ae425e91a38823937901409 TWILIO_AUTH_TOKEN=ccc42b8b4afe47a1ab1a364ff48da3e1 TWILIO_FROM_NUMBER=+17712328309 TWILIO_TO_NUMBER=+919025036336

# Deploy
eb deploy

# Open
eb open
```

---

## 🐳 OPTION 4: Docker Deployment (Production-Ready)

### Step 1: Create `Dockerfile` (in project root):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### Step 2: Create `docker-compose.yml` (Optional but recommended):
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - TWILIO_ACCOUNT_SID=ACb52548537ae425e91a38823937901409
      - TWILIO_AUTH_TOKEN=ccc42b8b4afe47a1ab1a364ff48da3e1
      - TWILIO_FROM_NUMBER=+17712328309
      - TWILIO_TO_NUMBER=+919025036336
      - FLASK_SECRET_KEY=your_secure_key
    volumes:
      - ./database:/app/database
```

### Step 3: Build and Run
```bash
# Using Docker directly
docker build -t smart-irrigation .
docker run -p 5000:5000 smart-irrigation

# Or using docker-compose
docker-compose up
```

---

## 📱 OPTION 5: PythonAnywhere Deployment (No Setup Required)

### Step 1: Upload Project
- Go to https://www.pythonanywhere.com
- Sign up (free tier: $0, paid: $5+/month)
- Upload your project files

### Step 2: Configure Web App
- Open Web tab → Add new web app
- Choose "Flask" + Python 3.11
- Point to your app.py

### Step 3: Set Environment Variables
- Go to Web app → Environment variables
- Add all Twilio credentials

### Step 4: Reload
- Click "Reload" button
- Access your app URL

---

## ✅ Final Deployment Checklist

### Security
- [ ] Remove hardcoded credentials (use .env)
- [ ] Add `.env` to `.gitignore`
- [ ] Use strong `FLASK_SECRET_KEY`
- [ ] Enable HTTPS (all platforms support this)

### Database
- [ ] Verify `database/schema.sql` is correct
- [ ] Test database initialization
- [ ] Set up backup strategy

### Monitoring
- [ ] Check application logs regularly
- [ ] Monitor Twilio message usage (50 daily limit on trial)
- [ ] Test ESP32 sensor connectivity from production

### ESP32 Configuration
- In `esp32_send_data.ino`, update the server URL:
  ```cpp
  String server = "your-deployed-url.com/api/sensor_data";
  ```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Database error | Run `python -c "from app import init_db; init_db()"` |
| Port already in use | Change port: `python app.py --port 8000` |
| Twilio SMS not working | Check credentials in .env and trial limits |
| Import errors | Run `pip install -r requirements.txt` again |
| ESP32 can't connect | Verify network/URL configuration in .ino file |

---

## 📞 Quick Reference

**Local Testing**:
```bash
.\venv\Scripts\activate
python app.py
```

**Production Deployment** (Recommended):
- **Best for beginners**: PythonAnywhere
- **Best for scalability**: AWS Elastic Beanstalk
- **Best for simplicity**: Heroku (if within budget)
- **Best for full control**: Docker on your own server

Choose OPTION 1 first to test locally, then pick a deployment platform based on your needs.
