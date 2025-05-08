/**
 * Global Air Quality Monitoring Dashboard - Colorful Theme Module
 * Enhanced with dynamic animations and beautiful visual effects
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add colorful mode toggle button to body
    addColorfulModeToggle();
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('colorful-theme');
    
    // Apply colorful theme if previously selected
    if (savedTheme === 'enabled') {
        document.body.classList.add('colorful-mode');
        updateToggleButton(true);
    }
    
    // Initialize the rest of colorful theme features
    initColorfulTheme();
});

// Add colorful mode toggle button
function addColorfulModeToggle() {
    // Create the toggle button if it doesn't exist
    if (!document.getElementById('colorful-mode-toggle')) {
        const toggleButton = document.createElement('button');
        toggleButton.id = 'colorful-mode-toggle';
        toggleButton.className = 'theme-toggle-button';
        toggleButton.innerHTML = '<i class="fas fa-palette"></i>';
        toggleButton.setAttribute('aria-label', 'Toggle colorful mode');
        toggleButton.title = 'Toggle colorful mode';
        
        // Add event listener
        toggleButton.addEventListener('click', toggleColorfulMode);
        
        // Add to body
        document.body.appendChild(toggleButton);
    }
}

// Toggle colorful mode
function toggleColorfulMode() {
    const isColorful = document.body.classList.toggle('colorful-mode');
    
    // Update button appearance
    updateToggleButton(isColorful);
    
    // Save preference
    localStorage.setItem('colorful-theme', isColorful ? 'enabled' : 'disabled');
    
    // Trigger any necessary updates for charts and visualizations
    document.dispatchEvent(new Event('themeChanged'));
}

// Update toggle button appearance based on current state
function updateToggleButton(isColorful) {
    const toggleButton = document.getElementById('colorful-mode-toggle');
    if (toggleButton) {
        const icon = toggleButton.querySelector('i');
        if (icon) {
            if (isColorful) {
                icon.className = 'fas fa-adjust';
                toggleButton.title = 'Switch to standard mode';
            } else {
                icon.className = 'fas fa-palette';
                toggleButton.title = 'Switch to colorful mode';
            }
        }
    }
}

// Initialize colorful theme functionality
function initColorfulTheme() {
    console.log("Initializing enhanced colorful theme...");
    
    // Don't set colorful-theme by default since we're now using colorful-mode toggle
    
    // Add animated gradients to dashboard cards
    applyGradientBackgrounds();
    
    // Initialize AQI improvement counters if applicable
    const counterElements = document.querySelectorAll('[data-aqi-counter]');
    counterElements.forEach(element => {
        const startValue = parseInt(element.getAttribute('data-start-value') || 0);
        const endValue = parseInt(element.getAttribute('data-end-value') || 0);
        const message = element.getAttribute('data-message') || '';
        
        if (startValue && endValue) {
            initAQIImprovementCounter(element.id, startValue, endValue, message);
        }
    });
    
    // Apply colorful styling to charts
    updateChartsForTheme();
    
    // Add glowing effects
    addGlowingEffects();
    
    // Initialize page transitions
    initPageTransitions();
    
    // Initialize typing animation for headings
    initTypingAnimation();
    
    // Add number counter animations
    initNumberCounters();
    
    // Add background particles effect
    initBackgroundParticles();
    
    // Add card hover effects
    addCardHoverEffects();
}

// Apply animated gradient backgrounds to dashboard cards
function applyGradientBackgrounds() {
    const cards = document.querySelectorAll('.dashboard-card');
    
    cards.forEach((card, index) => {
        // Skip cards that already have a background or specific styling
        if (card.style.background || card.classList.contains('no-gradient')) {
            return;
        }
        
        // Generate a subtle gradient background
        const baseHue = (index * 40) % 360; // Spread colors across the spectrum
        
        // Create a dynamic gradient that shifts slightly
        const style = document.createElement('style');
        style.textContent = `
            @keyframes gradientShift${index} {
                0% {
                    background-position: 0% 50%;
                }
                50% {
                    background-position: 100% 50%;
                }
                100% {
                    background-position: 0% 50%;
                }
            }
        `;
        document.head.appendChild(style);
        
        // Apply the animated gradient
        card.style.background = `linear-gradient(135deg, 
                                hsla(${baseHue}, 70%, 97%, 1), 
                                hsla(${baseHue + 30}, 80%, 95%, 1), 
                                hsla(${baseHue + 60}, 70%, 97%, 1))`;
        card.style.backgroundSize = '200% 200%';
        card.style.animation = `gradientShift${index} 15s ease infinite`;
        
        // Add subtle box shadow
        card.style.boxShadow = `0 10px 30px rgba(0, 0, 0, 0.05), 
                               0 1px 8px rgba(0, 0, 0, 0.1), 
                               inset 0 1px 0 rgba(255, 255, 255, 0.6)`;
        
        // Add subtle border
        card.style.border = '1px solid rgba(230, 230, 250, 0.7)';
        
        // Add transition for hover effect
        card.style.transition = 'all 0.3s ease-in-out, transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
    });
}

// Add glowing effects to important UI elements
function addGlowingEffects() {
    // Add glowing effect to primary buttons
    const primaryButtons = document.querySelectorAll('.btn-colorful');
    primaryButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.boxShadow = '0 0 20px 5px rgba(0, 210, 255, 0.5)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.1)';
        });
    });
    
    // Add glowing badges
    const badges = document.querySelectorAll('.badge');
    badges.forEach(badge => {
        if (!badge.classList.contains('no-glow')) {
            badge.classList.add('badge-glow');
        }
    });
    
    // Add pulsing effect to AQI values
    const aqiValues = document.querySelectorAll('.aqi-value');
    aqiValues.forEach(value => {
        // Create pulsing animation
        const pulseAnimation = `
            @keyframes pulse-aqi {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
        `;
        
        // Add the animation style
        const style = document.createElement('style');
        style.textContent = pulseAnimation;
        document.head.appendChild(style);
        
        // Apply the animation
        value.style.animation = 'pulse-aqi 2s infinite ease-in-out';
        value.style.transformOrigin = 'center';
        value.style.display = 'inline-block';
    });
}

// Add hover effects to cards
function addCardHoverEffects() {
    const cards = document.querySelectorAll('.dashboard-card, .info-card, .feature-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function(e) {
            // Add 3D tilt effect based on mouse position
            this.addEventListener('mousemove', handleMouseMove);
            
            // Add shine effect
            if (!this.querySelector('.card-shine')) {
                const shine = document.createElement('div');
                shine.classList.add('card-shine');
                shine.style.position = 'absolute';
                shine.style.top = '0';
                shine.style.left = '0';
                shine.style.right = '0';
                shine.style.bottom = '0';
                shine.style.background = 'radial-gradient(circle at var(--mouse-x) var(--mouse-y), rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 50%)';
                shine.style.opacity = '0';
                shine.style.transition = 'opacity 0.3s';
                shine.style.pointerEvents = 'none';
                shine.style.zIndex = '1';
                
                // Make sure card has position relative
                if (getComputedStyle(this).position === 'static') {
                    this.style.position = 'relative';
                }
                
                this.appendChild(shine);
                
                // Fade in the shine
                setTimeout(() => {
                    shine.style.opacity = '1';
                }, 10);
            }
        });
        
        card.addEventListener('mouseleave', function() {
            // Remove tilt effect
            this.removeEventListener('mousemove', handleMouseMove);
            this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
            
            // Remove shine effect
            const shine = this.querySelector('.card-shine');
            if (shine) {
                shine.style.opacity = '0';
                setTimeout(() => {
                    shine.remove();
                }, 300);
            }
        });
    });
    
    function handleMouseMove(e) {
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Calculate percentage
        const percentX = x / rect.width;
        const percentY = y / rect.height;
        
        // Calculate rotation (max 5 degrees)
        const rotateY = (percentX - 0.5) * 5; // -2.5 to 2.5 degrees
        const rotateX = (0.5 - percentY) * 5; // -2.5 to 2.5 degrees
        
        // Apply transform
        this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        
        // Update shine position
        const shine = this.querySelector('.card-shine');
        if (shine) {
            this.style.setProperty('--mouse-x', `${x}px`);
            this.style.setProperty('--mouse-y', `${y}px`);
        }
    }
}

// Initialize typing animation for headings
function initTypingAnimation() {
    // Find hero headings
    const heroHeadings = document.querySelectorAll('.hero h1:not(.no-typing)');
    
    heroHeadings.forEach(heading => {
        const text = heading.textContent;
        heading.textContent = '';
        heading.style.borderRight = '0.15em solid #3a7bd5';
        heading.style.animation = 'blink-caret 0.75s step-end infinite';
        
        // Add the typing animation style
        const style = document.createElement('style');
        style.textContent = `
            @keyframes blink-caret {
                from, to { border-color: transparent }
                50% { border-color: #3a7bd5 }
            }
        `;
        document.head.appendChild(style);
        
        // Type out the text
        let i = 0;
        function typeWriter() {
            if (i < text.length) {
                heading.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 50);
            } else {
                // Remove the cursor when done
                heading.style.borderRight = 'none';
                heading.style.animation = 'none';
            }
        }
        
        // Start typing animation after a short delay
        setTimeout(typeWriter, 500);
    });
}

// Initialize number counter animations
function initNumberCounters() {
    const counters = document.querySelectorAll('.info-card-value, .stats-card .number');
    
    // Create IntersectionObserver to start animation when element is visible
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                
                // Skip if already animated
                if (element.dataset.animated === 'true') return;
                
                // Mark as animated
                element.dataset.animated = 'true';
                
                // Get the target number
                let targetNumber;
                if (element.textContent.includes(' ')) {
                    // If there's a space (like "125 AQI"), only animate the number
                    const parts = element.textContent.split(' ');
                    targetNumber = parseFloat(parts[0]);
                    const suffix = parts.slice(1).join(' ');
                    
                    // Start from zero
                    element.innerHTML = `0 <span>${suffix}</span>`;
                    
                    // Animate to target
                    animateCounter(element, 0, targetNumber, suffix);
                } else {
                    targetNumber = parseFloat(element.textContent);
                    
                    // Start from zero
                    element.textContent = '0';
                    
                    // Animate to target
                    animateCounter(element, 0, targetNumber);
                }
            }
        });
    }, { threshold: 0.2 });
    
    // Observe each counter
    counters.forEach(counter => {
        observer.observe(counter);
    });
    
    // Counter animation function
    function animateCounter(element, start, end, suffix = '') {
        const duration = 1500; // 1.5 seconds
        const startTime = performance.now();
        const isFloat = String(end).includes('.');
        const decimalPlaces = isFloat ? String(end).split('.')[1].length : 0;
        
        function easeOutQuart(t) {
            return 1 - Math.pow(1 - t, 4);
        }
        
        function animateFrame(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = easeOutQuart(progress);
            
            const currentValue = start + (end - start) * easedProgress;
            
            if (suffix) {
                element.innerHTML = `${isFloat ? currentValue.toFixed(decimalPlaces) : Math.floor(currentValue)} <span>${suffix}</span>`;
            } else {
                element.textContent = isFloat ? currentValue.toFixed(decimalPlaces) : Math.floor(currentValue);
            }
            
            if (progress < 1) {
                requestAnimationFrame(animateFrame);
            }
        }
        
        requestAnimationFrame(animateFrame);
    }
}

// Update charts for colorful theme
function updateChartsForTheme() {
    // This function will be called after charts are initialized
    // It will adjust chart colors for the colorful theme
    if (typeof Chart !== 'undefined') {
        // Set colorful chart defaults
        Chart.defaults.color = '#555';
        Chart.defaults.borderColor = 'rgba(230, 230, 250, 0.8)';
        Chart.defaults.font.family = "'Poppins', 'Segoe UI', sans-serif";
        
        // Define beautiful gradient colors for charts
        const defaultColors = [
            { start: '#3a7bd5', end: '#00d2ff' }, // Blue gradient
            { start: '#FF9E7D', end: '#FF5D9E' }, // Pink/orange gradient
            { start: '#82c0cc', end: '#489fb5' }, // Teal gradient
            { start: '#8338ec', end: '#3a86ff' }, // Purple/blue gradient
            { start: '#43a047', end: '#66bb6a' }, // Green gradient
            { start: '#ef5350', end: '#e53935' }, // Red gradient
            { start: '#ffc107', end: '#ff9800' }, // Yellow/orange gradient
            { start: '#9c27b0', end: '#ba68c8' }  // Purple gradient
        ];
        
        // Save default colors for other libraries to use
        window.colorfulThemeColors = defaultColors;
        
        // Update existing charts if needed
        if (window.updateChartColors && typeof window.updateChartColors === 'function') {
            window.updateChartColors();
        }
    }
}

// Initialize background particles effect for hero sections
function initBackgroundParticles() {
    const heroSections = document.querySelectorAll('.hero');
    
    heroSections.forEach((hero, index) => {
        // Skip if already has particles or has .no-particles class
        if (hero.querySelector('.particles-container') || hero.classList.contains('no-particles')) {
            return;
        }
        
        // Create particles container
        const particlesContainer = document.createElement('div');
        particlesContainer.className = 'particles-container';
        particlesContainer.style.position = 'absolute';
        particlesContainer.style.top = '0';
        particlesContainer.style.left = '0';
        particlesContainer.style.width = '100%';
        particlesContainer.style.height = '100%';
        particlesContainer.style.overflow = 'hidden';
        particlesContainer.style.zIndex = '1';
        
        // Add particles
        const particleCount = 50;
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            
            // Random particle properties
            const size = Math.random() * 5 + 1;
            const posX = Math.random() * 100;
            const posY = Math.random() * 100;
            const opacity = Math.random() * 0.5 + 0.1;
            const animDuration = Math.random() * 20 + 10;
            const animDelay = Math.random() * 10;
            
            // Style the particle
            particle.style.position = 'absolute';
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.borderRadius = '50%';
            particle.style.background = 'rgba(255, 255, 255, ' + opacity + ')';
            particle.style.left = `${posX}%`;
            particle.style.top = `${posY}%`;
            particle.style.animation = `float-particle${index} ${animDuration}s ease-in-out ${animDelay}s infinite`;
            
            particlesContainer.appendChild(particle);
        }
        
        // Create the animation keyframes
        const style = document.createElement('style');
        style.textContent = `
            @keyframes float-particle${index} {
                0% { transform: translate(0, 0); }
                25% { transform: translate(${Math.random() * 30 - 15}px, ${Math.random() * 30 - 5}px); }
                50% { transform: translate(${Math.random() * 30 - 15}px, ${Math.random() * 30 - 10}px); }
                75% { transform: translate(${Math.random() * 30 - 15}px, ${Math.random() * 30 - 5}px); }
                100% { transform: translate(0, 0); }
            }
        `;
        document.head.appendChild(style);
        
        // Add the particles container to the hero
        hero.insertBefore(particlesContainer, hero.firstChild);
        
        // Ensure hero has position relative
        if (getComputedStyle(hero).position === 'static') {
            hero.style.position = 'relative';
        }
    });
}

// Display an AQI alert notification with beautiful animations
function showAQIAlert(title, message, level = 'moderate') {
    // Create alert container if it doesn't exist
    let alertContainer = document.getElementById('aqi-alert-container');
    
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'aqi-alert-container';
        alertContainer.style.position = 'fixed';
        alertContainer.style.top = '20px';
        alertContainer.style.right = '20px';
        alertContainer.style.zIndex = '9999';
        alertContainer.style.maxWidth = '350px';
        document.body.appendChild(alertContainer);
    }
    
    // Create the alert element
    const alert = document.createElement('div');
    alert.className = 'aqi-alert';
    
    // Set background color based on alert level
    let bgColor, borderColor, icon;
    
    switch (level) {
        case 'high':
            bgColor = 'linear-gradient(135deg, #ff5252, #ff1744)';
            borderColor = '#d50000';
            icon = '<i class="fas fa-exclamation-triangle"></i>';
            break;
        case 'low':
            bgColor = 'linear-gradient(135deg, #66bb6a, #43a047)';
            borderColor = '#2e7d32';
            icon = '<i class="fas fa-check-circle"></i>';
            break;
        case 'moderate':
        default:
            bgColor = 'linear-gradient(135deg, #29b6f6, #0288d1)';
            borderColor = '#0277bd';
            icon = '<i class="fas fa-info-circle"></i>';
            break;
    }
    
    // Style the alert
    alert.style.background = bgColor;
    alert.style.color = 'white';
    alert.style.borderRadius = '12px';
    alert.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.2), 0 0 20px 5px rgba(0, 210, 255, 0.15)';
    alert.style.marginBottom = '15px';
    alert.style.padding = '20px';
    alert.style.position = 'relative';
    alert.style.border = `1px solid ${borderColor}`;
    alert.style.transform = 'translateX(120%)';
    alert.style.opacity = '0';
    alert.style.transition = 'all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
    
    // Add content
    alert.innerHTML = `
        <div style="display: flex; align-items: flex-start;">
            <div style="margin-right: 15px; font-size: 28px; animation: pulse-icon 2s infinite;" class="alert-icon">
                ${icon}
            </div>
            <div style="flex: 1;">
                <h4 style="margin: 0 0 8px 0; font-weight: 600; font-size: 18px;">${title}</h4>
                <p style="margin: 0; font-size: 14px; line-height: 1.5;">${message}</p>
            </div>
        </div>
        <button class="close-alert" style="position: absolute; top: 10px; right: 10px; background: none; border: none; color: white; cursor: pointer; font-size: 16px; transition: all 0.2s; opacity: 0.7;">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add the alert to the container
    alertContainer.appendChild(alert);
    
    // Create icon pulse animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse-icon {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
    `;
    document.head.appendChild(style);
    
    // Animate the alert in
    setTimeout(() => {
        alert.style.transform = 'translateX(0)';
        alert.style.opacity = '1';
    }, 50);
    
    // Add close functionality
    const closeButton = alert.querySelector('.close-alert');
    closeButton.addEventListener('mouseenter', () => {
        closeButton.style.opacity = '1';
        closeButton.style.transform = 'scale(1.1)';
    });
    
    closeButton.addEventListener('mouseleave', () => {
        closeButton.style.opacity = '0.7';
        closeButton.style.transform = 'scale(1)';
    });
    
    closeButton.addEventListener('click', () => {
        closeAlert(alert);
    });
    
    // Auto-close after 7 seconds for low and moderate alerts
    if (level !== 'high') {
        setTimeout(() => {
            closeAlert(alert);
        }, 7000);
    }
    
    // Function to close/remove the alert with animation
    function closeAlert(alertElement) {
        alertElement.style.transform = 'translateX(120%)';
        alertElement.style.opacity = '0';
        
        setTimeout(() => {
            alertElement.remove();
        }, 500);
    }
}

// Initialize AQI improvement counter animation with enhanced visuals
function initAQIImprovementCounter(elementId, startValue, endValue, message) {
    const element = document.getElementById(elementId);
    
    if (!element) {
        console.error(`Element with id ${elementId} not found`);
        return;
    }
    
    // Check if it's an improvement or deterioration
    const isImprovement = startValue > endValue;
    const difference = Math.abs(startValue - endValue);
    const percentChange = ((Math.abs(startValue - endValue) / startValue) * 100).toFixed(1);
    
    // Create the counter element with enhanced design
    element.innerHTML = `
        <div class="aqi-counter-card">
            <div class="aqi-counter-header">
                <div class="aqi-counter-icon">
                    <i class="fas ${isImprovement ? 'fa-arrow-down' : 'fa-arrow-up'}"></i>
                </div>
                <h4>${isImprovement ? 'Air Quality Improvement' : 'Air Quality Change'}</h4>
            </div>
            <div class="aqi-counter-content">
                <div class="aqi-counter-values">
                    <div class="aqi-counter-from">
                        <span class="label">Previous</span>
                        <span class="value">${startValue}</span>
                    </div>
                    <div class="aqi-counter-arrow">
                        <i class="fas fa-long-arrow-alt-right"></i>
                    </div>
                    <div class="aqi-counter-to">
                        <span class="label">Current</span>
                        <span class="value" id="aqi-counter-current">${endValue}</span>
                    </div>
                </div>
                <div class="aqi-counter-progress">
                    <div class="aqi-progress-bar">
                        <div class="aqi-progress-fill" id="aqi-progress-fill"></div>
                    </div>
                </div>
                <div class="aqi-counter-change">
                    <span class="badge ${isImprovement ? 'aqi-good-bg' : 'aqi-unhealthy-bg'}">
                        ${isImprovement ? '↓' : '↑'} ${difference} (${percentChange}%)
                    </span>
                </div>
                <div class="aqi-counter-message">
                    ${message}
                </div>
            </div>
        </div>
    `;
    
    // Style the counter
    addCounterStyles();
    
    // Animate the counter regardless of improvement (looks better)
    animateCounter(startValue, endValue);
    
    // Add styles for the counter with improved visuals
    function addCounterStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .aqi-counter-card {
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(230, 230, 250, 0.7);
                overflow: hidden;
                position: relative;
                transition: all 0.3s ease;
            }
            
            .aqi-counter-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15), 0 0 20px 5px rgba(0, 210, 255, 0.1);
            }
            
            .aqi-counter-card::after {
                content: "";
                position: absolute;
                top: 0;
                right: 0;
                width: 150px;
                height: 150px;
                background: linear-gradient(135deg, 
                    ${isImprovement ? 'rgba(76, 175, 80, 0.05)' : 'rgba(244, 67, 54, 0.05)'}, 
                    ${isImprovement ? 'rgba(76, 175, 80, 0.02)' : 'rgba(244, 67, 54, 0.02)'});
                border-radius: 0 0 0 100%;
                z-index: 1;
            }
            
            .aqi-counter-header {
                display: flex;
                align-items: center;
                margin-bottom: 25px;
                position: relative;
                z-index: 2;
            }
            
            .aqi-counter-icon {
                width: 50px;
                height: 50px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 15px;
                font-size: 20px;
                background: ${isImprovement ? 
                    'linear-gradient(135deg, #66bb6a, #43a047)' : 
                    'linear-gradient(135deg, #ef5350, #e53935)'};
                color: white;
                box-shadow: 0 8px 25px ${isImprovement ? 
                    'rgba(76, 175, 80, 0.4)' : 
                    'rgba(244, 67, 54, 0.4)'};
            }
            
            .aqi-counter-header h4 {
                margin: 0;
                font-size: 20px;
                font-weight: 600;
                color: #333;
            }
            
            .aqi-counter-content {
                text-align: center;
                position: relative;
                z-index: 2;
            }
            
            .aqi-counter-values {
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .aqi-counter-from, .aqi-counter-to {
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 15px;
                border-radius: 10px;
                min-width: 120px;
            }
            
            .aqi-counter-from {
                background-color: ${isImprovement ? 'rgba(244, 67, 54, 0.1)' : 'rgba(76, 175, 80, 0.1)'};
                color: ${isImprovement ? '#e53935' : '#43a047'};
            }
            
            .aqi-counter-to {
                background-color: ${isImprovement ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)'};
                color: ${isImprovement ? '#43a047' : '#e53935'};
            }
            
            .aqi-counter-arrow {
                margin: 0 20px;
                color: #666;
                font-size: 24px;
            }
            
            .aqi-counter-from .label, .aqi-counter-to .label {
                font-size: 14px;
                margin-bottom: 8px;
                font-weight: 500;
            }
            
            .aqi-counter-from .value, .aqi-counter-to .value {
                font-size: 32px;
                font-weight: 700;
            }
            
            .aqi-counter-progress {
                margin: 20px 0;
            }
            
            .aqi-progress-bar {
                height: 10px;
                background-color: #eee;
                border-radius: 5px;
                overflow: hidden;
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .aqi-progress-fill {
                height: 100%;
                width: 0%;
                border-radius: 5px;
                background: ${isImprovement ? 
                    'linear-gradient(to right, #66bb6a, #43a047)' : 
                    'linear-gradient(to right, #ef5350, #e53935)'};
                transition: width 2s cubic-bezier(0.19, 1, 0.22, 1);
            }
            
            .aqi-counter-change {
                margin: 15px 0;
            }
            
            .aqi-counter-message {
                font-size: 16px;
                color: #555;
                margin-top: 15px;
                line-height: 1.5;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Animate the counter value and progress bar
    function animateCounter(start, end) {
        const counterElement = document.getElementById('aqi-counter-current');
        const progressFill = document.getElementById('aqi-progress-fill');
        const duration = 2000; // 2 seconds
        const startTime = performance.now();
        const change = end - start;
        
        // Calculate progress percentage for the fill bar
        const progressPercent = isImprovement ? 
            ((start - end) / start) * 100 : 
            ((end - start) / end) * 100;
        
        function easeOutQuart(t) {
            return 1 - Math.pow(1 - t, 4);
        }
        
        function animateFrame(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = easeOutQuart(progress);
            
            const currentValue = Math.round(start + change * easedProgress);
            counterElement.textContent = currentValue;
            
            // Update progress bar width
            progressFill.style.width = `${progressPercent * easedProgress}%`;
            
            if (progress < 1) {
                requestAnimationFrame(animateFrame);
            }
        }
        
        requestAnimationFrame(animateFrame);
    }
}

// Initialize page transitions with beautiful animations
function initPageTransitions() {
    // Add page transition styles
    const style = document.createElement('style');
    style.textContent = `
        .page-transition-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(58, 123, 213, 0.97), rgba(0, 210, 255, 0.97));
            backdrop-filter: blur(10px);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.5s ease;
        }
        
        .page-transition-overlay.active {
            opacity: 1;
            pointer-events: all;
        }
        
        .page-transition-content {
            text-align: center;
            transform: translateY(20px);
            opacity: 0;
            transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1);
        }
        
        .page-transition-overlay.active .page-transition-content {
            transform: translateY(0);
            opacity: 1;
        }
        
        .page-transition-spinner {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            animation: spinner 1s infinite ease-in-out;
            margin: 0 auto 20px;
        }
        
        .page-transition-text {
            color: white;
            font-size: 18px;
            font-weight: 500;
        }
        
        @keyframes spinner {
            to {
                transform: rotate(360deg);
            }
        }
    `;
    document.head.appendChild(style);
    
    // Create overlay element
    const overlay = document.createElement('div');
    overlay.className = 'page-transition-overlay';
    overlay.innerHTML = `
        <div class="page-transition-content">
            <div class="page-transition-spinner"></div>
            <div class="page-transition-text">Loading...</div>
        </div>
    `;
    document.body.appendChild(overlay);
    
    // Add event listeners to links
    document.querySelectorAll('a').forEach(link => {
        // Skip links that should not trigger page transition
        if (link.hasAttribute('data-no-transition') || 
            link.getAttribute('target') === '_blank' || 
            link.getAttribute('href')?.startsWith('#') ||
            link.getAttribute('href')?.startsWith('javascript:')) {
            return;
        }
        
        link.addEventListener('click', function(e) {
            // Skip if modifier keys are pressed
            if (e.ctrlKey || e.metaKey || e.shiftKey) {
                return;
            }
            
            const href = this.getAttribute('href');
            if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
                e.preventDefault();
                
                // Show transition overlay
                overlay.classList.add('active');
                
                // Set custom loading text based on link destination
                let pageName = "new page";
                if (href.includes('map')) pageName = "map view";
                else if (href.includes('historical')) pageName = "historical data";
                else if (href.includes('polluted')) pageName = "pollution rankings";
                else if (href.includes('comparison')) pageName = "city comparison";
                overlay.querySelector('.page-transition-text').textContent = `Loading ${pageName}...`;
                
                // Navigate after a short delay
                setTimeout(() => {
                    window.location.href = href;
                }, 800);
            }
        });
    });
}

// Call the initialization function when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initColorfulTheme();
    
    // Add welcome animation if on home page
    if (document.body.dataset.page === 'index') {
        setTimeout(() => {
            showAQIAlert('Welcome to Air Quality Monitor', 'Explore real-time air quality data from around the world with our interactive tools and visualizations.', 'low');
        }, 1500);
    }
});