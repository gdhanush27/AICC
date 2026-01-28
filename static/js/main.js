// Mobile Navigation Toggle
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');

if (navToggle) {
    navToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        
        // Animate hamburger
        const spans = navToggle.querySelectorAll('span');
        if (navMenu.classList.contains('active')) {
            spans[0].style.transform = 'rotate(45deg) translateY(12px)';
            spans[1].style.opacity = '0';
            spans[2].style.transform = 'rotate(-45deg) translateY(-12px)';
        } else {
            spans[0].style.transform = 'none';
            spans[1].style.opacity = '1';
            spans[2].style.transform = 'none';
        }
    });
}

// Theme Toggle
const themeToggle = document.getElementById('theme-toggle-main');
const body = document.body;

// Check for saved theme preference or default to 'light'
const currentTheme = localStorage.getItem('theme') || 'light';
body.setAttribute('data-theme', currentTheme);
updateThemeIcon(currentTheme);

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
    if (theme === 'dark') {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    }
}

// Close mobile menu when clicking on a link
const navLinks = document.querySelectorAll('.nav-link');
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        if (navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            const spans = navToggle.querySelectorAll('span');
            spans[0].style.transform = 'none';
            spans[1].style.opacity = '1';
            spans[2].style.transform = 'none';
        }
    });
});

// Highlight active nav link based on current page
const currentPath = window.location.pathname;
navLinks.forEach(link => {
    if (link.getAttribute('href') === currentPath || 
        (currentPath === '/' && link.getAttribute('href') === '/')) {
        link.style.color = 'var(--primary-color)';
        link.style.background = 'rgba(99, 102, 241, 0.1)';
    }
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar scroll effect
let lastScroll = 0;
const navbar = document.querySelector('.navbar');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        navbar.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.boxShadow = 'none';
    }
    
    lastScroll = currentScroll;
});

// Intersection Observer for fade-in animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Helper function to check if element is in viewport
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Display all elements immediately without scroll animations
document.querySelectorAll('.section, .event-card, .stat-card, .member-card').forEach(el => {
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
});

// Parallax effect for hero background
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const hero = document.querySelector('.hero-background');
    if (hero) {
        hero.style.transform = `translateY(${scrolled * 0.5}px)`;
    }
});

// Add loading animation
window.addEventListener('load', () => {
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease';
        document.body.style.opacity = '1';
    }, 100);
});

// Console easter egg
console.log('%c Welcome to AI Coding Club! ', 'background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; font-size: 20px; padding: 10px; border-radius: 5px;');
console.log('%c Interested in joining? Contact us! ', 'background: #1e293b; color: #cbd5e1; font-size: 14px; padding: 5px;');

// ========================================
// Registration Form Enhancements
// ========================================

// Form validation and real-time feedback
document.addEventListener('DOMContentLoaded', function() {
    const registrationForm = document.getElementById('registrationForm');
    
    if (registrationForm) {
        // Add input event listeners for real-time validation
        const formInputs = registrationForm.querySelectorAll('.form-input');
        
        formInputs.forEach(input => {
            // Add focus animation
            input.addEventListener('focus', function() {
                this.closest('.form-group').classList.add('focused');
                animateProgressDot();
            });
            
            input.addEventListener('blur', function() {
                this.closest('.form-group').classList.remove('focused');
                validateField(this);
            });
            
            // Real-time validation as user types
            input.addEventListener('input', function() {
                if (this.value.length > 0) {
                    validateField(this);
                }
            });
        });
        
        // Character counter for textarea
        const textareas = registrationForm.querySelectorAll('textarea.form-input');
        textareas.forEach(textarea => {
            const maxLength = textarea.getAttribute('maxlength');
            if (maxLength) {
                const counter = document.createElement('div');
                counter.className = 'char-counter';
                counter.style.cssText = 'text-align: right; font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem;';
                textarea.parentNode.appendChild(counter);
                
                textarea.addEventListener('input', function() {
                    const remaining = maxLength - this.value.length;
                    counter.textContent = `${this.value.length} / ${maxLength} characters`;
                    counter.style.color = remaining < 50 ? 'var(--warning)' : 'var(--text-secondary)';
                });
                
                // Initialize counter
                counter.textContent = `0 / ${maxLength} characters`;
            }
        });
    }
});

