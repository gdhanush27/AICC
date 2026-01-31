"""
Configuration file for AI Coding Club website
Data is loaded from JSON files in the data/ folder
Edit JSON files to update events, members, and other details
"""

import json
import os

# Get the directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_json(filename):
    """Load JSON data from the data directory"""
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Using empty data.")
        return {} if 'info' in filename else []
    except json.JSONDecodeError as e:
        print(f"Error parsing {filename}: {e}")
        return {} if 'info' in filename else []

# Email validation settings
ALLOWED_EMAIL_DOMAINS = [
    'kongu.edu',
    'kongu.ac.in',
    'gmail.com'
]

# Note: Razorpay and Groq API keys are now stored in data/club_info.json
# and can be edited via the Admin Panel > Club Information

# Load all data from JSON files
CLUB_INFO = load_json('club_info.json')
EVENTS = load_json('events.json')
MEMBERS = load_json('members.json')
GALLERY = load_json('gallery.json')
