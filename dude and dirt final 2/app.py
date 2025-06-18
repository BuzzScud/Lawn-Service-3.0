"""
DUDE & DIRT - Professional Lawn Care Management System
Production-ready Flask application for Google Cloud deployment
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import secrets
import requests
import json
import logging

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Production configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lawn_service.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'development')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Weather API configuration
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', 'c42d013d70735bb8b4050545852b7a4a')
WEATHER_API_URL = 'http://api.weatherstack.com/current'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    duration_hours = db.Column(db.Integer, default=2)
    active = db.Column(db.Boolean, default=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    service = db.relationship('Service', backref='bookings')
    scheduled_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, completed, cancelled
    special_instructions = db.Column(db.Text)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    step_completed = db.Column(db.Integer, default=1)  # Track 3-step process

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {str(e)}")
        return None

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {str(error)}")
    return render_template('base.html'), 500

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            # Validate required fields
            required_fields = ['username', 'email', 'password', 'full_name']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'success': False, 'message': f'{field} is required'})
            
            # Check if user exists
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'success': False, 'message': 'Email already registered'})
            
            if User.query.filter_by(username=data['username']).first():
                return jsonify({'success': False, 'message': 'Username already taken'})
            
            # Create new user
            user = User(
                username=data['username'],
                email=data['email'],
                password_hash=generate_password_hash(data['password']),
                full_name=data['full_name'],
                phone=data.get('phone', ''),
                address=data.get('address', '')
            )
            
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            return jsonify({'success': True, 'message': 'Registration successful'})
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Registration failed. Please try again.'})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            user = User.query.filter_by(email=data['email']).first()
            
            if user and check_password_hash(user.password_hash, data['password']):
                login_user(user)
                if request.is_json:
                    return jsonify({'success': True, 'message': 'Login successful'})
                else:
                    return redirect(url_for('dashboard'))
            else:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Invalid credentials'})
                else:
                    flash('Invalid credentials', 'error')
                    
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            if request.is_json:
                return jsonify({'success': False, 'message': 'Login failed. Please try again.'})
            else:
                flash('Login failed. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
        return render_template('dashboard.html', user=current_user, bookings=user_bookings)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash('Error loading dashboard', 'error')
        return render_template('dashboard.html', user=current_user, bookings=[])

@app.route('/booking/step1')
@login_required
def booking_step1():
    try:
        services = Service.query.filter_by(active=True).all()
        return render_template('booking_step1.html', services=services)
    except Exception as e:
        logger.error(f"Booking step1 error: {str(e)}")
        return render_template('booking_step1.html', services=[])

@app.route('/booking/step2', methods=['GET', 'POST'])
@login_required
def booking_step2():
    if request.method == 'POST':
        try:
            data = request.get_json()
            # Handle service selection from step 1
            if 'service_id' in data:
                session['booking_data'] = {
                    'service_id': data['service_id'],
                    'service_name': data['service_name'],
                    'price': data['price']
                }
                return jsonify({'success': True})
            # Handle product selection for step 2
            elif 'products' in data:
                if 'booking_data' not in session:
                    return jsonify({'success': False, 'message': 'No booking data found'})
                session['booking_data']['products'] = data['products']
                session['booking_data']['products_total'] = data.get('products_total', 0)
                return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Booking step2 POST error: {str(e)}")
            return jsonify({'success': False, 'message': 'Error processing request'})
    
    if 'booking_data' not in session:
        return redirect(url_for('booking_step1'))
    
    # Sample products for lawn care
    products = [
        {
            'id': 1,
            'name': 'Organic Fertilizer',
            'description': 'Premium organic fertilizer for healthy lawn growth',
            'price': 29.99,
            'size': '50lb bag',
            'category': 'Fertilizer'
        },
        {
            'id': 2,
            'name': 'Weed Control Plus',
            'description': 'Professional weed killer and prevention formula',
            'price': 45.99,
            'size': '1 gallon',
            'category': 'Weed Control'
        },
        {
            'id': 3,
            'name': 'Grass Seed Mix',
            'description': 'Premium grass seed blend for thick, green lawns',
            'price': 19.99,
            'size': '10lb bag',
            'category': 'Seeds'
        },
        {
            'id': 4,
            'name': 'Lawn Aerator Tool',
            'description': 'Professional-grade manual lawn aerator',
            'price': 89.99,
            'size': 'Standard size',
            'category': 'Tools'
        },
        {
            'id': 5,
            'name': 'Mulch Premium',
            'description': 'Natural wood mulch for garden beds and landscaping',
            'price': 12.99,
            'size': '2 cubic ft',
            'category': 'Mulch'
        },
        {
            'id': 6,
            'name': 'Irrigation Timer',
            'description': 'Smart irrigation timer with weather sensing',
            'price': 149.99,
            'size': '6-zone',
            'category': 'Irrigation'
        }
    ]
    
    return render_template('booking_step2.html', booking_data=session['booking_data'], products=products)

@app.route('/booking/step3', methods=['GET', 'POST'])
@login_required
def booking_step3():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if 'booking_data' not in session:
                return jsonify({'success': False, 'message': 'No booking data found'})
            
            session['booking_data'].update({
                'scheduled_date': data['scheduled_date'],
                'scheduled_time': data['scheduled_time'],
                'special_instructions': data.get('special_instructions', '')
            })
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Booking step3 POST error: {str(e)}")
            return jsonify({'success': False, 'message': 'Error processing request'})
    
    if 'booking_data' not in session:
        return redirect(url_for('booking_step1'))
    
    return render_template('booking_step3.html', booking_data=session['booking_data'])

@app.route('/booking/step4', methods=['GET', 'POST'])
@login_required
def booking_step4():
    if 'booking_data' not in session:
        return redirect(url_for('booking_step1'))
    
    if request.method == 'POST':
        try:
            # Create the booking
            booking_data = session['booking_data']
            service = Service.query.get(booking_data['service_id'])
            
            if not service:
                return jsonify({'success': False, 'message': 'Service not found'})
            
            # Parse date and time
            scheduled_datetime = datetime.strptime(
                f"{booking_data['scheduled_date']} {booking_data['scheduled_time']}", 
                "%Y-%m-%d %H:%M"
            )
            
            # Calculate total price
            total_price = service.price + booking_data.get('products_total', 0)
            
            booking = Booking(
                user_id=current_user.id,
                service_id=service.id,
                scheduled_date=scheduled_datetime,
                special_instructions=booking_data.get('special_instructions', ''),
                total_price=total_price,
                status='confirmed'
            )
            
            db.session.add(booking)
            db.session.commit()
            
            # Clear session data
            session.pop('booking_data', None)
            
            return jsonify({'success': True, 'message': 'Booking confirmed successfully!'})
            
        except Exception as e:
            logger.error(f"Booking confirmation error: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Error confirming booking'})
    
    return render_template('booking_step4.html', booking_data=session['booking_data'])

# Weather API functions
def load_weather_cache():
    """Load weather data from cache file"""
    try:
        cache_file = 'weather_cache.json'
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading weather cache: {str(e)}")
    return {}

def save_weather_cache(cache_data):
    """Save weather data to cache file"""
    try:
        cache_file = 'weather_cache.json'
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving weather cache: {str(e)}")

def is_cache_valid(cached_time):
    """Check if cached data is still valid (within 2 hours)"""
    try:
        cache_time = datetime.fromisoformat(cached_time)
        return datetime.now() - cache_time < timedelta(hours=2)
    except:
        return False

def get_mock_weather_data(location):
    """Return mock weather data as fallback"""
    return {
        'location': {
            'name': location,
            'region': 'Local Area',
            'country': 'United States'
        },
        'current': {
            'temperature': 72,
            'weather_descriptions': ['Partly Cloudy'],
            'weather_icons': ['https://assets.weatherstack.com/images/wsymbols01_png_64/wsymbol_0002_sunny_intervals.png'],
            'humidity': 65,
            'wind_speed': 8,
            'wind_dir': 'SW',
            'uv_index': 5,
            'visibility': 10
        }
    }

@app.route('/api/weather')
@login_required
def get_weather():
    """Get weather data with caching and fallback"""
    try:
        location = request.args.get('location', 'Miami, FL')
        
        # Check cache first
        cache = load_weather_cache()
        cache_key = f"weather_{location.lower().replace(' ', '_')}"
        
        if cache_key in cache and is_cache_valid(cache[cache_key].get('timestamp', '')):
            logger.info(f"Returning cached weather data for {location}")
            return jsonify({
                'success': True,
                'data': cache[cache_key]['data'],
                'cached': True,
                'timestamp': cache[cache_key]['timestamp']
            })
        
        # Try to fetch from API
        try:
            params = {
                'access_key': WEATHER_API_KEY,
                'query': location,
                'units': 'f'
            }
            
            response = requests.get(WEATHER_API_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'error' not in data:
                    # Cache the successful response
                    cache[cache_key] = {
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    }
                    save_weather_cache(cache)
                    
                    logger.info(f"Successfully fetched weather data for {location}")
                    return jsonify({
                        'success': True,
                        'data': data,
                        'cached': False,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    logger.warning(f"Weather API error: {data.get('error', {}).get('info', 'Unknown error')}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API request failed: {str(e)}")
        
        # Return mock data as fallback
        mock_data = get_mock_weather_data(location)
        logger.info(f"Returning mock weather data for {location}")
        
        return jsonify({
            'success': True,
            'data': mock_data,
            'cached': False,
            'mock': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Weather endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Weather service temporarily unavailable'
        }), 500

@app.route('/api/weather/status')
@login_required
def weather_status():
    """Get weather API status and cache info"""
    try:
        cache = load_weather_cache()
        cache_count = len(cache)
        
        return jsonify({
            'success': True,
            'cache_entries': cache_count,
            'api_key_configured': bool(WEATHER_API_KEY),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Weather status error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        
        current_user.full_name = data.get('full_name', current_user.full_name)
        current_user.phone = data.get('phone', current_user.phone)
        current_user.address = data.get('address', current_user.address)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating profile'})

@app.route('/points')
@login_required
def points():
    try:
        # Calculate user seeds based on bookings and activities
        completed_bookings = Booking.query.filter_by(user_id=current_user.id, status='completed').count()
        confirmed_bookings = Booking.query.filter_by(user_id=current_user.id, status='confirmed').count()
        
        # Seed calculation: 100 per completed booking + 25 per confirmed booking + 500 welcome bonus
        total_seeds = (completed_bookings * 100) + (confirmed_bookings * 25) + 500
        
        user_seeds = {
            'total_seeds': total_seeds,
            'completed_bookings': completed_bookings,
            'confirmed_bookings': confirmed_bookings,
            'welcome_bonus': 500
        }
        
        return render_template('points.html', user_seeds=user_seeds)
    except Exception as e:
        logger.error(f"Points page error: {str(e)}")
        return render_template('points.html', user_seeds={'total_seeds': 0, 'completed_bookings': 0, 'confirmed_bookings': 0, 'welcome_bonus': 0})

@app.route('/receipts')
@login_required
def receipts():
    try:
        # Get user's completed bookings for receipts
        user_receipts = Booking.query.filter_by(
            user_id=current_user.id,
            status='completed'
        ).order_by(Booking.scheduled_date.desc()).all()
        
        return render_template('receipts.html', receipts=user_receipts)
    except Exception as e:
        logger.error(f"Receipts page error: {str(e)}")
        return render_template('receipts.html', receipts=[])

@app.route('/products')
@login_required
def products():
    try:
        # Initialize booking flow starting with a default service but jump to products
        session['booking_data'] = {
            'service_id': 1,  # Default service
            'service_name': 'Product Purchase',
            'price': 0  # Only product prices will apply
        }
        
        # Sample products for lawn care
        products = [
            {
                'id': 1,
                'name': 'Organic Fertilizer',
                'description': 'Premium organic fertilizer for healthy lawn growth. Perfect for spring and fall applications.',
                'price': 29.99,
                'size': '50lb bag',
                'category': 'Fertilizer',
                'image': '/static/images/fertilizer.jpg',
                'rating': 4.8,
                'reviews': 156,
                'features': ['100% Organic', 'Slow Release', 'Pet Safe', 'Long Lasting']
            },
            {
                'id': 2,
                'name': 'Weed Control Plus',
                'description': 'Professional-grade weed killer and prevention formula that targets weeds while protecting grass.',
                'price': 45.99,
                'size': '1 gallon',
                'category': 'Weed Control',
                'image': '/static/images/weed-control.jpg',
                'rating': 4.6,
                'reviews': 89,
                'features': ['Fast Acting', 'Selective Formula', 'Weather Resistant', 'Professional Grade']
            },
            {
                'id': 3,
                'name': 'Grass Seed Mix',
                'description': 'Premium grass seed blend designed for thick, green lawns that resist drought and disease.',
                'price': 19.99,
                'size': '10lb bag',
                'category': 'Seeds',
                'image': '/static/images/grass-seed.jpg',
                'rating': 4.7,
                'reviews': 203,
                'features': ['Drought Resistant', 'Fast Germination', 'Disease Resistant', 'Premium Blend']
            },
            {
                'id': 4,
                'name': 'Lawn Aerator Tool',
                'description': 'Professional-grade manual lawn aerator for improving soil compaction and water absorption.',
                'price': 89.99,
                'size': 'Standard size',
                'category': 'Tools',
                'image': '/static/images/aerator.jpg',
                'rating': 4.5,
                'reviews': 67,
                'features': ['Durable Steel', 'Ergonomic Handle', 'Easy Storage', 'Professional Quality']
            },
            {
                'id': 5,
                'name': 'Mulch Premium',
                'description': 'Natural wood mulch for garden beds and landscaping. Helps retain moisture and suppress weeds.',
                'price': 12.99,
                'size': '2 cubic ft',
                'category': 'Mulch',
                'image': '/static/images/mulch.jpg',
                'rating': 4.4,
                'reviews': 124,
                'features': ['100% Natural', 'Weed Suppression', 'Moisture Retention', 'Color Enhanced']
            },
            {
                'id': 6,
                'name': 'Irrigation Timer',
                'description': 'Smart irrigation timer with weather sensing technology for efficient watering schedules.',
                'price': 149.99,
                'size': '6-zone',
                'category': 'Irrigation',
                'image': '/static/images/timer.jpg',
                'rating': 4.9,
                'reviews': 78,
                'features': ['Weather Sensing', 'Smart Controls', '6 Zones', 'Water Efficient']
            }
        ]
        
        return render_template('products.html', products=products)
    except Exception as e:
        logger.error(f"Products page error: {str(e)}")
        return render_template('products.html', products=[])

# API Routes
@app.route('/api/stats')
@login_required
def get_user_stats():
    try:
        user_bookings = Booking.query.filter_by(user_id=current_user.id).all()
        
        stats = {
            'total_bookings': len(user_bookings),
            'completed_bookings': len([b for b in user_bookings if b.status == 'completed']),
            'pending_bookings': len([b for b in user_bookings if b.status == 'pending']),
            'confirmed_bookings': len([b for b in user_bookings if b.status == 'confirmed']),
            'total_spent': sum([b.total_price for b in user_bookings if b.status in ['completed', 'confirmed']]),
            'member_since': current_user.created_at.strftime('%B %Y'),
            'next_booking': None
        }
        
        # Find next upcoming booking
        upcoming_bookings = [b for b in user_bookings if b.scheduled_date > datetime.now() and b.status in ['confirmed', 'pending']]
        if upcoming_bookings:
            next_booking = min(upcoming_bookings, key=lambda x: x.scheduled_date)
            stats['next_booking'] = {
                'service': next_booking.service.name,
                'date': next_booking.scheduled_date.strftime('%B %d, %Y'),
                'time': next_booking.scheduled_date.strftime('%I:%M %p')
            }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats API error: {str(e)}")
        return jsonify({'error': 'Error fetching stats'}), 500

@app.route('/api/services')
def get_services():
    try:
        services = Service.query.filter_by(active=True).all()
        services_data = []
        for service in services:
            services_data.append({
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'price': service.price,
                'duration_hours': service.duration_hours
            })
        return jsonify(services_data)
    except Exception as e:
        logger.error(f"Services API error: {str(e)}")
        return jsonify({'error': 'Error fetching services'}), 500

@app.route('/api/bookings')
@login_required
def get_bookings():
    try:
        bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                'id': booking.id,
                'service_name': booking.service.name,
                'scheduled_date': booking.scheduled_date.isoformat(),
                'status': booking.status,
                'total_price': booking.total_price,
                'created_at': booking.created_at.isoformat()
            })
        return jsonify(bookings_data)
    except Exception as e:
        logger.error(f"Bookings API error: {str(e)}")
        return jsonify({'error': 'Error fetching bookings'}), 500

def init_database():
    """Initialize database with sample data"""
    try:
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Check if demo user exists
            demo_user = User.query.filter_by(email='demo@dudeandirt.com').first()
            if not demo_user:
                # Create demo user
                demo_user = User(
                    username='demo_user',
                    email='demo@dudeandirt.com',
                    password_hash=generate_password_hash('demo123'),
                    full_name='Demo User',
                    phone='(555) 123-4567',
                    address='123 Demo Street, Demo City, DC 12345'
                )
                db.session.add(demo_user)
                logger.info("Created demo user")
            
            # Check if services exist
            if Service.query.count() == 0:
                services = [
                    Service(name='Lawn Mowing', description='Professional lawn mowing service', price=50.0, duration_hours=1),
                    Service(name='Fertilization', description='Organic fertilization treatment', price=75.0, duration_hours=1),
                    Service(name='Weed Control', description='Professional weed control treatment', price=65.0, duration_hours=1),
                    Service(name='Aeration', description='Lawn aeration service', price=100.0, duration_hours=2),
                    Service(name='Overseeding', description='Grass overseeding service', price=85.0, duration_hours=2),
                    Service(name='Leaf Removal', description='Fall leaf cleanup service', price=60.0, duration_hours=2)
                ]
                
                for service in services:
                    db.session.add(service)
                
                logger.info("Created sample services")
            
            # Create sample bookings for demo user
            if demo_user and Booking.query.filter_by(user_id=demo_user.id).count() == 0:
                sample_bookings = [
                    Booking(
                        user_id=demo_user.id,
                        service_id=1,
                        scheduled_date=datetime.now() + timedelta(days=7),
                        status='confirmed',
                        total_price=50.0,
                        special_instructions='Please trim around the flower beds carefully'
                    ),
                    Booking(
                        user_id=demo_user.id,
                        service_id=2,
                        scheduled_date=datetime.now() - timedelta(days=30),
                        status='completed',
                        total_price=75.0,
                        special_instructions='Spring fertilization'
                    )
                ]
                
                for booking in sample_bookings:
                    db.session.add(booking)
                
                logger.info("Created sample bookings")
            
            db.session.commit()
            logger.info("Database initialization completed successfully")
            
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        db.session.rollback()

# Initialize database when app starts
init_database()

if __name__ == '__main__':
    # This runs only in local development
    app.run(host='127.0.0.1', port=5000, debug=True) 