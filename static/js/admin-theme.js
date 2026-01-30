// Admin Panel Theme Toggle
// Note: This file uses the same 'theme' localStorage key as main.js for consistency
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Check for saved theme preference or default to 'light'
    // Use 'theme' key for consistency across all pages
    const currentTheme = localStorage.getItem('theme') || 'light';
    body.setAttribute('data-theme', currentTheme);
    
    // Update toggle icon
    updateThemeIcon(currentTheme);
    
    // Theme toggle click handler
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const theme = body.getAttribute('data-theme');
            const newTheme = theme === 'dark' ? 'light' : 'dark';
            
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }
    
    function updateThemeIcon(theme) {
        if (!themeToggle) return;
        
        const icon = themeToggle.querySelector('i');
        // Icon shows what you'll switch TO: sun icon when in dark mode (click to go light)
        if (theme === 'dark') {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    }
});
