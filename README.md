# AICC - AI Coding Club Website

A modern, responsive Flask-based website for the AI Coding Club at KEC. Features a comprehensive admin panel for easy content management and a beautiful gradient-based UI.

## Features

### Frontend Features
- 🎨 Modern, gradient-based UI with dark/light theme support
- 📱 Fully responsive design for all devices (mobile, tablet, desktop)
- ⚡ Fast and lightweight with optimized assets
- 🌙 Automatic theme switching based on user preference
- 🖼️ Gallery with lightbox effect and category filtering
- 📅 Event showcase with countdown timers and status badges
- 👥 Members directory with social links (LinkedIn, GitHub)
- 📊 Dynamic event status tracking (upcoming, ongoing, completed)

### Admin Panel Features
- 🔒 Secure login with session management
- 📝 CRUD operations for all content (events, members, gallery, club info)
- 📤 File upload system for images
- 🎯 Real-time data editing through JSON files
- 🔄 Automatic data reloading without server restart
- 🖼️ Image management with secure file handling
- 📊 Dashboard overview of all club data
- 🎨 Clean admin interface with responsive design

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd AICC
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows:** `venv\Scripts\activate`
   - **Linux/Mac:** `source venv/bin/activate`

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Open your browser:**
   ```
   http://localhost:5000
   ```

The application will run on port 5000 by default. Visit the homepage to see the club website!

## Admin Panel

The admin panel provides a complete content management system accessible at `/admin/login`.

### Default Credentials
**⚠️ IMPORTANT: Change these in production!**
- **Username:** `admin`
- **Password:** `password`

