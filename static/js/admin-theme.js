// Admin Panel Theme Toggle
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Check for saved theme preference or default to 'light'
    const currentTheme = localStorage.getItem('adminTheme') || 'light';
    body.setAttribute('data-theme', currentTheme);
    
    // Update toggle icon
    updateThemeIcon(currentTheme);
    
    // Theme toggle click handler
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const theme = body.getAttribute('data-theme');
            const newTheme = theme === 'dark' ? 'light' : 'dark';
            
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('adminTheme', newTheme);
            updateThemeIcon(newTheme);
        });
    }
    
    function updateThemeIcon(theme) {
        if (!themeToggle) return;
        
        const icon = themeToggle.querySelector('i');
        if (theme === 'dark') {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    }
});
