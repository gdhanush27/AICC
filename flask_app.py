from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import json
import time
import re
import requests
import base64
import uuid
import qrcode
from io import BytesIO
from flask_mail import Mail, Message
from config import ALLOWED_EMAIL_DOMAINS, KEY_ID_RAZOR, KEY_SECRET_RAZOR

# Get the absolute path of the directory containing this file (AICC/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# All data, templates, and static folders are in the same AICC directory
PROJECT_ROOT = BASE_DIR

# Function to ensure all required folders and files exist
def initialize_app_structure():
    """Create all necessary folders and files if they don't exist"""
    
    # Create necessary directories in PROJECT_ROOT
    directories = [
        os.path.join(PROJECT_ROOT, 'data'),
        os.path.join(PROJECT_ROOT, 'static'),
        os.path.join(PROJECT_ROOT, 'static/uploads'),
        os.path.join(PROJECT_ROOT, 'static/css'),
        os.path.join(PROJECT_ROOT, 'static/js'),
        os.path.join(PROJECT_ROOT, 'static/img'),
        os.path.join(PROJECT_ROOT, 'static/img/members'),
        os.path.join(PROJECT_ROOT, 'static/img/life'),
        os.path.join(PROJECT_ROOT, 'static/img/poster'),
        os.path.join(PROJECT_ROOT, 'templates'),
        os.path.join(PROJECT_ROOT, 'templates/admin'),
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Create default JSON files if they don't exist
    data_files = {
        'data/club_info.json': {
            "name": "AI and Cybersecurity Club",
            "short_name": "AICC",
            "tagline": "Innovate. Secure. Excel.",
            "description": "The AI and Cybersecurity Club is a student-driven community dedicated to exploring cutting-edge technologies in artificial intelligence and cybersecurity.",
            "college": "Thiagarajar College of Engineering",
            "department": "Department of Computer Science and Engineering",
            "address": "Madurai, Tamil Nadu, India",
            "logo": "/static/img/aicc-logo.webp"
        },
        'data/events.json': [],
        'data/members.json': [],
        'data/gallery.json': []
    }
    
    for file_path, default_content in data_files.items():
        full_path = os.path.join(PROJECT_ROOT, file_path)
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                json.dump(default_content, f, indent=4)

# Initialize app structure on startup
initialize_app_structure()

app = Flask(__name__, 
            template_folder=os.path.join(PROJECT_ROOT, 'templates'),
            static_folder=os.path.join(PROJECT_ROOT, 'static'))
app.secret_key = 'your-secret-key-change-this-in-production'  # ⚠️ CHANGE THIS IN PRODUCTION!
app.config['UPLOAD_FOLDER'] = os.path.join(PROJECT_ROOT, 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching in development
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Initialize Flask-Mail (will be configured from club_info.json)
mail = Mail(app)

def configure_mail():
    """Configure Flask-Mail from club_info.json"""
    email_config = CLUB_INFO.get('email_config', {})
    if email_config:
        app.config['MAIL_SERVER'] = email_config.get('MAIL_SERVER', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = email_config.get('MAIL_PORT', 587)
        app.config['MAIL_USE_TLS'] = email_config.get('MAIL_USE_TLS', True)
        app.config['MAIL_USERNAME'] = email_config.get('MAIL_USERNAME', '')
        app.config['MAIL_PASSWORD'] = email_config.get('MAIL_PASSWORD', '')
        app.config['MAIL_DEFAULT_SENDER'] = email_config.get('MAIL_DEFAULT_SENDER', '')
        mail.init_app(app)

# Function to load data from JSON files
def load_data():
    """Reload all data from JSON files"""
    data_dir = os.path.join(PROJECT_ROOT, 'data')
    with open(os.path.join(data_dir, 'club_info.json'), 'r') as f:
        club_info = json.load(f)
    with open(os.path.join(data_dir, 'events.json'), 'r') as f:
        events = json.load(f)
    with open(os.path.join(data_dir, 'members.json'), 'r') as f:
        members = json.load(f)
    with open(os.path.join(data_dir, 'gallery.json'), 'r') as f:
        gallery = json.load(f)
    return club_info, events, members, gallery

# Load initial data
CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()

# Configure mail with loaded data
configure_mail()

# Add cache-busting filter
@app.template_filter('cache_bust')
def cache_bust_filter(url):
    """Add timestamp to URL for cache busting"""
    if url and '?' not in url:
        return f"{url}?v={int(time.time())}"
    return url

# Make cache_bust available in all templates
app.jinja_env.filters['cache_bust'] = cache_bust_filter

# Admin credentials - ⚠️ CHANGE THESE IN PRODUCTION!
# Use environment variables or database authentication for production
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'  # ⚠️ CHANGE THIS PASSWORD!

# Helper function for file uploads
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sort_members_by_role(members, role_hierarchy, year_hierarchy):
    """Sort members by predefined role hierarchy and year (descending)"""
    def get_sort_key(member):
        role = member.get('role', '')
        year = member.get('year', '')
        
        # Get role index
        try:
            role_index = role_hierarchy.index(role)
        except ValueError:
            # If role not in hierarchy, put at the end
            role_index = len(role_hierarchy)
        
        # Get year index (negative for descending order)
        try:
            year_index = -year_hierarchy.index(year)  # Negative for descending
        except ValueError:
            # If year not in hierarchy, put at the end
            year_index = 0
        
        return (role_index, year_index)
    
    return sorted(members, key=get_sort_key)

def slugify(value):
    """Create a URL-safe slug from text"""
    value = (value or '').strip().lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    return value.strip('-') or 'event'

def delete_old_image(image_path):
    """Delete old image file if it exists in uploads folder"""
    if image_path and '/static/uploads/' in image_path:
        # Extract filename from path
        filename = image_path.split('/static/uploads/')[-1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            pass

def generate_qr_code(data_string):
    """Generate QR code and return as base64 encoded string"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data_string)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return img_base64
    except Exception as e:
        print(f"QR code generation error: {e}")
        return None

def send_registration_email(email, registration_id, qr_code_base64, event_name, registration_data):
    """Send registration confirmation email with QR code"""
    try:
        configure_mail()  # Reconfigure mail in case settings changed
        
        msg = Message(
            subject=f'Registration Confirmation - {event_name}',
            recipients=[email]
        )
        
        # Create HTML email body with CID reference for QR code
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">Registration Successful!</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p style="font-size: 16px; color: #333;">Dear {registration_data.get('name', 'Participant')},</p>
                    
                    <p style="font-size: 14px; color: #555;">
                        Thank you for registering for <strong>{event_name}</strong>!
                    </p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                        <h3 style="color: #667eea; margin-top: 0;">Registration ID:</h3>
                        <p style="font-size: 20px; font-weight: bold; color: #333; margin: 10px 0;">{registration_id}</p>
                    </div>
                    
                    <p style="font-size: 14px; color: #555;">
                        Please save this QR code. You may need to present it at the event:
                    </p>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <img src="cid:qrcode" alt="QR Code" style="max-width: 250px; border: 2px solid #ddd; padding: 10px; background: white; border-radius: 8px;"/>
                    </div>
                    
                    <p style="font-size: 14px; color: #555;">
                        We look forward to seeing you at the event!
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="font-size: 12px; color: #999; text-align: center;">
                        This is an automated email. Please do not reply.<br>
                        {CLUB_INFO.get('name', 'AI Coding Club')} | {CLUB_INFO.get('college', '')}
                    </p>
                </div>
            </body>
        </html>
        """
        
        msg.html = html_body
        
        # Attach QR code as inline image with Content-ID
        if qr_code_base64:
            qr_image_data = base64.b64decode(qr_code_base64)
            msg.attach(
                filename='qrcode.png',
                content_type='image/png',
                data=qr_image_data,
                disposition='inline',
                headers={'Content-ID': '<qrcode>'}
            )
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email sending error: {e}")
        return False

def create_razorpay_order(order_id, amount, customer_name, customer_email, customer_phone, return_url):
    """Create a Razorpay payment order"""
    try:
        # Razorpay API endpoint
        url = "https://api.razorpay.com/v1/orders"
        
        # Basic Auth using key_id and key_secret
        auth = (KEY_ID_RAZOR, KEY_SECRET_RAZOR)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Convert amount to paise (Razorpay uses smallest currency unit)
        amount_in_paise = int(float(amount) * 100)
        
        # Razorpay order payload
        payload = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": str(order_id),
            "notes": {
                "customer_name": customer_name or "Guest",
                "customer_email": customer_email or "",
                "customer_phone": customer_phone or ""
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, auth=auth)
        
        if response.status_code == 200:
            razorpay_response = response.json()
            # Return in format expected by our code
            return {
                "order_id": razorpay_response.get("id"),
                "amount": amount,
                "currency": razorpay_response.get("currency"),
                "receipt": razorpay_response.get("receipt")
            }
        else:
            # Return error details
            error_data = {'error': 'Razorpay API error', 'status_code': response.status_code}
            try:
                error_data['details'] = response.json()
            except:
                error_data['details'] = response.text
            return error_data
            
    except requests.exceptions.RequestException as e:
        return {'error': 'Network error', 'details': str(e)}
    except Exception as e:
        return {'error': 'Unexpected error', 'details': str(e)}

@app.route('/')
def home():
    """Home page with hero section and registration deadline"""
    # Reload data to get latest changes
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    
    # Sort events: with register_link first, then by status (upcoming first)
    sorted_events = sorted(EVENTS, key=lambda x: (
        not bool(x.get('register_link')),  # Events with register_link first
        x.get('status') != 'upcoming',     # Then upcoming events
        x.get('status') == 'completed'     # Then ongoing, then completed
    ))
    
    # Find the next event with an active registration deadline (sorted by earliest deadline)
    next_deadline_event = None
    valid_deadline_events = []
    
    for event in EVENTS:
        # Only consider upcoming or ongoing events with registration deadlines
        if event.get('status') in ['upcoming', 'ongoing']:
            if event.get('registration_deadline') and event.get('register_link'):
                deadline_date = event['registration_deadline']['date']
                try:
                    # Try multiple date formats
                    deadline = None
                    for date_format in ['%Y-%m-%d', '%B %d, %Y']:
                        try:
                            deadline = datetime.strptime(deadline_date, date_format)
                            break
                        except ValueError:
                            continue
                    
                    if deadline and deadline.date() >= datetime.now().date():
                        valid_deadline_events.append((deadline, event))
                except Exception as e:
                    pass
    
    # Sort by earliest deadline and pick the first one
    if valid_deadline_events:
        valid_deadline_events.sort(key=lambda x: x[0])
        next_deadline_event = valid_deadline_events[0][1]
    
    return render_template('index.html', 
                         club_info=CLUB_INFO, 
                         events=sorted_events[:3],  # Show only top 3 events on home
                         contact=CLUB_INFO,
                         next_deadline_event=next_deadline_event)

@app.route('/about')
def about():
    """About page"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return render_template('about.html', 
                         club_info=CLUB_INFO,
                         contact=CLUB_INFO)

@app.route('/events')
def events():
    """Events page showing all events"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    # Sort events: with register_link first, then by status (upcoming first)
    sorted_events = sorted(EVENTS, key=lambda x: (
        not bool(x.get('register_link')),  # Events with register_link first
        x.get('status') != 'upcoming',     # Then upcoming events
        x.get('status') == 'completed'     # Then ongoing, then completed
    ))
    return render_template('events.html', 
                         events=sorted_events,
                         club_info=CLUB_INFO,
                         contact=CLUB_INFO)

@app.route('/events/<int:event_id>')
def event_detail(event_id):
    """Individual event detail page"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    event = next((e for e in EVENTS if e.get('id') == event_id), None)
    if not event:
        return render_template('404.html'), 404
    return render_template('event_detail.html',
                         event=event,
                         club_info=CLUB_INFO,
                         contact=CLUB_INFO)

@app.route('/events/<int:event_id>/register')
def event_register(event_id):
    """Event registration form page"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    
    event = next((e for e in EVENTS if e.get('id') == event_id), None)
    if not event:
        return render_template('404.html'), 404
    
    # Check if event has internal registration
    if event.get('registration_type') != 'internal':
        flash('This event uses external registration.', 'info')
        return redirect(url_for('event_detail', event_id=event_id))
    
    # Load form templates
    templates_file = os.path.join(PROJECT_ROOT, 'data', 'form_templates.json')
    try:
        with open(templates_file, 'r') as f:
            templates = json.load(f)
        
        # Find the template for this event
        template = next((t for t in templates if t.get('id') == event.get('template_id')), None)
        if template and not template.get('active'):
            template = None
        
        # Generate submit endpoint based on event slug
        if template:
            event_slug = slugify(event.get('name'))
            submit_endpoint = f"/api/register/{event_slug}"
        else:
            submit_endpoint = None
        
        return render_template('register_form.html',
                             event=event,
                             form=template,
                             submit_endpoint=submit_endpoint,
                             club_info=CLUB_INFO,
                             contact=CLUB_INFO)
    except Exception as e:
        flash('Registration form not available at this time.', 'error')
        return redirect(url_for('event_detail', event_id=event_id))

@app.route('/api/register/<event_slug>', methods=['POST'])
def api_register_event(event_slug):
    """API endpoint to handle event registration submissions"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # ENSURE SUBMITTER EMAIL IS ALWAYS REQUIRED
        submitter_email = data.get('submitter_email', '').strip()
        if not submitter_email:
            return jsonify({
                'error': 'Submitter email is required',
                'details': 'Please provide your email address'
            }), 400
        
        # Validate submitter email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, submitter_email):
            return jsonify({
                'error': 'Invalid email format',
                'details': 'Please provide a valid email address'
            }), 400
        
        # Validate email domain
        email_domain = submitter_email.split('@')[1].lower()
        if email_domain not in ALLOWED_EMAIL_DOMAINS:
            allowed_domains_str = ', '.join(ALLOWED_EMAIL_DOMAINS)
            return jsonify({
                'error': f'Email domain not allowed. Please use one of: {allowed_domains_str}'
            }), 400
        
        # Validate form if template_id provided
        template_id = data.get('template_id')
        template_definition = None
        if template_id is not None:
            try:
                template_id_int = int(template_id)
            except (TypeError, ValueError):
                return jsonify({'error': 'Invalid template id'}), 400

            templates_file = os.path.join(PROJECT_ROOT, 'data', 'form_templates.json')
            if os.path.exists(templates_file):
                with open(templates_file, 'r') as f:
                    templates = json.load(f)
                template_definition = next((t for t in templates if t.get('id') == template_id_int), None)

        if template_definition:
            if not template_definition.get('active', False):
                return jsonify({'error': 'Registration form is inactive'}), 400

            # Validate required fields
            missing_fields = []
            for field in template_definition.get('fields', []):
                if field.get('required'):
                    field_name = field.get('name')
                    if not field_name or not str(data.get(field_name, '')).strip():
                        missing_fields.append(field.get('label') or field_name)

            if missing_fields:
                return jsonify({
                    'error': 'Missing required fields',
                    'missing': missing_fields
                }), 400
            
            # Validate email fields
            for field in template_definition.get('fields', []):
                if field.get('type') == 'email':
                    field_name = field.get('name')
                    email_value = data.get(field_name, '').strip()
                    
                    if email_value:
                        # Basic email format validation
                        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                        if not re.match(email_pattern, email_value):
                            return jsonify({
                                'error': f'Invalid email format for {field.get("label", field_name)}'
                            }), 400
                        
                        # Domain validation
                        email_domain = email_value.split('@')[1].lower()
                        if email_domain not in ALLOWED_EMAIL_DOMAINS:
                            allowed_domains_str = ', '.join(ALLOWED_EMAIL_DOMAINS)
                            return jsonify({
                                'error': f'Email domain not allowed. Please use one of: {allowed_domains_str}'
                            }), 400

        # Validate event and registration deadline
        event_id = data.get('event_id')
        event = None
        
        if event_id is not None:
            try:
                event_id_int = int(event_id)
                _, events, _, _ = load_data()
                event = next((e for e in events if e.get('id') == event_id_int), None)
            except (TypeError, ValueError):
                pass
        
        # If no event found by ID, try to find by slug
        if not event:
            _, events, _, _ = load_data()
            event = next((e for e in events if slugify(e.get('name', '')) == event_slug), None)
        
        if event:
            # Check registration type
            if event.get('registration_type') not in ['internal']:
                return jsonify({'error': 'Registration is not enabled for this event'}), 400
            
            # Check registration deadline
            deadline_info = event.get('registration_deadline')
            if deadline_info and deadline_info.get('date'):
                try:
                    deadline_date = deadline_info['date']
                    # Skip validation for TBA deadlines
                    if deadline_date.upper() != 'TBA':
                        deadline = datetime.strptime(deadline_date, '%Y-%m-%d')
                        if deadline.date() < datetime.now().date():
                            return jsonify({'error': 'Registration deadline has passed'}), 400
                except ValueError:
                    pass
            
            event_slug = slugify(event.get('name', event_slug))

        # Save registration to file
        registrations_dir = os.path.join(PROJECT_ROOT, 'data', 'registrations')
        os.makedirs(registrations_dir, exist_ok=True)
        
        # Get or create registration file for this event
        # Check if event already has a registration file path
        if event and event.get('registration_file'):
            reg_file = os.path.join(PROJECT_ROOT, event['registration_file'])
        else:
            # Create new timestamped registration file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            reg_filename = f'{event_slug}_{timestamp}_registrations.json'
            reg_file = os.path.join(registrations_dir, reg_filename)
            
            # Update event with registration file path
            if event:
                event['registration_file'] = f'data/registrations/{reg_filename}'
                # Save events.json
                events_file = os.path.join(PROJECT_ROOT, 'data', 'events.json')
                with open(events_file, 'w') as f:
                    json.dump(EVENTS, f, indent=4)
        
        # Load existing registrations or create new list
        registrations = []
        if os.path.exists(reg_file):
            with open(reg_file, 'r') as f:
                registrations = json.load(f)
        
        # MANDATORY CHECK: SUBMITTER EMAIL MUST BE UNIQUE (DEFAULT FOR ALL FORMS)
        submitter_email = data.get('submitter_email', '').strip().lower()
        if submitter_email:
            for reg in registrations:
                existing_email = reg.get('submitter_email', '').strip().lower()
                if existing_email == submitter_email:
                    return jsonify({
                        'error': 'Email already registered',
                        'details': f'The email {submitter_email} is already registered for this event. Each email can only register once.'
                    }), 400
        
        # CHECK FOR OTHER DUPLICATE UNIQUE FIELDS (from form template)
        if template_definition:
            for field in template_definition.get('fields', []):
                if field.get('type') == 'email' and field.get('unique', False):
                    field_name = field.get('name')
                    # Skip if it's the submitter_email (already checked above)
                    if field_name == 'submitter_email':
                        continue
                    
                    email_value = data.get(field_name, '').strip().lower()
                    
                    if email_value:
                        # Check if email already exists in registrations
                        for reg in registrations:
                            existing_email = reg.get(field_name, '').strip().lower()
                            if existing_email == email_value:
                                return jsonify({
                                    'error': f'{field.get("label", field_name)} already registered',
                                    'details': f'The email {email_value} is already registered for this event.'
                                }), 400
        
        # Add timestamp and unique registration ID to registration
        registration_uuid = str(uuid.uuid4())
        data['timestamp'] = datetime.now().isoformat()
        data['id'] = len(registrations) + 1
        data['registration_id'] = registration_uuid
        data['payment_status'] = 'pending' if template_definition and template_definition.get('payment_enabled') else 'not_required'
        data['attendance_status'] = 'not_entered'  # Track attendance
        data['entry_time'] = None  # When they entered
        data['marked_by'] = None  # Admin who marked entry
        
        # Generate QR code for registration with admin verification URL
        event_name = event.get('name', 'Event') if event else 'Event'
        event_id_param = event.get('id', '') if event else ''
        # Create URL for admin to verify entry (host_url already has trailing slash)
        qr_url = f"{request.host_url}admin/verify-entry?regid={registration_uuid}&email={data.get('submitter_email', '')}&event_id={event_id_param}"
        qr_code_base64 = generate_qr_code(qr_url)
        
        if qr_code_base64:
            data['qr_code'] = qr_code_base64
        
        # Check if payment is required
        if template_definition and template_definition.get('payment_enabled'):
            payment_amount = template_definition.get('payment_amount', 0)
            if payment_amount > 0:
                # Create Razorpay payment order
                try:
                    # Ensure phone is available
                    customer_phone = data.get('phone', data.get('team_leader_phone', ''))
                    if not customer_phone or not str(customer_phone).strip():
                        return jsonify({
                            'error': 'Phone number is required for payment',
                            'details': 'Please provide a valid phone number'
                        }), 400
                    
                    order_id = f"ORD_{event_slug}_{data['id']}_{int(time.time())}"
                    payment_order = create_razorpay_order(
                        order_id=order_id,
                        amount=payment_amount,
                        customer_name=data.get('name', data.get('team_leader_name', 'Guest')),
                        customer_email=data.get('email', data.get('team_leader_email', '')),
                        customer_phone=customer_phone,
                        return_url=f"{request.host_url}payment/callback"
                    )
                    
                    # Check if payment order was successful
                    if payment_order and 'order_id' in payment_order and not payment_order.get('error'):
                        # DON'T save registration yet - only save after payment verification
                        # Add payment amount to registration data for verification
                        data['payment_amount'] = payment_amount
                        
                        # Store registration data temporarily in session or return to frontend
                        return jsonify({
                            'success': True,
                            'payment_required': True,
                            'order_id': payment_order['order_id'],
                            'amount': payment_order['amount'],
                            'currency': payment_order['currency'],
                            'key_id': KEY_ID_RAZOR,
                            'registration_data': data,  # Send back to frontend for saving after payment
                            'registration_file': os.path.basename(reg_file)  # Filename to save to
                        }), 200
                    else:
                        # Handle Razorpay error gracefully - return 400, not 500
                        error_msg = 'Failed to create payment order'
                        error_details = 'Payment gateway error. Please contact support.'
                        
                        if payment_order and 'error' in payment_order:
                            if payment_order.get('status_code') == 401:
                                error_details = 'Payment gateway configuration error. Please contact administrator.'
                            elif 'details' in payment_order:
                                error_details = payment_order['details']
                        
                        return jsonify({
                            'error': error_msg,
                            'details': error_details
                        }), 400
                        
                except Exception as e:
                    return jsonify({
                        'error': 'Payment gateway error',
                        'details': 'Unable to process payment. Please try again or contact support.'
                    }), 400
        
        # No payment required - save registration
        # Append new registration
        registrations.append(data)
        
        # Save to file
        with open(reg_file, 'w') as f:
            json.dump(registrations, f, indent=4)
        
        # Send confirmation email with QR code
        email_sent = False
        if qr_code_base64:
            email_sent = send_registration_email(
                email=data.get('submitter_email'),
                registration_id=registration_uuid,
                qr_code_base64=qr_code_base64,
                event_name=event_name,
                registration_data=data
            )
        
        return jsonify({
            'success': True,
            'message': 'Registration submitted successfully!' + (' Confirmation email sent.' if email_sent else ''),
            'registration_id': registration_uuid,
            'email_sent': email_sent,
            'qr_code': qr_code_base64
        }), 200
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to process registration', 'details': str(e)}), 500


@app.route('/payment/verify', methods=['POST'])
def payment_verify():
    """Verify Razorpay payment signature and save registration (Server-side verification)"""
    try:
        data = request.get_json()
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        registration_data = data.get('registration_data')
        registration_file = data.get('registration_file')
        
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return jsonify({'error': 'Missing payment details'}), 400
        
        if not registration_data:
            return jsonify({'error': 'Missing registration data'}), 400
        
        # STEP 1: SERVER-SIDE SIGNATURE VERIFICATION
        # This is critical security step - never trust client-side verification alone
        import hmac
        import hashlib
        
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(
            KEY_SECRET_RAZOR.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if expected_signature != razorpay_signature:
            # Log failed verification attempt
            print(f"Payment verification failed for order {razorpay_order_id}")
            return jsonify({'error': 'Invalid payment signature'}), 400
        
        # STEP 2: ADDITIONAL SERVER-SIDE CHECK - Verify payment status with Razorpay API
        # This prevents replay attacks and ensures payment is actually captured
        try:
            verify_url = f"https://api.razorpay.com/v1/payments/{razorpay_payment_id}"
            auth = (KEY_ID_RAZOR, KEY_SECRET_RAZOR)
            response = requests.get(verify_url, auth=auth)
            
            if response.status_code == 200:
                payment_details = response.json()
                payment_status = payment_details.get('status')
                
                # Verify payment is actually captured
                if payment_status != 'captured':
                    return jsonify({
                        'error': 'Payment not captured',
                        'status': payment_status
                    }), 400
                
                # Verify order_id matches
                if payment_details.get('order_id') != razorpay_order_id:
                    return jsonify({'error': 'Order ID mismatch'}), 400
                
                # Verify amount matches (prevent tampering)
                expected_amount = int(float(registration_data.get('payment_amount', 0)) * 100)
                actual_amount = payment_details.get('amount', 0)
                
                if expected_amount != actual_amount:
                    print(f"Amount mismatch - Expected: {expected_amount}, Received: {actual_amount}, Registration Amount: {registration_data.get('payment_amount')}")
                    return jsonify({
                        'error': 'Payment amount mismatch',
                        'details': f'Expected ₹{expected_amount/100}, received ₹{actual_amount/100}'
                    }), 400
            else:
                return jsonify({'error': 'Unable to verify payment with Razorpay'}), 400
                
        except Exception as e:
            print(f"Error verifying payment with Razorpay API: {str(e)}")
            return jsonify({'error': 'Payment verification failed'}), 500
        
        # STEP 3: Payment fully verified on server - NOW save the registration
        registrations_dir = os.path.join(PROJECT_ROOT, 'data', 'registrations')
        
        if registration_file:
            reg_file = os.path.join(registrations_dir, registration_file)
        else:
            return jsonify({'error': 'Missing registration file'}), 400
        
        # Load existing registrations
        registrations = []
        if os.path.exists(reg_file):
            with open(reg_file, 'r') as f:
                registrations = json.load(f)
        
        # Check for duplicate payment (prevent double registration)
        for reg in registrations:
            if reg.get('payment_id') == razorpay_payment_id:
                return jsonify({
                    'error': 'Payment already processed',
                    'registration_id': reg.get('id')
                }), 400
        
        # Add payment details to registration data
        registration_data['payment_status'] = 'completed'
        registration_data['payment_id'] = razorpay_payment_id
        registration_data['payment_order_id'] = razorpay_order_id
        registration_data['payment_completed_at'] = datetime.now().isoformat()
        registration_data['payment_verified_server_side'] = True
        registration_data['attendance_status'] = 'not_entered'
        registration_data['entry_time'] = None
        registration_data['marked_by'] = None
        
        # Generate UUID and QR code if not already present
        if 'registration_id' not in registration_data:
            registration_uuid = str(uuid.uuid4())
            registration_data['registration_id'] = registration_uuid
            
            # Get event name
            event_name = 'Event'
            try:
                _, events, _, _ = load_data()
                event_id = registration_data.get('event_id')
                if event_id:
                    event = next((e for e in events if e.get('id') == int(event_id)), None)
                    if event:
                        event_name = event.get('name', 'Event')
            except:
                pass
            
            # Generate QR code with admin verification URL
            event_id_param = registration_data.get('event_id', '')
            qr_url = f"{request.host_url}admin/verify-entry?regid={registration_uuid}&email={registration_data.get('submitter_email', '')}&event_id={event_id_param}"
            qr_code_base64 = generate_qr_code(qr_url)
            
            if qr_code_base64:
                registration_data['qr_code'] = qr_code_base64
        else:
            registration_uuid = registration_data['registration_id']
            qr_code_base64 = registration_data.get('qr_code')
            event_name = 'Event'
        
        # Assign new ID
        registration_data['id'] = len(registrations) + 1
        
        # Save registration
        registrations.append(registration_data)
        with open(reg_file, 'w') as f:
            json.dump(registrations, f, indent=4)
        
        # Send confirmation email with QR code
        email_sent = False
        if qr_code_base64:
            email_sent = send_registration_email(
                email=registration_data.get('submitter_email'),
                registration_id=registration_uuid,
                qr_code_base64=qr_code_base64,
                event_name=event_name,
                registration_data=registration_data
            )
        
        return jsonify({
            'success': True,
            'message': 'Payment verified and registration completed!' + (' Confirmation email sent.' if email_sent else ''),
            'registration_id': registration_uuid,
            'email_sent': email_sent,
            'qr_code': qr_code_base64
        }), 200
            
    except Exception as e:
        print(f"Payment verification error: {str(e)}")
        return jsonify({'error': 'Payment verification failed'}), 500


@app.route('/payment/webhook', methods=['POST'])
def payment_webhook():
    """Handle Razorpay webhook for payment notifications (Server-side)"""
    try:
        # Get webhook data
        webhook_secret = os.getenv('RAZORPAY_WEBHOOK_SECRET', 'your_webhook_secret_here')
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        webhook_body = request.get_data()
        
        # Verify webhook signature (Server-side verification)
        import hmac
        import hashlib
        expected_signature = hmac.new(
            webhook_secret.encode(),
            webhook_body,
            hashlib.sha256
        ).hexdigest()
        
        if webhook_signature != expected_signature:
            print("Webhook signature verification failed")
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Process webhook event
        event = request.get_json()
        event_type = event.get('event')
        
        if event_type == 'payment.captured':
            # Payment successful - update registration on server
            payment_entity = event.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            payment_id = payment_entity.get('id')
            amount = payment_entity.get('amount')
            
            print(f"Payment captured: {payment_id} for order: {order_id}")
            
            # Find and update registration
            registrations_dir = os.path.join(PROJECT_ROOT, 'data', 'registrations')
            if os.path.exists(registrations_dir):
                for filename in os.listdir(registrations_dir):
                    if filename.endswith('_registrations.json'):
                        filepath = os.path.join(registrations_dir, filename)
                        with open(filepath, 'r') as f:
                            registrations = json.load(f)
                        
                        for reg in registrations:
                            if reg.get('payment_order_id') == order_id:
                                reg['payment_status'] = 'completed'
                                reg['payment_id'] = payment_id
                                reg['payment_completed_at'] = datetime.now().isoformat()
                                reg['webhook_verified'] = True
                                
                                with open(filepath, 'w') as f:
                                    json.dump(registrations, f, indent=4)
                                
                                return jsonify({'status': 'ok'}), 200
        
        elif event_type == 'payment.failed':
            # Payment failed - update status
            payment_entity = event.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            
            print(f"Payment failed for order: {order_id}")
            
            # Update registration status
            registrations_dir = os.path.join(PROJECT_ROOT, 'data', 'registrations')
            if os.path.exists(registrations_dir):
                for filename in os.listdir(registrations_dir):
                    if filename.endswith('_registrations.json'):
                        filepath = os.path.join(registrations_dir, filename)
                        with open(filepath, 'r') as f:
                            registrations = json.load(f)
                        
                        for reg in registrations:
                            if reg.get('payment_order_id') == order_id:
                                reg['payment_status'] = 'failed'
                                reg['payment_failed_at'] = datetime.now().isoformat()
                                
                                with open(filepath, 'w') as f:
                                    json.dump(registrations, f, indent=4)
                                
                                return jsonify({'status': 'ok'}), 200
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"Webhook processing error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500


@app.route('/payment/status/<order_id>', methods=['GET'])
def payment_status(order_id):
    """Check payment status from Razorpay (Server-side check)"""
    try:
        # Verify with Razorpay API
        verify_url = f"https://api.razorpay.com/v1/orders/{order_id}"
        auth = (KEY_ID_RAZOR, KEY_SECRET_RAZOR)
        response = requests.get(verify_url, auth=auth)
        
        if response.status_code == 200:
            order_details = response.json()
            return jsonify({
                'success': True,
                'order_id': order_details.get('id'),
                'status': order_details.get('status'),
                'amount': order_details.get('amount'),
                'amount_paid': order_details.get('amount_paid'),
                'attempts': order_details.get('attempts')
            }), 200
        else:
            return jsonify({'error': 'Unable to fetch order status'}), 400
            
    except Exception as e:
        print(f"Status check error: {str(e)}")
        return jsonify({'error': 'Status check failed'}), 500


@app.route('/payment/callback')
def payment_callback():
    """Handle Razorpay payment callback/redirect"""
    payment_id = request.args.get('razorpay_payment_id')
    order_id = request.args.get('razorpay_order_id')
    signature = request.args.get('razorpay_signature')
    
    if not all([payment_id, order_id, signature]):
        flash('Invalid payment callback', 'error')
        return redirect(url_for('events'))
    
    # Verify signature on server
    try:
        import hmac
        import hashlib
        message = f"{order_id}|{payment_id}"
        expected_signature = hmac.new(
            KEY_SECRET_RAZOR.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if signature == expected_signature:
            flash('Payment successful! Your registration is confirmed.', 'success')
        else:
            flash('Payment verification failed. Please contact support.', 'error')
            
    except Exception as e:
        flash('Error processing payment. Please contact support.', 'error')
    
    return redirect(url_for('events'))


@app.route('/members')
def members():
    """Members page showing team members"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return render_template('members.html', 
                         members=MEMBERS,
                         club_info=CLUB_INFO,
                         contact=CLUB_INFO)

@app.route('/gallery')
def gallery():
    """Life @ AICC gallery page"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return render_template('gallery.html', 
                         gallery=GALLERY,
                         club_info=CLUB_INFO,
                         contact=CLUB_INFO)

@app.route('/api/events')
def api_events():
    """API endpoint to get events data"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return jsonify(EVENTS)

@app.route('/api/members')
def api_members():
    """API endpoint to get members data"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return jsonify(MEMBERS)

# ========================================
# Admin Routes
# ========================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('Successfully logged out.', 'success')
    return redirect(url_for('admin_login'))

def admin_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login to access the admin panel.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return render_template('admin/dashboard.html',
                         events_count=len(EVENTS),
                         members_count=len(MEMBERS),
                         gallery_count=len(GALLERY),
                         gallery=GALLERY)

@app.route('/admin/club-info', methods=['GET', 'POST'])
@admin_required
def admin_club_info():
    """Edit club information"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    if request.method == 'POST':
        # Reload current club info
        CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
        
        # Handle logo upload
        logo_url = CLUB_INFO.get('logo', '/static/img/aicc-logo.webp')
        if 'logo_image' in request.files:
            file = request.files['logo_image']
            if file and file.filename and allowed_file(file.filename):
                # Delete old logo if it's in uploads folder
                delete_old_image(logo_url)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                logo_url = f"/static/uploads/{filename}"
        
        # Process member_roles and member_years arrays from form
        member_roles = []
        member_years = []
        
        # Get roles from form (could be multiple inputs)
        role_data = request.form.get('member_roles_json')
        if role_data:
            try:
                member_roles = json.loads(role_data)
            except:
                member_roles = CLUB_INFO.get('member_roles', [])
        
        # Get years from form
        year_data = request.form.get('member_years_json')
        if year_data:
            try:
                member_years = json.loads(year_data)
            except:
                member_years = CLUB_INFO.get('member_years', [])
        
        data = {
            'name': request.form.get('name'),
            'short_name': request.form.get('short_name'),
            'tagline': request.form.get('tagline'),
            'description': request.form.get('description'),
            'college': request.form.get('college'),
            'department': request.form.get('department'),
            'address': request.form.get('address'),
            'logo': logo_url,
            'member_roles': member_roles,
            'member_years': member_years,
            'email': CLUB_INFO.get('email', ''),
            'linkedin': CLUB_INFO.get('linkedin', ''),
            'instagram': CLUB_INFO.get('instagram', ''),
            'email_config': {
                'MAIL_SERVER': request.form.get('mail_server', 'smtp.gmail.com'),
                'MAIL_PORT': int(request.form.get('mail_port', 587)),
                'MAIL_USE_TLS': request.form.get('mail_use_tls') == 'true',
                'MAIL_USERNAME': request.form.get('mail_username', ''),
                'MAIL_PASSWORD': request.form.get('mail_password', ''),
                'MAIL_DEFAULT_SENDER': request.form.get('mail_default_sender', '')
            },
            'faculty_coordinators': CLUB_INFO.get('faculty_coordinators', []),
            'secretaries': CLUB_INFO.get('secretaries', [])
        }
        
        with open(os.path.join(PROJECT_ROOT, 'data/club_info.json'), 'w') as f:
            json.dump(data, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
        
        flash('Club information updated successfully!', 'success')
        return redirect(url_for('admin_club_info'))
    
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return render_template('admin/club_info.html', club_info=CLUB_INFO)

@app.route('/admin/events', methods=['GET'])
@admin_required
def admin_events():
    """View all events"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return render_template('admin/events.html', events=EVENTS)

@app.route('/admin/events/create', methods=['GET', 'POST'])
@admin_required
def admin_create_event():
    """Create a new event"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    if request.method == 'POST':
        # Reload events from file
        with open(os.path.join(PROJECT_ROOT, 'data/events.json'), 'r') as f:
            events = json.load(f)
        
        # Handle image upload
        image_url = ''
        if 'event_image' in request.files:
            file = request.files['event_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = f"/static/uploads/{filename}"
        
        # Add new event
        new_event = {
            'id': max([e.get('id', 0) for e in events], default=0) + 1,
            'name': request.form.get('name'),
            'date': request.form.get('date'),
            'time': request.form.get('time'),
            'location': request.form.get('location'),
            'description': request.form.get('description'),
            'how': request.form.get('how'),
            'status': request.form.get('status'),
            'image': image_url,
            'rules': request.form.get('rules', '').split('\n') if request.form.get('rules') else [],
            'coordinators': []
        }
        
        # Handle registration settings
        registration_type = request.form.get('registration_type', 'none')
        new_event['registration_type'] = registration_type
        
        if registration_type == 'external':
            new_event['register_link'] = request.form.get('register_link', '#')
            new_event['template_id'] = None
        elif registration_type == 'internal':
            template_id = request.form.get('template_id')
            new_event['template_id'] = int(template_id) if template_id else None
            new_event['register_link'] = '#'
        else:
            new_event['register_link'] = '#'
            new_event['template_id'] = None
        
        # Add registration deadline if provided
        deadline_date = request.form.get('deadline_date')
        deadline_message = request.form.get('deadline_message')
        if deadline_date:
            new_event['registration_deadline'] = {
                'date': deadline_date,
                'message': deadline_message if deadline_message else 'Register now!'
            }
        
        events.append(new_event)
        
        with open(os.path.join(PROJECT_ROOT, 'data/events.json'), 'w') as f:
            json.dump(events, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('admin_events'))
    
    # Load form templates for the dropdown
    templates = []
    templates_file = os.path.join(PROJECT_ROOT, 'data', 'form_templates.json')
    try:
        if os.path.exists(templates_file):
            with open(templates_file, 'r') as f:
                templates = json.load(f)
    except Exception as e:
        print(f"Error loading templates: {e}")
    
    return render_template('admin/create_event.html', forms=templates)

@app.route('/admin/events/<int:event_id>/delete', methods=['POST'])
@admin_required
def admin_delete_event(event_id):
    """Delete an event"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    with open(os.path.join(PROJECT_ROOT, 'data/events.json'), 'r') as f:
        events = json.load(f)
    
    # Find the event and delete its image before removing
    event_to_delete = next((e for e in events if e.get('id') == event_id), None)
    if event_to_delete:
        delete_old_image(event_to_delete.get('image', ''))
    
    events = [e for e in events if e.get('id') != event_id]
    
    with open(os.path.join(PROJECT_ROOT, 'data/events.json'), 'w') as f:
        json.dump(events, f, indent=4)
    
    # Reload data
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin_events'))

@app.route('/admin/members', methods=['GET', 'POST'])
@admin_required
def admin_members():
    """Manage members"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    if request.method == 'POST':
        with open(os.path.join(PROJECT_ROOT, 'data/members.json'), 'r') as f:
            members = json.load(f)
        
        # Handle image upload
        image_url = '/static/img/members/default.webp'
        if 'member_image' in request.files:
            file = request.files['member_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = f"/static/uploads/{filename}"
        
        new_member = {
            'name': request.form.get('name'),
            'role': request.form.get('role'),
            'year': request.form.get('year'),
            'domain': request.form.get('domain'),
            'image': image_url,
            'linkedin': request.form.get('linkedin'),
            'github': request.form.get('github')
        }
        
        members.append(new_member)
        
        # Sort members by role hierarchy and year before saving
        role_hierarchy = CLUB_INFO.get('member_roles', [])
        year_hierarchy = CLUB_INFO.get('member_years', [])
        if role_hierarchy:
            members = sort_members_by_role(members, role_hierarchy, year_hierarchy)
        
        with open(os.path.join(PROJECT_ROOT, 'data/members.json'), 'w') as f:
            json.dump(members, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
        
        flash('Member added successfully!', 'success')
        return redirect(url_for('admin_members'))
    
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return render_template('admin/members.html', members=MEMBERS, club_info=CLUB_INFO)

@app.route('/admin/contact', methods=['GET', 'POST'])
@admin_required
def admin_contact():
    """Edit contact information"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    if request.method == 'POST':
        # Load current club info and update contact fields
        CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
        
        CLUB_INFO['email'] = request.form.get('email')
        CLUB_INFO['instagram'] = request.form.get('instagram')
        CLUB_INFO['linkedin'] = request.form.get('linkedin')
        # Keep existing faculty_coordinators and secretaries
        
        with open(os.path.join(PROJECT_ROOT, 'data/club_info.json'), 'w') as f:
            json.dump(CLUB_INFO, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
        
        flash('Contact information updated successfully!', 'success')
        return redirect(url_for('admin_contact'))
    
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return render_template('admin/contact.html', contact=CLUB_INFO)

# ========================================
# File Upload Routes
# ========================================

@app.route('/admin/upload', methods=['POST'])
@admin_required
def upload_file():
    """Handle file uploads"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Ensure upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Return URL path
        url = f"/static/uploads/{filename}"
        return jsonify({'url': url}), 200
    
    return jsonify({'error': 'Invalid file type'}), 400

# ========================================
# Edit Routes
# ========================================

@app.route('/admin/events/<int:event_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_event(event_id):
    """Edit an existing event"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    with open(os.path.join(PROJECT_ROOT, 'data/events.json'), 'r') as f:
        events = json.load(f)
    
    event = next((e for e in events if e.get('id') == event_id), None)
    if not event:
        flash('Event not found!', 'error')
        return redirect(url_for('admin_events'))
    
    if request.method == 'POST':
        # Handle image upload
        image_url = event.get('image', '')
        if 'event_image' in request.files:
            file = request.files['event_image']
            if file and file.filename and allowed_file(file.filename):
                # Delete old image before uploading new one
                delete_old_image(image_url)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = f"/static/uploads/{filename}"
        
        # Update event data
        event['name'] = request.form.get('name')
        event['date'] = request.form.get('date')
        event['time'] = request.form.get('time')
        event['location'] = request.form.get('location')
        event['description'] = request.form.get('description')
        event['how'] = request.form.get('how')
        event['status'] = request.form.get('status')
        event['image'] = image_url
        event['rules'] = request.form.get('rules', '').split('\n') if request.form.get('rules') else []
        
        # Handle registration settings
        registration_type = request.form.get('registration_type', 'none')
        event['registration_type'] = registration_type
        
        if registration_type == 'external':
            event['register_link'] = request.form.get('register_link', '#')
            event['template_id'] = None
        elif registration_type == 'internal':
            template_id = request.form.get('template_id')
            event['template_id'] = int(template_id) if template_id else None
            event['register_link'] = '#'
        else:
            event['register_link'] = '#'
            event['template_id'] = None
        
        # Handle registration deadline
        deadline_date = request.form.get('deadline_date')
        deadline_message = request.form.get('deadline_message')
        if deadline_date:
            event['registration_deadline'] = {
                'date': deadline_date,
                'message': deadline_message if deadline_message else 'Register now!'
            }
        elif 'registration_deadline' in event:
            # Remove deadline if fields are empty
            del event['registration_deadline']
        
        with open(os.path.join(PROJECT_ROOT, 'data/events.json'), 'w') as f:
            json.dump(events, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
        
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin_events'))
    
    # Load form templates for the dropdown
    templates = []
    templates_file = os.path.join(PROJECT_ROOT, 'data', 'form_templates.json')
    try:
        if os.path.exists(templates_file):
            with open(templates_file, 'r') as f:
                templates = json.load(f)
    except Exception as e:
        print(f"Error loading templates: {e}")
    
    return render_template('admin/edit_event.html', event=event, forms=templates)

@app.route('/admin/events/<int:event_id>/delete-image', methods=['POST'])
@admin_required
def admin_delete_event_image(event_id):
    """Delete event image"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    try:
        with open(os.path.join(PROJECT_ROOT, 'data/events.json'), 'r') as f:
            events = json.load(f)
        
        event = next((e for e in events if e.get('id') == event_id), None)
        if not event:
            return jsonify({'success': False, 'error': 'Event not found'}), 404
        
        # Delete the image file if it exists
        if event.get('image'):
            delete_old_image(event['image'])
            event['image'] = ''
            
            # Save updated events
            with open(os.path.join(PROJECT_ROOT, 'data/events.json'), 'w') as f:
                json.dump(events, f, indent=4)
            
            # Reload data
            CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'No image to delete'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/members/<int:member_index>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_member(member_index):
    """Edit an existing member"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    with open(os.path.join(PROJECT_ROOT, 'data/members.json'), 'r') as f:
        members = json.load(f)
    
    if member_index >= len(members):
        flash('Member not found!', 'error')
        return redirect(url_for('admin_members'))
    
    member = members[member_index]
    
    if request.method == 'POST':
        # Handle image upload
        image_url = member.get('image', '')
        
        # Check if user wants to reset to default
        if request.form.get('reset_image') == 'true':
            # Delete old custom image if it exists
            if image_url and image_url != '/static/img/members/default.webp':
                delete_old_image(image_url)
            image_url = '/static/img/members/default.webp'
        elif 'member_image' in request.files:
            file = request.files['member_image']
            if file and file.filename and allowed_file(file.filename):
                # Delete old image before uploading new one
                delete_old_image(image_url)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = f"/static/uploads/{filename}"
        
        # Update member data
        members[member_index] = {
            'name': request.form.get('name'),
            'role': request.form.get('role'),
            'year': request.form.get('year'),
            'domain': request.form.get('domain'),
            'image': image_url or '/static/img/members/default.webp',
            'linkedin': request.form.get('linkedin'),
            'github': request.form.get('github')
        }
        
        # Sort members by role hierarchy and year before saving
        role_hierarchy = CLUB_INFO.get('member_roles', [])
        year_hierarchy = CLUB_INFO.get('member_years', [])
        if role_hierarchy:
            members = sort_members_by_role(members, role_hierarchy, year_hierarchy)
        
        with open(os.path.join(PROJECT_ROOT, 'data/members.json'), 'w') as f:
            json.dump(members, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
        
        flash('Member updated successfully!', 'success')
        return redirect(url_for('admin_members'))
    
    # Load club_info for role and year dropdowns
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return render_template('admin/edit_member.html', member=member, member_index=member_index, club_info=CLUB_INFO)

@app.route('/admin/members/<int:member_index>/delete', methods=['POST'])
@admin_required
def admin_delete_member(member_index):
    """Delete a member"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    with open(os.path.join(PROJECT_ROOT, 'data/members.json'), 'r') as f:
        members = json.load(f)
    
    if member_index < len(members):
        # Delete member's image before removing from list
        member = members[member_index]
        delete_old_image(member.get('image', ''))
        
        members.pop(member_index)
        
        with open(os.path.join(PROJECT_ROOT, 'data/members.json'), 'w') as f:
            json.dump(members, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
        
        flash('Member deleted successfully!', 'success')
    
    return redirect(url_for('admin_members'))

@app.route('/admin/gallery', methods=['GET', 'POST'])
@admin_required
def admin_gallery():
    """Manage gallery images"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    if request.method == 'POST':
        if 'gallery_image' in request.files:
            file = request.files['gallery_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Add to gallery
                with open(os.path.join(PROJECT_ROOT, 'data/gallery.json'), 'r') as f:
                    gallery = json.load(f)
                
                new_image = {
                    'url': f"/static/uploads/{filename}",
                    'title': request.form.get('title', 'Gallery Image'),
                    'category': request.form.get('category', 'events')
                }
                
                gallery.append(new_image)
                
                with open(os.path.join(PROJECT_ROOT, 'data/gallery.json'), 'w') as f:
                    json.dump(gallery, f, indent=4)
                
                # Reload data
                CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
                
                flash('Image uploaded successfully!', 'success')
                return redirect(url_for('admin_gallery'))
    
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    return render_template('admin/gallery.html', gallery=GALLERY)

@app.route('/admin/gallery/<int:image_index>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_gallery_image(image_index):
    """Edit a gallery image"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    with open(os.path.join(PROJECT_ROOT, 'data/gallery.json'), 'r') as f:
        gallery = json.load(f)
    
    if image_index >= len(gallery):
        flash('Image not found!', 'error')
        return redirect(url_for('admin_gallery'))
    
    image = gallery[image_index]
    
    if request.method == 'POST':
        # Update image details
        image['title'] = request.form.get('title')
        image['category'] = request.form.get('category', 'events')
        image['description'] = request.form.get('description', '')
        
        with open(os.path.join(PROJECT_ROOT, 'data/gallery.json'), 'w') as f:
            json.dump(gallery, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
        
        flash('Image updated successfully!', 'success')
        return redirect(url_for('admin_gallery'))
    
    return render_template('admin/edit_gallery.html', image=image, image_index=image_index)

@app.route('/admin/gallery/<int:image_index>/delete', methods=['POST'])
@admin_required
def admin_delete_gallery_image(image_index):
    """Delete a gallery image"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    
    with open(os.path.join(PROJECT_ROOT, 'data/gallery.json'), 'r') as f:
        gallery = json.load(f)
    
    if image_index < len(gallery):
        # Delete the image file before removing from gallery
        image = gallery[image_index]
        delete_old_image(image.get('url') or image.get('image', ''))
        
        gallery.pop(image_index)
        
        with open(os.path.join(PROJECT_ROOT, 'data/gallery.json'), 'w') as f:
            json.dump(gallery, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
        
        flash('Image deleted successfully!', 'success')
    
    return redirect(url_for('admin_gallery'))

# ========================================
# REGISTRATION FORMS MANAGEMENT ROUTES
# ========================================

@app.route('/admin/form-templates')
@admin_required
def admin_registration_forms():
    """Admin page to manage form templates"""
    templates_file = os.path.join(PROJECT_ROOT, 'data', 'form_templates.json')
    templates = []
    
    try:
        if os.path.exists(templates_file):
            with open(templates_file, 'r') as f:
                templates = json.load(f)
    except Exception as e:
        flash('Error loading form templates.', 'error')
    
    return render_template('admin/registration_forms.html',
                         forms=templates)

@app.route('/admin/form-templates/create', methods=['GET', 'POST'])
@admin_required
def admin_create_registration_form():
    """Create a new form template"""
    if request.method == 'POST':
        try:
            # Load existing templates
            templates_file = os.path.join(PROJECT_ROOT, 'data', 'form_templates.json')
            templates = []
            if os.path.exists(templates_file):
                with open(templates_file, 'r') as f:
                    templates = json.load(f)
            
            # Get form data
            template_data = {
                'id': len(templates) + 1,
                'name': request.form.get('name'),
                'description': request.form.get('description', ''),
                'fields': json.loads(request.form.get('fields', '[]')),
                'active': request.form.get('active') == 'true'
            }
            
            # Add to templates list
            templates.append(template_data)
            
            # Save to file
            with open(templates_file, 'w') as f:
                json.dump(templates, f, indent=4)
            
            flash('Form template created successfully!', 'success')
            return redirect(url_for('admin_registration_forms'))
            
        except Exception as e:
            flash(f'Error creating form template: {str(e)}', 'error')
    
    return render_template('admin/create_registration_form.html')

@app.route('/admin/form-templates/<int:form_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_registration_form(form_id):
    """Edit an existing form template"""
    templates_file = os.path.join(PROJECT_ROOT, 'data', 'form_templates.json')
    
    try:
        with open(templates_file, 'r') as f:
            templates = json.load(f)
    except:
        flash('Error loading form templates.', 'error')
        return redirect(url_for('admin_registration_forms'))
    
    # Find the template
    template_index = next((i for i, t in enumerate(templates) if t.get('id') == form_id), None)
    if template_index is None:
        flash('Template not found.', 'error')
        return redirect(url_for('admin_registration_forms'))
    
    if request.method == 'POST':
        try:
            # Update template data
            templates[template_index]['name'] = request.form.get('name')
            templates[template_index]['description'] = request.form.get('description', '')
            templates[template_index]['fields'] = json.loads(request.form.get('fields', '[]'))
            templates[template_index]['active'] = request.form.get('active') == 'true'
            
            # Save to file
            with open(templates_file, 'w') as f:
                json.dump(templates, f, indent=4)
            
            flash('Form template updated successfully!', 'success')
            return redirect(url_for('admin_registration_forms'))
            
        except Exception as e:
            pass
            flash(f'Error updating form template: {str(e)}', 'error')
    
    return render_template('admin/edit_registration_form.html',
                         form=templates[template_index])

@app.route('/admin/form-templates/<int:form_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_form_status(form_id):
    """Toggle the active status of a form template"""
    templates_file = os.path.join(PROJECT_ROOT, 'data', 'form_templates.json')
    
    try:
        with open(templates_file, 'r') as f:
            templates = json.load(f)
        
        # Find the template and toggle its active status
        template = next((t for t in templates if t.get('id') == form_id), None)
        if template:
            template['active'] = not template.get('active', True)
            
            with open(templates_file, 'w') as f:
                json.dump(templates, f, indent=4)
            
            status = 'activated' if template['active'] else 'deactivated'
            flash(f'Form template {status} successfully!', 'success')
        else:
            flash('Template not found.', 'error')
            
    except Exception as e:
        flash('Error updating form template status.', 'error')
    
    return redirect(url_for('admin_registration_forms'))

@app.route('/admin/form-templates/<int:form_id>/delete', methods=['POST'])
@admin_required
def admin_delete_registration_form(form_id):
    """Delete a form template"""
    templates_file = os.path.join(PROJECT_ROOT, 'data', 'form_templates.json')
    
    try:
        with open(templates_file, 'r') as f:
            templates = json.load(f)
        
        # Find and remove the template
        template_index = next((i for i, t in enumerate(templates) if t.get('id') == form_id), None)
        if template_index is not None:
            templates.pop(template_index)
            
            with open(templates_file, 'w') as f:
                json.dump(templates, f, indent=4)
            
            flash('Form template deleted successfully!', 'success')
        else:
            flash('Template not found.', 'error')
            
    except Exception as e:
        flash('Error deleting form template.', 'error')
    
    return redirect(url_for('admin_registration_forms'))

@app.route('/admin/events/<int:event_id>/registrations')
@admin_required
def admin_view_registrations(event_id):
    """View registrations for a specific event"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    
    event = next((e for e in EVENTS if e.get('id') == event_id), None)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('admin_events'))
    
    # Load form template if assigned
    template = None
    if event.get('template_id'):
        templates_file = os.path.join(PROJECT_ROOT, 'data', 'form_templates.json')
        try:
            with open(templates_file, 'r') as f:
                templates = json.load(f)
            template = next((t for t in templates if t.get('id') == event.get('template_id')), None)
        except:
            pass
    
    # Load registrations for this event
    registrations = []
    if event.get('registration_file'):
        reg_file = os.path.join(PROJECT_ROOT, event['registration_file'])
        if os.path.exists(reg_file):
            with open(reg_file, 'r') as f:
                registrations = json.load(f)
    else:
        # Fallback to old naming convention for backwards compatibility
        event_slug = slugify(event.get('name', ''))
        reg_file = os.path.join(PROJECT_ROOT, 'data', 'registrations', f'{event_slug}_registrations.json')
        if os.path.exists(reg_file):
            with open(reg_file, 'r') as f:
                registrations = json.load(f)
    
    return render_template('admin/view_registrations.html',
                         form=template,
                         event=event,
                         registrations=registrations)

@app.route('/admin/verify-entry')
@admin_required
def admin_verify_entry():
    """QR code entry verification page"""
    regid = request.args.get('regid')
    email = request.args.get('email')
    event_id = request.args.get('event_id')
    
    if not regid or not email or not event_id:
        flash('Invalid QR code. Missing parameters.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        event_id = int(event_id)
    except (ValueError, TypeError):
        flash('Invalid event ID.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    
    event = next((e for e in EVENTS if e.get('id') == event_id), None)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Load registrations
    registrations = []
    reg_file_path = None
    if event.get('registration_file'):
        reg_file_path = os.path.join(PROJECT_ROOT, event['registration_file'])
        if os.path.exists(reg_file_path):
            with open(reg_file_path, 'r') as f:
                registrations = json.load(f)
    else:
        event_slug = slugify(event.get('name', ''))
        reg_file_path = os.path.join(PROJECT_ROOT, 'data', 'registrations', f'{event_slug}_registrations.json')
        if os.path.exists(reg_file_path):
            with open(reg_file_path, 'r') as f:
                registrations = json.load(f)
    
    # Find the registration
    registration = None
    for reg in registrations:
        if reg.get('registration_id') == regid and reg.get('submitter_email', '').lower() == email.lower():
            registration = reg
            break
    
    if not registration:
        flash('Registration not found or email does not match.', 'error')
        return redirect(url_for('admin_view_registrations', event_id=event_id))
    
    # Check if already entered
    already_entered = registration.get('attendance_status') == 'entered'
    
    return render_template('admin/verify_entry.html',
                         event=event,
                         registration=registration,
                         already_entered=already_entered)

@app.route('/admin/mark-entry', methods=['POST'])
@admin_required
def admin_mark_entry():
    """Mark attendee as entered"""
    regid = request.form.get('regid')
    email = request.form.get('email')
    event_id = request.form.get('event_id')
    
    if not regid or not email or not event_id:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        event_id = int(event_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid event ID'}), 400
    
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    
    event = next((e for e in EVENTS if e.get('id') == event_id), None)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Load registrations
    registrations = []
    reg_file_path = None
    if event.get('registration_file'):
        reg_file_path = os.path.join(PROJECT_ROOT, event['registration_file'])
        if os.path.exists(reg_file_path):
            with open(reg_file_path, 'r') as f:
                registrations = json.load(f)
    else:
        event_slug = slugify(event.get('name', ''))
        reg_file_path = os.path.join(PROJECT_ROOT, 'data', 'registrations', f'{event_slug}_registrations.json')
        if os.path.exists(reg_file_path):
            with open(reg_file_path, 'r') as f:
                registrations = json.load(f)
    
    # Find and update the registration
    updated = False
    for reg in registrations:
        if reg.get('registration_id') == regid and reg.get('submitter_email', '').lower() == email.lower():
            # Check if already entered
            if reg.get('attendance_status') == 'entered':
                return jsonify({'error': 'Already marked as entered', 'already_entered': True}), 400
            
            # Mark as entered
            reg['attendance_status'] = 'entered'
            reg['entry_time'] = datetime.now().isoformat()
            reg['marked_by'] = ADMIN_USERNAME  # Current admin
            updated = True
            break
    
    if not updated:
        return jsonify({'error': 'Registration not found'}), 404
    
    # Save updated registrations
    try:
        with open(reg_file_path, 'w') as f:
            json.dump(registrations, f, indent=4)
        return jsonify({'success': True, 'message': 'Entry marked successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to save entry'}), 500

@app.route('/admin/events/<int:event_id>/registrations/export')
@admin_required
def admin_export_registrations(event_id):
    """Export registrations to Excel"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from flask import send_file
        from io import BytesIO
    except ImportError:
        flash('Please install openpyxl: pip install openpyxl', 'error')
        return redirect(url_for('admin_view_registrations', event_id=event_id))
    
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY
    CLUB_INFO, EVENTS, MEMBERS, GALLERY = load_data()
    
    event = next((e for e in EVENTS if e.get('id') == event_id), None)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('admin_events'))
    
    # Load form template if assigned
    template = None
    if event.get('template_id'):
        templates_file = os.path.join(PROJECT_ROOT, 'data', 'form_templates.json')
        try:
            with open(templates_file, 'r') as f:
                templates = json.load(f)
            template = next((t for t in templates if t.get('id') == event.get('template_id')), None)
        except:
            pass
    
    if not template:
        flash('No form template found for this event.', 'error')
        return redirect(url_for('admin_view_registrations', event_id=event_id))
    
    # Load registrations
    registrations = []
    if event.get('registration_file'):
        reg_file = os.path.join(PROJECT_ROOT, event['registration_file'])
        if os.path.exists(reg_file):
            with open(reg_file, 'r') as f:
                registrations = json.load(f)
    else:
        # Fallback to old naming convention for backwards compatibility
        event_slug = slugify(event.get('name', ''))
        reg_file = os.path.join(PROJECT_ROOT, 'data', 'registrations', f'{event_slug}_registrations.json')
        if os.path.exists(reg_file):
            with open(reg_file, 'r') as f:
                registrations = json.load(f)
    
    if not registrations:
        flash('No registrations to export.', 'error')
        return redirect(url_for('admin_view_registrations', event_id=event_id))
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'Registrations'
    
    # Header style
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    header_alignment = Alignment(horizontal='center', vertical='center')
    
    # Create headers
    headers = ['#', 'Timestamp', 'Submitter Email'] + [field.get('label') for field in template.get('fields', [])] + ['Payment Status', 'Attendance Status', 'Entry Time']
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
    
    # Add data rows
    for row_num, reg in enumerate(registrations, 2):
        ws.cell(row=row_num, column=1, value=reg.get('id', row_num - 1))
        ws.cell(row=row_num, column=2, value=reg.get('timestamp', ''))
        ws.cell(row=row_num, column=3, value=reg.get('submitter_email', '-'))
        
        for col_num, field in enumerate(template.get('fields', []), 4):
            value = reg.get(field.get('name'), '')
            ws.cell(row=row_num, column=col_num, value=str(value) if value else '-')
        
        # Add payment status, attendance status, and entry time
        payment_col = len(template.get('fields', [])) + 4  # After submitter email and form fields
        payment_status = reg.get('payment_status', 'not_required')
        ws.cell(row=row_num, column=payment_col, value=payment_status)
        
        attendance_col = payment_col + 1
        attendance_status = reg.get('attendance_status', 'not_entered')
        ws.cell(row=row_num, column=attendance_col, value=attendance_status)
        
        entry_time_col = payment_col + 2
        entry_time = reg.get('entry_time', '-')
        ws.cell(row=row_num, column=entry_time_col, value=entry_time)
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Generate filename
    filename = f"{event.get('name', 'event').replace(' ', '_')}_registrations.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