These credentials are set in [app.py](app.py#L48-L49). For production, use environment variables or a database.

### Admin Features

#### Dashboard (`/admin`)
- Overview of all club data
- Quick access to all admin sections
- Real-time statistics

#### Club Info Management (`/admin/club-info`)
- Edit club name, tagline, and description
- Update college and department information
- Manage club logo

#### Events Management (`/admin/events`)
- Create new events with detailed information
- Edit existing events
- Delete events
- Upload event posters
- Set registration deadlines
- Manage event coordinators
- Update event status (upcoming/ongoing/completed)

#### Members Management (`/admin/members`)
- Add new members with photos
- Edit member information
- Delete members
- Manage social links (LinkedIn, GitHub)
- Update member roles and domains

#### Gallery Management (`/admin/gallery`)
- Upload photos with descriptions
- Categorize gallery items
- Delete gallery photos
- Bulk image management

#### Contact Info (`/admin/contact`)
- Update contact email
- Manage social media links
- Edit faculty coordinators
- Update student secretaries

## Configuration & Data Management

All club data is managed through JSON files in the `data/` directory. The admin panel provides a user-friendly interface for editing this data, or you can manually edit the files.

### Club Information (`data/club_info.json`)
```json
{
    "name": "AI Coding Club",
    "short_name": "AICC",
    "tagline": "Innovate. Code. Transform.",
    "description": "The AI Coding Club empowers students...",
    "college": "Kongu Engineering College",
    "department": "Computer Science and Engineering",
    "address": "Perundurai, Erode - 638060",
    "logo": "/static/img/aicc-logo.webp"
}
```

### Events (`data/events.json`)
Each event includes:
```json
[
    {
        "id": 1,
        "name": "Event Name",
        "date": "2026-02-15",
        "time": "10:00 AM - 4:00 PM",
        "location": "Main Auditorium",
        "description": "Detailed event description...",
        "how": "How the event works...",
        "rules": ["Rule 1", "Rule 2", "Rule 3"],
        "coordinators": [
            {
                "name": "Coordinator Name",
                "role": "Event Lead",
                "phone": "+91 98765 43210",
                "email": "coordinator@kec.edu"
            }
        ],
        "status": "upcoming",
        "image": "/static/img/poster/event.jpg",
        "register_link": "https://forms.google.com/...",
        "registration_deadline": {
            "date": "2026-02-10",
            "message": "Register before Feb 10, 2026"
        }
    }
]
```

**Event Status Options:**
- `upcoming` - Event is scheduled for the future
- `ongoing` - Event is currently happening
- `completed` - Event has finished

### Members (`data/members.json`)
```json
[
    {
        "name": "Member Name",
        "role": "President / Vice President / Secretary / Member",
        "year": "3rd Year / 4th Year",
        "domain": "AI/ML / Web Development / App Development",
        "image": "/static/img/members/member.jpg",
        "linkedin": "https://linkedin.com/in/username",
        "github": "https://github.com/username"
    }
]
```

### Contact Information (`data/contact_info.json`)
```json
{
    "email": "kecaicodingclub@gmail.com",
    "linkedin": "https://linkedin.com/company/aicc",
    "instagram": "https://www.instagram.com/kec_aicc",
    "facebook": "https://facebook.com/aicc",
    "faculty_coordinators": [
        {
            "name": "Dr. Faculty Name",
            "phone": "+91 12345 67890"
        }
    ],
    "secretaries": [
        {
            "name": "Student Secretary",
            "phone": "+91 98765 43210"
        }
    ]
}
```

### Gallery (`data/gallery.json`)
```json
[
    {
        "title": "Event/Activity Name",
        "description": "Photo description",
        "image": "/static/img/life/photo.jpg",
        "category": "event / workshop / hackathon / club-life"
    }
]
```

## Project Structure

```
AICC/
├── app.py                 # Main Flask application (703 lines)
├── config.py              # Configuration loader
├── requirements.txt       # Python dependencies
├── .gitignore             # Git ignore file
├── README.md              # This file
├── data/                  # JSON data files
│   ├── club_info.json     # Club information
│   ├── contact_info.json  # Contact details
│   ├── events.json        # Events data
│   ├── members.json       # Members data
│   ├── gallery.json       # Gallery photos
│   └── README.md          # Data directory documentation
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Base template with navbar & footer
│   ├── index.html         # Homepage
│   ├── about.html         # About page
│   ├── events.html        # Events listing
│   ├── event_detail.html  # Individual event page
│   ├── members.html       # Members showcase
│   ├── gallery.html       # Photo gallery
│   └── admin/             # Admin panel templates
│       ├── dashboard.html      # Admin dashboard
│       ├── login.html          # Admin login
│       ├── club_info.html      # Club info editor
│       ├── events.html         # Events management
│       ├── edit_event.html     # Event editor
│       ├── members.html        # Members management
│       ├── edit_member.html    # Member editor
│       ├── gallery.html        # Gallery management
│       ├── edit_gallery.html   # Gallery editor
│       └── contact.html        # Contact info editor
└── static/                # Static assets
    ├── css/
    │   ├── style.css      # Main stylesheet
    │   └── admin.css      # Admin panel styles
    ├── js/
    │   ├── main.js        # Frontend JavaScript
    │   └── admin-theme.js # Admin theme toggle
    ├── img/               # Images directory
    │   ├── poster/        # Event posters
    │   ├── members/       # Member photos
    │   └── life/          # Gallery images
    └── uploads/           # User uploaded files
        └── .gitkeep
```

## File Upload & Image Management

### Supported Image Formats
- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)
- GIF (`.gif`)
- WebP (`.webp`)

### Upload Limits
- Maximum file size: **16MB**
- Files are automatically renamed for security
- Images are stored in appropriate directories

### Image Directories
1. **Event Posters:** `static/img/poster/` - Add event poster images here
2. **Member Photos:** `static/img/members/` - Add member profile pictures here
3. **Gallery Photos:** `static/img/life/` - Add gallery/event photos here
4. **Club Logo:** Update in `data/club_info.json`

### Using the Admin Panel for Uploads
The admin panel (`/admin/upload`) provides a secure file upload interface that:
- Validates file types and sizes
- Automatically handles file naming
- Updates JSON data files
- Provides upload feedback

## Page Routes

