# DUDE & DIRT - Professional Lawn Care Management System

A modern, responsive web application for managing lawn care services, bookings, and customer relationships. Built with Flask, featuring a beautiful UI with custom color palette, weather integration, and comprehensive booking system.

## 🌟 Features

### Core Functionality
- **User Authentication** - Secure login/registration system
- **Service Booking** - Multi-step booking process with date/time selection
- **Dashboard** - Comprehensive user dashboard with stats and quick actions
- **Weather Integration** - Real-time weather data with lawn care recommendations
- **Seeds & Rewards** - Loyalty program with points and redemption system
- **Receipt Management** - Timeline view of service history and receipts
- **Product Catalog** - Browse and purchase lawn care products

### Technical Features
- **Responsive Design** - Mobile-first, works on all devices
- **Modern UI** - Custom color palette with smooth animations
- **Weather Caching** - Efficient API usage with 2-hour cache duration
- **Error Handling** - Comprehensive error handling and logging
- **Production Ready** - Optimized for Google Cloud deployment

## 🎨 Design System

### Color Palette
- **Primary Green**: `#057A55` (600), `#046C4E` (700), `#03543F` (800), `#014737` (900)
- **Secondary Blue**: `#1E429F` (800), `#233876` (900)
- **Accent Orange**: `#9F580A` (600), `#8E4B10` (700), `#723B13` (800), `#633112` (900)
- **Neutral**: Cool Gray variations
- **Alerts**: Standard red for warnings/errors

### Icons
- Plant/seed icon for branding and navigation
- Receipt icon for transaction history
- Consistent iconography throughout the application

## 🚀 Quick Start

### Demo Account
- **Email**: `demo@dudeandirt.com`
- **Password**: `demo123`

### Local Development
```bash
# Clone and setup
git clone <repository-url>
cd "DUDE AND DIRT"

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

## ☁️ Google Cloud Deployment

### Prerequisites
1. Google Cloud account with billing enabled
2. Google Cloud SDK installed
3. App Engine API enabled

### Deployment Steps

1. **Initialize Google Cloud Project**
```bash
gcloud init
gcloud app create --region=us-central1
```

2. **Configure Environment Variables**
Edit `app.yaml` and update:
```yaml
env_variables:
  SECRET_KEY: "your-secure-production-secret-key"
  WEATHER_API_KEY: "your-weatherstack-api-key"
```

3. **Deploy Application**
```bash
gcloud app deploy
```

4. **View Application**
```bash
gcloud app browse
```

### Production Configuration

#### Environment Variables
- `SECRET_KEY`: Secure secret key for session management
- `WEATHER_API_KEY`: Weatherstack API key for weather data
- `FLASK_ENV`: Set to `production`

#### Database
- Uses SQLite by default (suitable for demo/small scale)
- For production scale, consider Cloud SQL with PostgreSQL
- Database is automatically initialized with demo data

#### Scaling
- Configured for auto-scaling (1-10 instances)
- CPU utilization target: 60%
- Handles traffic spikes automatically

## 📁 Project Structure

```
DUDE AND DIRT/
├── app.py                 # Main Flask application
├── main.py               # Google Cloud entry point
├── requirements.txt      # Python dependencies
├── app.yaml             # App Engine configuration
├── .gcloudignore        # Deployment exclusions
├── templates/           # Jinja2 templates
│   ├── base.html        # Base template with navigation
│   ├── login.html       # Authentication pages
│   ├── dashboard.html   # Main dashboard
│   ├── booking_*.html   # Multi-step booking flow
│   ├── points.html      # Seeds & rewards system
│   ├── receipts.html    # Transaction history
│   └── products.html    # Product catalog
└── static/             # Static assets (CSS, JS, images)
```

## 🔧 API Endpoints

### Authentication
- `POST /login` - User authentication
- `POST /register` - User registration
- `GET /logout` - User logout

### Booking System
- `GET /booking/step1` - Service selection
- `POST /booking/step2` - Product selection
- `POST /booking/step3` - Date/time selection
- `POST /booking/step4` - Booking confirmation

### Data APIs
- `GET /api/weather` - Weather data with caching
- `GET /api/stats` - User statistics
- `GET /api/bookings` - User booking history
- `GET /api/services` - Available services

## 🌤️ Weather Integration

### Features
- Real-time weather data from Weatherstack API
- 2-hour caching to optimize API usage
- Fallback mock data when API unavailable
- Lawn care recommendations based on conditions

### Configuration
```python
WEATHER_API_KEY = 'your-weatherstack-api-key'
WEATHER_API_URL = 'http://api.weatherstack.com/current'
```

## 💾 Database Schema

### User Model
- Authentication and profile information
- Relationship to bookings and activities

### Service Model
- Available lawn care services
- Pricing and duration information

### Booking Model
- User service bookings
- Status tracking and history
- Pricing and scheduling details

## 🎯 Seeds & Rewards System

### Earning Seeds
- **Service Completion**: 100 seeds per completed service
- **Booking Confirmation**: 25 seeds per confirmed booking
- **Welcome Bonus**: 500 seeds for new members

### Redemption Options
- Service discounts (20% off)
- Free products (fertilizer, tools)
- Premium services (aeration, overseeding)
- VIP status upgrades

## 🔒 Security Features

- Password hashing with Werkzeug
- Session management with Flask-Login
- CSRF protection
- Input validation and sanitization
- Error handling without information disclosure

## 📱 Responsive Design

- Mobile-first approach
- Breakpoints for tablet and desktop
- Touch-friendly interface
- Optimized images and assets

## 🚀 Performance Optimizations

- Weather data caching
- Efficient database queries
- Minified assets
- Optimized images
- CDN-delivered dependencies

## 🔧 Maintenance

### Monitoring
- Application logs via Google Cloud Logging
- Error tracking and alerting
- Performance monitoring

### Updates
- Rolling deployments with zero downtime
- Database migrations handled automatically
- Environment-specific configurations

## 📞 Support

For technical support or questions:
- Check application logs in Google Cloud Console
- Review error messages in the browser console
- Verify environment variables are set correctly

## 📄 License

This project is proprietary software for DUDE & DIRT lawn care services.

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Deployment**: Google Cloud App Engine Ready 