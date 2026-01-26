from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import json
import time

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
        print(f"✓ Directory ensured: {directory}")
    
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
        'data/gallery.json': [],
        'data/contact_info.json': {
            "email": "aicc@tce.edu",
            "instagram": "https://instagram.com/aicc_tce",
            "linkedin": "https://linkedin.com/company/aicc-tce",
            "faculty_coordinators": [],
            "secretaries": []
        }
    }
    
    for file_path, default_content in data_files.items():
        full_path = os.path.join(PROJECT_ROOT, file_path)
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                json.dump(default_content, f, indent=4)
            print(f"✓ Created: {file_path}")
        else:
            print(f"✓ File exists: {file_path}")
    
    print("✓ App structure initialized successfully!")

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
    with open(os.path.join(data_dir, 'contact_info.json'), 'r') as f:
        contact_info = json.load(f)
    return club_info, events, members, gallery, contact_info

# Load initial data
CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()

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

def delete_old_image(image_path):
    """Delete old image file if it exists in uploads folder"""
    if image_path and '/static/uploads/' in image_path:
        # Extract filename from path
        filename = image_path.split('/static/uploads/')[-1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Deleted old image: {filepath}")
        except Exception as e:
            print(f"Error deleting image {filepath}: {e}")

@app.route('/')
def home():
    """Home page with hero section and registration deadline"""
    # Reload data to get latest changes
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    
    # Sort events: with register_link first, then by status (upcoming first)
    sorted_events = sorted(EVENTS, key=lambda x: (
        not bool(x.get('register_link')),  # Events with register_link first
        x.get('status') != 'upcoming',     # Then upcoming events
        x.get('status') == 'completed'     # Then ongoing, then completed
    ))
    
    # Find the next event with an active registration deadline
    next_deadline_event = None
    for event in sorted_events:
        # Only consider upcoming or ongoing events
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
                        next_deadline_event = event
                        break
                except Exception as e:
                    print(f"Error parsing deadline date for event {event.get('name')}: {e}")
                    pass
    
    return render_template('index.html', 
                         club_info=CLUB_INFO, 
                         events=sorted_events[:3],  # Show only top 3 events on home
                         contact=CONTACT_INFO,
                         next_deadline_event=next_deadline_event)

@app.route('/about')
def about():
    """About page"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    return render_template('about.html', 
                         club_info=CLUB_INFO,
                         contact=CONTACT_INFO)

@app.route('/events')
def events():
    """Events page showing all events"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    # Sort events: with register_link first, then by status (upcoming first)
    sorted_events = sorted(EVENTS, key=lambda x: (
        not bool(x.get('register_link')),  # Events with register_link first
        x.get('status') != 'upcoming',     # Then upcoming events
        x.get('status') == 'completed'     # Then ongoing, then completed
    ))
    return render_template('events.html', 
                         events=sorted_events,
                         club_info=CLUB_INFO,
                         contact=CONTACT_INFO)

@app.route('/events/<int:event_id>')
def event_detail(event_id):
    """Individual event detail page"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    event = next((e for e in EVENTS if e.get('id') == event_id), None)
    if not event:
        return render_template('404.html'), 404
    return render_template('event_detail.html',
                         event=event,
                         club_info=CLUB_INFO,
                         contact=CONTACT_INFO)

@app.route('/members')
def members():
    """Members page showing team members"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    return render_template('members.html', 
                         members=MEMBERS,
                         club_info=CLUB_INFO,
                         contact=CONTACT_INFO)

@app.route('/gallery')
def gallery():
    """Life @ AICC gallery page"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    return render_template('gallery.html', 
                         gallery=GALLERY,
                         club_info=CLUB_INFO,
                         contact=CONTACT_INFO)

@app.route('/api/events')
def api_events():
    """API endpoint to get events data"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    return jsonify(EVENTS)