// Field validation function
function validateField(field) {
    const value = field.value.trim();
    const fieldType = field.type;
    const fieldName = field.name;
    let isValid = true;
    let errorMessage = '';
    
    // Remove existing error message
    const existingError = field.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Email validation
    if (fieldType === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    // Phone validation
    if (fieldType === 'tel' && value) {
        const phoneRegex = /^[0-9]{10}$/;
        if (!phoneRegex.test(value.replace(/[\s\-\(\)]/g, ''))) {
            isValid = false;
            errorMessage = 'Please enter a valid 10-digit phone number';
        }
    }
    
    // Display validation state
    if (!isValid && value) {
        field.style.borderColor = 'var(--danger)';
        field.style.background = 'rgba(239, 68, 68, 0.05)';
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = 'color: var(--danger); font-size: 0.85rem; margin-top: 0.5rem; display: flex; align-items: center; gap: 0.5rem;';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i>${errorMessage}`;
        field.parentNode.appendChild(errorDiv);
    } else if (value) {
        field.style.borderColor = 'var(--success)';
        field.style.background = 'rgba(16, 185, 129, 0.05)';
    } else {
        field.style.borderColor = 'var(--border-color)';
        field.style.background = 'var(--dark-bg)';
    }
    
    return isValid;
}

// Animate progress dots
function animateProgressDot() {
    const progressDots = document.querySelectorAll('.progress-dot');
    if (progressDots.length === 0) return;
    
    const registrationForm = document.getElementById('registrationForm');
    if (!registrationForm) return;
    
    const totalFields = registrationForm.querySelectorAll('.form-input[required]').length;
    const filledFields = Array.from(registrationForm.querySelectorAll('.form-input[required]'))
        .filter(input => input.value.trim() !== '').length;
    
    const progress = Math.min(Math.floor((filledFields / totalFields) * progressDots.length), progressDots.length);
    
    progressDots.forEach((dot, index) => {
        if (index < progress) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

// Add floating label effect
function addFloatingLabels() {
    const formGroups = document.querySelectorAll('.form-group');
    
    formGroups.forEach(group => {
        const input = group.querySelector('.form-input');
        const label = group.querySelector('.form-label');
        
        if (input && label) {
            input.addEventListener('focus', () => {
                label.style.color = 'var(--primary-color)';
                label.style.transform = 'translateY(-2px)';
                label.style.transition = 'all 0.3s ease';
            });
            
            input.addEventListener('blur', () => {
                if (!input.value) {
                    label.style.color = 'var(--text-primary)';
                    label.style.transform = 'translateY(0)';
                }
            });
        }
    });
}

// Call floating labels on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addFloatingLabels);
} else {
    addFloatingLabels();
}

// Add confetti animation on successful submission
function showConfetti() {
    const duration = 3 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 };
    
    function randomInRange(min, max) {
        return Math.random() * (max - min) + min;
    }
    
    const interval = setInterval(function() {
        const timeLeft = animationEnd - Date.now();
        
        if (timeLeft <= 0) {
            return clearInterval(interval);
        }
        
        const particleCount = 50 * (timeLeft / duration);
        
        // Create simple confetti effect with DOM elements
        for (let i = 0; i < 3; i++) {
            const confetti = document.createElement('div');
            confetti.style.cssText = `
                position: fixed;
                width: 10px;
                height: 10px;
                background: ${['var(--primary-color)', 'var(--secondary-color)', 'var(--accent-color)', 'var(--success)'][Math.floor(Math.random() * 4)]};
                top: -10px;
                left: ${randomInRange(0, 100)}%;
                animation: confettiFall ${randomInRange(2, 4)}s linear;
                z-index: 9999;
                border-radius: 50%;
            `;
            document.body.appendChild(confetti);
            
            setTimeout(() => confetti.remove(), 4000);
        }
    }, 250);
}

// Add CSS animation for confetti
const style = document.createElement('style');
style.textContent = `
    @keyframes confettiFall {
        to {
            transform: translateY(100vh) rotate(360deg);
            opacity: 0;
        }
    }
    
    .form-group.focused {
        transform: scale(1.01);
        transition: transform 0.3s ease;
    }
    
    .form-input:focus {
        animation: inputPulse 0.5s ease;
    }
    
    @keyframes inputPulse {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-2px); }
    }
`;
document.head.appendChild(style);

// Enhanced form submission with better feedback
document.addEventListener('DOMContentLoaded', function() {
    const registrationForm = document.getElementById('registrationForm');
    
    if (registrationForm) {
        registrationForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            const successMsg = document.getElementById('successMessage');
            const errorMsg = document.getElementById('errorMessage');
            const errorText = document.getElementById('errorText');
            
            // Validate all fields before submission
            const formInputs = this.querySelectorAll('.form-input[required]');
            let allValid = true;
            
            formInputs.forEach(input => {
                if (!validateField(input)) {
                    allValid = false;
                }
            });
            
            if (!allValid) {
                errorText.textContent = 'Please fill in all required fields correctly';
                errorMsg.classList.remove('hidden');
                errorMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });
                return;
            }
            
            // Show loading state
            submitBtn.disabled = true;
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
            submitBtn.style.opacity = '0.7';
            
            // Hide previous messages
            successMsg.classList.add('hidden');
            errorMsg.classList.add('hidden');
            
            try {
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                const response = await fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    // Show success message
                    successMsg.classList.remove('hidden');
                    this.reset();
                    
                    // Reset validation states
                    formInputs.forEach(input => {
                        input.style.borderColor = 'var(--border-color)';
                        input.style.background = 'var(--dark-bg)';
                    });
                    
                    // Show confetti
                    showConfetti();
                    
                    // Scroll to success message
                    successMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    
                    // Reset progress dots
                    document.querySelectorAll('.progress-dot').forEach(dot => {
                        dot.classList.remove('active');
                    });
                    
                } else {
                    const result = await response.json().catch(() => ({}));
                    if (result.error) {
                        errorText.textContent = result.error + (result.missing ? `: ${result.missing.join(', ')}` : '');
                    } else {
                        errorText.textContent = 'An error occurred. Please try again.';
                    }
                    errorMsg.classList.remove('hidden');
                    errorMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            } catch (error) {
                console.error('Error:', error);
                errorText.textContent = 'Network error. Please check your connection and try again.';
                errorMsg.classList.remove('hidden');
                errorMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } finally {
                // Re-enable submit button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                submitBtn.style.opacity = '1';
            }
        });
    }
});

// ========================================
// Scroll to Top Button
// ========================================
const scrollToTopBtn = document.createElement('button');
scrollToTopBtn.className = 'scroll-to-top';
scrollToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
scrollToTopBtn.setAttribute('aria-label', 'Scroll to top');
document.body.appendChild(scrollToTopBtn);

window.addEventListener('scroll', () => {
    if (window.pageYOffset > 300) {
        scrollToTopBtn.classList.add('visible');
    } else {
        scrollToTopBtn.classList.remove('visible');
    }
});

scrollToTopBtn.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

// ========================================
// Flash Messages Auto-Dismiss
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach((message, index) => {
        // Auto-dismiss after 5 seconds (staggered by 100ms each)
        setTimeout(() => {
            message.classList.add('dismissing');
            setTimeout(() => {
                message.remove();
            }, 300); // Match the animation duration
        }, 5000 + (index * 100));
    });
});
