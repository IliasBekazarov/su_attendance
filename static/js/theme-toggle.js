// Theme Toggle Functionality
class ThemeToggle {
    constructor() {
        this.theme = this.getTheme();
        this.init();
    }

    init() {
        // Apply the theme immediately on page load
        this.applyTheme(this.theme);
        
        // Set up event listeners when DOM is ready
        this.setupEventListeners();
    }

    getTheme() {
        // Check localStorage first
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme;
        }
        
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        return 'light';
    }

    applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        
        // Save to localStorage
        localStorage.setItem('theme', theme);
        this.theme = theme;
        
        // Update toggle button icon
        this.updateToggleIcon();
    }

    createToggleButton() {
        const toggleButton = document.createElement('button');
        toggleButton.className = 'theme-toggle btn';
        toggleButton.setAttribute('type', 'button');
        toggleButton.setAttribute('title', 'Toggle theme');
        toggleButton.innerHTML = '<i class="fas fa-sun"></i>';
        toggleButton.id = 'theme-toggle';
        
        return toggleButton;
    }

    updateToggleIcon() {
        // Try to find the theme icon by its ID first
        let themeIcon = document.getElementById('theme-icon');
        
        // If not found, try to find it within the toggle button
        if (!themeIcon) {
            const toggleButton = document.getElementById('theme-toggle');
            if (toggleButton) {
                themeIcon = toggleButton.querySelector('i');
            }
        }
        
        if (themeIcon) {
            if (this.theme === 'dark') {
                themeIcon.className = 'fas fa-moon';
                themeIcon.setAttribute('title', 'Switch to light mode');
            } else {
                themeIcon.className = 'fas fa-sun';
                themeIcon.setAttribute('title', 'Switch to dark mode');
            }
        } else {
            console.warn('Theme icon not found');
        }

        // Also update the button title
        const toggleButton = document.getElementById('theme-toggle');
        if (toggleButton) {
            if (this.theme === 'dark') {
                toggleButton.setAttribute('title', 'Switch to light mode');
            } else {
                toggleButton.setAttribute('title', 'Switch to dark mode');
            }
        }
    }

    setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Function to handle the theme toggle
        const handleThemeToggle = (event) => {
            console.log('Theme toggle clicked!');
            event.preventDefault();
            event.stopPropagation();
            this.toggleTheme();
        };
        
        // Wait a bit for DOM to be fully ready
        const setupListeners = () => {
            const toggleButton = document.getElementById('theme-toggle');
            console.log('Looking for theme toggle button...', toggleButton);
            
            if (toggleButton) {
                // Remove any existing listeners
                toggleButton.removeEventListener('click', handleThemeToggle);
                
                // Add the click listener
                toggleButton.addEventListener('click', handleThemeToggle);
                console.log('Event listener attached to theme toggle button');
                
                // Test that the button is clickable
                console.log('Button is clickable:', !toggleButton.disabled);
                console.log('Button display style:', window.getComputedStyle(toggleButton).display);
                
                return true;
            }
            return false;
        };
        
        // Try to set up listeners immediately
        if (!setupListeners()) {
            // If button not found, try again after a short delay
            setTimeout(() => {
                if (!setupListeners()) {
                    console.error('Failed to find theme toggle button after multiple attempts');
                }
            }, 500);
        }
        
        // Also set up event delegation as a backup
        document.addEventListener('click', (event) => {
            if (event.target.closest('#theme-toggle')) {
                console.log('Theme toggle clicked via event delegation!');
                event.preventDefault();
                event.stopPropagation();
                this.toggleTheme();
            }
        });
    }

    toggleTheme() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        
        // Add animation effect
        const toggleButton = document.getElementById('theme-toggle');
        if (toggleButton) {
            toggleButton.style.transform = 'rotate(360deg)';
            setTimeout(() => {
                toggleButton.style.transform = '';
            }, 300);
        }
    }

    // Method to insert toggle button into navbar
    insertToggleIntoNavbar() {
        const navbar = document.querySelector('.navbar-nav');
        if (navbar) {
            const toggleLi = document.createElement('li');
            toggleLi.className = 'nav-item d-flex align-items-center';
            
            const toggleButton = this.createToggleButton();
            toggleLi.appendChild(toggleButton);
            
            // Insert before language dropdown if it exists
            const languageDropdown = navbar.querySelector('.dropdown');
            if (languageDropdown) {
                navbar.insertBefore(toggleLi, languageDropdown);
            } else {
                navbar.appendChild(toggleLi);
            }
            
            this.updateToggleIcon();
        }
    }
}

// Initialize theme system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing theme system...');
    
    // Initialize theme system
    window.themeToggle = new ThemeToggle();
    
    // Add a simple click handler as backup
    setTimeout(() => {
        const toggleButton = document.getElementById('theme-toggle');
        console.log('Theme toggle button found:', toggleButton);
        
        if (toggleButton) {
            console.log('Button HTML:', toggleButton.outerHTML);
            
            // Force update icon to make sure it's displayed correctly
            window.themeToggle.updateToggleIcon();
            
            // Add direct click handler
            toggleButton.onclick = function(e) {
                console.log('Direct onclick handler triggered!');
                e.preventDefault();
                e.stopPropagation();
                window.themeToggle.toggleTheme();
                return false;
            };
            
            // Make sure button is focusable and clickable
            toggleButton.style.pointerEvents = 'auto';
            toggleButton.style.cursor = 'pointer';
            toggleButton.tabIndex = 0;
            
        } else {
            console.error('Theme toggle button not found after initialization');
        }
    }, 100);
});

// Also initialize when the window loads as a fallback
window.addEventListener('load', function() {
    if (!window.themeToggle) {
        console.log('Fallback initialization of theme system...');
        window.themeToggle = new ThemeToggle();
    }
    
    // Additional fallback for theme toggle button
    setTimeout(() => {
        const toggleButton = document.getElementById('theme-toggle');
        if (toggleButton && !toggleButton.onclick) {
            console.log('Setting up fallback click handler...');
            toggleButton.addEventListener('click', function(e) {
                console.log('Fallback click handler activated!');
                e.preventDefault();
                if (window.themeToggle) {
                    window.themeToggle.toggleTheme();
                }
            });
        }
    }, 1000);
});

// Export for use in other scripts if needed
window.ThemeToggle = ThemeToggle;

// Debug function to test theme toggle manually
window.testThemeToggle = function() {
    console.log('Testing theme toggle...');
    if (window.themeToggle) {
        window.themeToggle.toggleTheme();
        console.log('Theme toggled! Current theme:', window.themeToggle.theme);
    } else {
        console.error('ThemeToggle not initialized!');
    }
};