@app.route('/api/members')
def api_members():
    """API endpoint to get members data"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
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
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    return render_template('admin/dashboard.html',
                         events_count=len(EVENTS),
                         members_count=len(MEMBERS),
                         gallery_count=len(GALLERY),
                         gallery=GALLERY)

@app.route('/admin/club-info', methods=['GET', 'POST'])
@admin_required
def admin_club_info():
    """Edit club information"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    
    if request.method == 'POST':
        # Reload current club info
        CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
        
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
        
        data = {
            'name': request.form.get('name'),
            'short_name': request.form.get('short_name'),
            'tagline': request.form.get('tagline'),
            'description': request.form.get('description'),
            'college': request.form.get('college'),
            'department': request.form.get('department'),
            'address': request.form.get('address'),
            'logo': logo_url
        }
        
        with open(os.path.join(PROJECT_ROOT, 'data/club_info.json'), 'w') as f:
            json.dump(data, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
        
        flash('Club information updated successfully!', 'success')
        return redirect(url_for('admin_club_info'))
    
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    return render_template('admin/club_info.html', club_info=CLUB_INFO)

@app.route('/admin/events', methods=['GET', 'POST'])
@admin_required
def admin_events():
    """Manage events"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    
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
            'register_link': request.form.get('register_link'),
            'rules': request.form.get('rules', '').split('\n') if request.form.get('rules') else [],
            'coordinators': []
        }
        
        # Add registration deadline if provided
        deadline_date = request.form.get('deadline_date')
        deadline_message = request.form.get('deadline_message')
        if deadline_date and deadline_message:
            new_event['registration_deadline'] = {
                'date': deadline_date,
                'message': deadline_message
            }
        
        events.append(new_event)
        
        with open(os.path.join(PROJECT_ROOT, 'data/events.json'), 'w') as f:
            json.dump(events, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
        
        flash('Event added successfully!', 'success')
        return redirect(url_for('admin_events'))
    
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    return render_template('admin/events.html', events=EVENTS)

@app.route('/admin/events/<int:event_id>/delete', methods=['POST'])
@admin_required
def admin_delete_event(event_id):
    """Delete an event"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    
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
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin_events'))

@app.route('/admin/members', methods=['GET', 'POST'])
@admin_required
def admin_members():
    """Manage members"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    
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
        
        with open(os.path.join(PROJECT_ROOT, 'data/members.json'), 'w') as f:
            json.dump(members, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
        
        flash('Member added successfully!', 'success')
        return redirect(url_for('admin_members'))
    
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    return render_template('admin/members.html', members=MEMBERS)

@app.route('/admin/contact', methods=['GET', 'POST'])
@admin_required
def admin_contact():
    """Edit contact information"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    
    if request.method == 'POST':
        data = {
            'email': request.form.get('email'),
            'instagram': request.form.get('instagram'),
            'linkedin': request.form.get('linkedin'),
            'faculty_coordinators': CONTACT_INFO.get('faculty_coordinators', []),
            'secretaries': CONTACT_INFO.get('secretaries', [])
        }
        
        with open(os.path.join(PROJECT_ROOT, 'data/contact_info.json'), 'w') as f:
            json.dump(data, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
        
        flash('Contact information updated successfully!', 'success')
        return redirect(url_for('admin_contact'))
    
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    return render_template('admin/contact.html', contact=CONTACT_INFO)

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
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    
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
        event['register_link'] = request.form.get('register_link')
        event['rules'] = request.form.get('rules', '').split('\n') if request.form.get('rules') else []
        
        # Handle registration deadline
        deadline_date = request.form.get('deadline_date')
        deadline_message = request.form.get('deadline_message')
        if deadline_date and deadline_message:
            event['registration_deadline'] = {
                'date': deadline_date,
                'message': deadline_message
            }
        elif 'registration_deadline' in event:
            # Remove deadline if fields are empty
            del event['registration_deadline']
        
        with open(os.path.join(PROJECT_ROOT, 'data/events.json'), 'w') as f:
            json.dump(events, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
        
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin_events'))
    
    return render_template('admin/edit_event.html', event=event)

@app.route('/admin/members/<int:member_index>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_member(member_index):
    """Edit an existing member"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    
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
        
        with open(os.path.join(PROJECT_ROOT, 'data/members.json'), 'w') as f:
            json.dump(members, f, indent=4)
        
        # Reload data
        CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
        
        flash('Member updated successfully!', 'success')
        return redirect(url_for('admin_members'))
    
    return render_template('admin/edit_member.html', member=member, member_index=member_index)

@app.route('/admin/members/<int:member_index>/delete', methods=['POST'])
@admin_required
def admin_delete_member(member_index):
    """Delete a member"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    
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
        CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
        
        flash('Member deleted successfully!', 'success')
    
    return redirect(url_for('admin_members'))

@app.route('/admin/gallery', methods=['GET', 'POST'])
@admin_required
def admin_gallery():
    """Manage gallery images"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    
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
                CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
                
                flash('Image uploaded successfully!', 'success')
                return redirect(url_for('admin_gallery'))
    
    CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
    return render_template('admin/gallery.html', gallery=GALLERY)

@app.route('/admin/gallery/<int:image_index>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_gallery_image(image_index):
    """Edit a gallery image"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    
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
        CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
        
        flash('Image updated successfully!', 'success')
        return redirect(url_for('admin_gallery'))
    
    return render_template('admin/edit_gallery.html', image=image, image_index=image_index)

@app.route('/admin/gallery/<int:image_index>/delete', methods=['POST'])
@admin_required
def admin_delete_gallery_image(image_index):
    """Delete a gallery image"""
    global CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO
    
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
        CLUB_INFO, EVENTS, MEMBERS, GALLERY, CONTACT_INFO = load_data()
        
        flash('Image deleted successfully!', 'success')
    
    return redirect(url_for('admin_gallery'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
