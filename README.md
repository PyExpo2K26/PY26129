# Smart Irrigation System

A Flask-based web dashboard for managing automated irrigation with Twilio SMS alerts and ESP32 sensor integration.

## Quick Start (30 seconds)

### Windows
```bash
setup.bat
python app.py
```

### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open: **http://localhost:5000**

## Deployment Options

| Option | Time | Cost | Best For |
|--------|------|------|----------|
| **Local Server** | 2 min | Free | Testing & development |
| **PythonAnywhere** | 5 min | Free-$5/mo | Beginners |
| **Heroku** | 10 min | $7-50/mo | Small projects |
| **AWS Beanstalk** | 15 min | $5-100/mo | Scalability |
| **Docker** | 20 min | Free-varies | Full control |

**👉 See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions**

## Features

✅ Real-time moisture monitoring (6 fields)  
✅ Automated irrigation control (8 gates)  
✅ SMS alerts via Twilio  
✅ ESP32 IoT sensor integration  
✅ User authentication & dashboard  
✅ Water flow monitoring  
✅ Pump management  

## Project Structure

```
├── app.py                 # Main Flask application
├── database/
│   ├── schema.sql        # SQLite database schema
│   └── irrigation_data.db # Auto-generated database
├── static/
│   ├── script.js         # Frontend logic
│   └── style.css         # Styling
├── templates/
│   ├── login.html        # Login page
│   └── dashboard.html    # Main dashboard
├── esp32_example/
│   └── esp32_send_data.ino # Arduino code for ESP32
├── requirements.txt      # Python dependencies
├── Procfile             # Heroku configuration
├── runtime.txt          # Python version
├── .env.example         # Environment variables template
└── DEPLOYMENT.md        # Full deployment guide
```

## Environment Variables

Create a `.env` file:

```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+0987654321
FLASK_SECRET_KEY=your_secret_key
```

## Dependencies

- Flask 2.3.2
- Twilio 8.10.0
- Gunicorn 21.2.0 (production)
- Python 3.9+

## Troubleshooting

**Port 5000 in use?**
```bash
python app.py --port 8000
```

**Database error?**
```bash
rm database/irrigation_data.db
python app.py
```

**Missing dependencies?**
```bash
pip install -r requirements.txt
```

## Next Steps

1. ✅ Complete local setup above
2. 📝 Update `.env` with your Twilio credentials
3. 🔌 Configure ESP32 with your server URL
4. 🚀 Choose a deployment option from DEPLOYMENT.md
5. 📊 Monitor your irrigation system!

## Support

For issues with:
- **Flask**: https://flask.palletsprojects.com
- **Twilio**: https://www.twilio.com/docs
- **ESP32**: https://docs.espressif.com

---

**Happy irrigating! 🌱**