### Public Routes
- `/` - Homepage with hero section and featured events
- `/about` - About the club page
- `/events` - All events listing
- `/events/<id>` - Individual event details
- `/members` - Members showcase page
- `/gallery` - Photo gallery with categories

### API Endpoints
- `/api/events` - JSON API for events data
- `/api/members` - JSON API for members data

### Admin Routes (Authentication Required)
- `/admin/login` - Admin login page
- `/admin` - Admin dashboard
- `/admin/club-info` - Edit club information
- `/admin/events` - Manage events (list, create, edit, delete)
- `/admin/events/<id>/edit` - Edit specific event
- `/admin/events/<id>/delete` - Delete specific event
- `/admin/members` - Manage members (list, create, edit, delete)
- `/admin/members/<index>/edit` - Edit specific member
- `/admin/members/<index>/delete` - Delete specific member
- `/admin/gallery` - Manage gallery photos
- `/admin/contact` - Edit contact information
- `/admin/upload` - File upload endpoint
- `/admin/logout` - Logout from admin panel

## Customization

### Styling & Theming
- **Main Stylesheet:** [static/css/style.css](static/css/style.css)
  - Modern gradient-based design
  - CSS custom properties for easy theming
  - Responsive breakpoints
  - Dark/light theme support

- **Admin Stylesheet:** [static/css/admin.css](static/css/admin.css)
  - Clean admin interface
  - Consistent with main site design
  - Form styling and layouts

### Color Customization
Edit CSS custom properties in [static/css/style.css](static/css/style.css):
```css
:root {
    --primary-color: #your-color;
    --secondary-color: #your-color;
    --accent-color: #your-color;
}
```

### JavaScript Features
- **Theme Toggle:** Automatic dark/light mode switching
- **Lightbox Gallery:** Click to expand gallery images
- **Smooth Scrolling:** Enhanced navigation experience
- **Form Validation:** Client-side form validation
- **Dynamic Loading:** AJAX-based content updates

## Security & Best Practices

### Production Security Checklist
⚠️ **Before deploying to production:**

1. **Change Default Credentials**
   - Update `ADMIN_USERNAME` and `ADMIN_PASSWORD` in [app.py](app.py)
   - Use strong, unique passwords
   - Consider implementing database-backed authentication

2. **Secure Secret Key**
   - Generate a strong secret key: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Set `app.secret_key` in [app.py](app.py)
   - Use environment variables: `os.environ.get('SECRET_KEY')`

3. **Environment Variables**
   ```python
   # Use environment variables for sensitive data
   app.secret_key = os.environ.get('SECRET_KEY', 'dev-key')
   ADMIN_USERNAME = os.environ.get('ADMIN_USER', 'admin')
   ADMIN_PASSWORD = os.environ.get('ADMIN_PASS', 'password')
   ```

