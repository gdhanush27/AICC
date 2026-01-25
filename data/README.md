# Data Folder

This folder contains all the configurable data for the AI Coding Club website in JSON format.

## Files

- **club_info.json** - Club information, tagline, description, and registration deadline
- **contact_info.json** - Contact details, social media links, coordinators, and secretaries
- **events.json** - List of all events with dates, locations, and registration links
- **members.json** - Team members with their roles, years, and social links
- **gallery.json** - Gallery images for "Life @ AICC" section

## How to Update

1. Edit the JSON files directly
2. Make sure to maintain valid JSON syntax
3. Restart the Flask app to see changes

## JSON Format Examples

### Adding a New Event
Edit `events.json` and add:
```json
{
    "id": 7,
    "name": "Event Name",
    "date": "March 15, 2026",
    "time": "10:00 AM",
    "location": "AI BLOCK",
    "description": "Event description here",
    "status": "upcoming",
    "image": "/static/img/poster/event.webp",
    "register_link": "https://registration-link.com"
}
```

### Adding a New Member
Edit `members.json` and add:
```json
{
    "name": "Member Name",
    "role": "Executive Member",
    "year": "2nd Year",
    "domain": "AI/ML",
    "image": "/static/img/members/member.webp",
    "linkedin": "https://linkedin.com/in/username",
    "github": "https://github.com/username"
}
```

### Adding a Gallery Image
Edit `gallery.json` and add:
```json
{
    "title": "2025-2026",
    "description": "Event description",
    "image": "/static/img/life/image.webp"
}
```

## Notes

- Event status can be: `upcoming`, `ongoing`, or `completed`
- Make sure image paths match your actual image files
- Keep proper JSON formatting (commas, brackets, quotes)