4. **Disable Debug Mode**
   - Set `debug=False` in [app.py](app.py#L703)
   - Use a production WSGI server (Gunicorn, uWSGI)

5. **Additional Security Measures**
   - Enable HTTPS/SSL
   - Implement rate limiting for login attempts
   - Add CSRF protection
   - Set secure session cookies
   - Implement file upload validation
   - Add input sanitization

### File Upload Security
The application includes:
- File extension validation
- File size limits (16MB max)
- Secure filename handling with `secure_filename()`
- Restricted upload directories

## Deployment

### Local Development
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run development server
python app.py
```
Access at: `http://localhost:5000`

### Production Deployment

#### Option 1: Gunicorn (Linux/Mac)
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

#### Option 2: Waitress (Windows/Cross-platform)
```bash
# Install Waitress
pip install waitress

# Run with Waitress
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

#### Option 3: Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

#### Nginx Reverse Proxy Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/AICC/static;
        expires 30d;
    }
}
```

### Environment Setup for Production
Create a `.env` file:
```bash
SECRET_KEY=your-super-secret-key-here
ADMIN_USER=your-admin-username
ADMIN_PASS=your-secure-password
FLASK_ENV=production
```

Load environment variables in [app.py](app.py):
```python
from dotenv import load_dotenv
load_dotenv()
```

## Technology Stack

- **Backend:** Flask 3.0.0 (Python web framework)
- **Template Engine:** Jinja2 (comes with Flask)
- **Data Storage:** JSON files (file-based database)
- **Frontend:** HTML5, CSS3, JavaScript (ES6+)
- **Styling:** Custom CSS with CSS Grid & Flexbox
- **Icons & Fonts:** Font Awesome, Google Fonts
- **Security:** Werkzeug 3.0.1 (secure filename handling)

### Dependencies
```
Flask==3.0.0
Werkzeug==3.0.1
```

## Features in Detail

### Event Management
- Create, edit, and delete events
- Event status tracking (upcoming/ongoing/completed)
- Registration deadlines with countdown
- Event coordinators with contact info
- Event rules and "How it works" sections
- Image upload for event posters
- Registration links integration

### Member Management
- Add/edit/delete member profiles
- Role-based organization (President, VP, Secretary, etc.)
- Domain expertise tagging (AI/ML, Web Dev, etc.)
- Social media integration (LinkedIn, GitHub)
- Profile pictures with upload support
- Year and department tracking

### Gallery System
- Category-based photo organization
- Lightbox view for images
- Photo descriptions and titles
- Multiple categories (events, workshops, hackathons, club-life)
- Bulk upload support via admin panel

### Admin Dashboard Features
- Centralized content management
- Real-time data updates
- Session-based authentication
- Responsive admin interface
- File upload handling
- Data persistence via JSON files
- Cache busting for updated content

## Troubleshooting

### Common Issues

**Issue:** Port 5000 already in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

**Issue:** Images not loading
- Check file paths in JSON files
- Ensure images are in correct directories
- Verify file extensions are supported
- Clear browser cache

**Issue:** Admin login not working
- Verify credentials in [app.py](app.py#L48-L49)
- Check if session is enabled
- Clear browser cookies

**Issue:** Changes not reflecting
- Reload JSON data (restart server or use admin panel)
- Clear browser cache (Ctrl+F5)
- Check file permissions

## API Documentation

### GET `/api/events`
Returns all events as JSON.

**Response:**
```json
[
    {
        "id": 1,
        "name": "Event Name",
        "date": "2026-02-15",
        "status": "upcoming",
        ...
    }
]
```

### GET `/api/members`
Returns all members as JSON.

**Response:**
```json
[
    {
        "name": "Member Name",
        "role": "President",
        "domain": "AI/ML",
        ...
    }
]
```

## Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Commit your changes:** `git commit -m 'Add amazing feature'`
4. **Push to branch:** `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Contribution Guidelines
- Follow existing code style
- Add comments for complex logic
- Test your changes thoroughly
- Update documentation as needed
- Keep commits focused and descriptive

## License

This project is open source and available under the MIT License.

### MIT License
```
Copyright (c) 2026 AI Coding Club, Kongu Engineering College

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

## Support & Contact

### AI Coding Club - KEC
- **Email:** kecaicodingclub@gmail.com
- **Instagram:** [@kec_aicc](https://www.instagram.com/kec_aicc)
- **College:** Kongu Engineering College, Perundurai, Erode

### Getting Help
- Check the [documentation](#configuration--data-management)
- Review [troubleshooting section](#troubleshooting)
- Open an issue on GitHub
- Contact the club via email or social media

## Roadmap

Future enhancements planned:
- [ ] Database integration (SQLite/PostgreSQL)
- [ ] User authentication for event registration
- [ ] Email notifications for events
- [ ] Blog/news section
- [ ] SEO optimization
- [ ] Analytics dashboard
- [ ] Multi-language support
- [ ] PWA support for mobile
- [ ] Advanced search and filtering
- [ ] Integration with Google Calendar

## Acknowledgments

Built with ❤️ by the AI Coding Club team at Kongu Engineering College.

Special thanks to all contributors and club members who made this project possible.

---

**Version:** 1.0.0  
**Last Updated:** January 2026  
**Maintained by:** AI Coding Club, KEC
