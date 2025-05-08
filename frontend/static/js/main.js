/**
 * Global Air Quality Monitoring Dashboard - Main JS Module
 * This module handles general page initialization and functionality
 */

// Global variables
let autoRefreshInterval = null;
let currentTheme = 'colorful';

document.addEventListener('DOMContentLoaded', function() {
    console.log('Air Quality Dashboard initialized');

    // Initialize bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize page-specific functionality
    const currentPage = document.body.dataset.page;

    if (currentPage === 'index') {
        initHomePage();
        
        // Add event listener for refresh map button on the home page
        const refreshMapBtn = document.getElementById('refresh-map');
        if (refreshMapBtn) {
            refreshMapBtn.addEventListener('click', function() {
                console.log('Refreshing map data...');
                const mapContainer = document.getElementById('map-container');
                if (mapContainer) {
                    // Show loading indicator
                    mapContainer.innerHTML = '<div class="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center bg-light"><div class="text-center"><div class="spinner-border text-primary mb-3" role="status"><span class="visually-hidden">Loading...</span></div><p>Refreshing map data...</p></div></div>';
                    
                    // Fetch fresh data
                    fetch('/api/interactive_map_data')
                        .then(response => response.json())
                        .then(data => {
                            console.log('Map data refreshed successfully:', data.length + ' markers');
                            // Initialize map with refreshed data
                            initMap(data);
                        })
                        .catch(error => {
                            console.error('Error refreshing marker data:', error);
                            mapContainer.innerHTML = '<div class="alert alert-danger">Error refreshing map data. Please try again.</div>';
                        });
                }
            });
        }
    } else if (currentPage === 'map') {
        initMapPage();
    } else if (currentPage === 'historical') {
        initHistoricalPage();
    } else if (currentPage === 'most-polluted') {
        initMostPollutedPage();
    }

    // Initialize colorful theme
    initColorfulTheme();

    // Handle mobile navigation menu
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');

    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });

        // Close mobile menu when clicking a link
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                navbarCollapse.classList.remove('show');
            });
        });
    }

    // Initialize Chart.js defaults and theme handling
    // Update chart colors based on current theme
    function updateChartColors() {
        const isColorfulMode = document.body.classList.contains('colorful-mode');
        Chart.defaults.color = isColorfulMode ? '#333' : '#666';
        Chart.defaults.borderColor = isColorfulMode ? 'rgba(0,0,0,0.1)' : 'rgba(0,0,0,0.1)';
    }

    // Initial color update
    updateChartColors();

    // Listen for theme changes
    document.addEventListener('themeChanged', updateChartColors);

    // Add event listener to dispatch themeChanged event
    const colorfulThemeToggle = document.getElementById('colorful-theme-toggle');
    if (colorfulThemeToggle) {
        colorfulThemeToggle.addEventListener('click', function() {
            // Toggle colorful mode class on body
            document.body.classList.toggle('colorful-mode');

            // Update theme text
            const isColorfulMode = document.body.classList.contains('colorful-mode');
            const themeText = document.getElementById('theme-text');
            if (themeText) {
                themeText.textContent = isColorfulMode ? 'Standard Theme' : 'Colorful Theme';
            }

            // Update icon
            const paletteIcon = this.querySelector('i');
            if (paletteIcon) {
                if (isColorfulMode) {
                    paletteIcon.classList.remove('fa-palette');
                    paletteIcon.classList.add('fa-adjust');
                } else {
                    paletteIcon.classList.remove('fa-adjust');
                    paletteIcon.classList.add('fa-palette');
                }
            }

            // Save preference to localStorage
            localStorage.setItem('theme', isColorfulMode ? 'colorful' : 'standard');

            // Dispatch theme changed event
            document.dispatchEvent(new Event('themeChanged'));
        });
    }

    const darkModeToggleFloat = document.getElementById('dark-mode-toggle-float');
    if (darkModeToggleFloat) {
        darkModeToggleFloat.addEventListener('click', function() {
            // Toggle colorful mode class on body
            document.body.classList.toggle('colorful-mode');

            // Update UI
            const isColorfulMode = document.body.classList.contains('colorful-mode');

            // Update floating button icon
            const floatIcon = this.querySelector('i');
            if (floatIcon) {
                floatIcon.className = isColorfulMode ? 'fas fa-adjust' : 'fas fa-palette';
            }

            // Save preference to localStorage
            localStorage.setItem('theme', isColorfulMode ? 'colorful' : 'standard');

            // Dispatch theme changed event
            document.dispatchEvent(new Event('themeChanged'));
        });
    }


});

// Initialize colorful theme
function initColorfulTheme() {
    // Add glowing effects to important UI elements
    const primaryButtons = document.querySelectorAll('.btn-colorful');
    primaryButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.boxShadow = '0 0 20px 5px rgba(0, 210, 255, 0.5)';
        });

        button.addEventListener('mouseleave', function() {
            this.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.1)';
        });
    });
}

function initHomePage() {
    console.log('Initializing home page');
    // Load featured countries chart if element exists
    const featuredCountriesChart = document.getElementById('featured-countries-chart');
    if (featuredCountriesChart) {
        // Get top 10 most polluted countries
        const countriesTable = document.getElementById('top-countries-table');
        if (countriesTable) {
            const rows = countriesTable.querySelectorAll('tbody tr');
            const countries = [];
            const aqiValues = [];

            rows.forEach(row => {
                const cols = row.querySelectorAll('td');
                if (cols.length >= 3) {
                    countries.push(cols[1].textContent);
                    aqiValues.push(parseFloat(cols[2].textContent));
                }
            });

            createPollutionBarChart(
                'featured-countries-chart',
                'Most Polluted Countries (2024)',
                countries,
                aqiValues
            );
        }
    }

    // Initialize map if the container exists
    const mapContainer = document.getElementById('map-container');
    if (mapContainer) {
        // Fetch marker data - use the correct path with url_for-like structure
        fetch('/api/interactive_map_data') // Use API endpoint instead of direct file access
            .then(response => response.json())
            .then(data => {
                console.log('Map data loaded successfully:', data.length + ' markers');
                // Initialize map with data
                initMap(data);
            })
            .catch(error => {
                console.error('Error loading marker data:', error);
                mapContainer.innerHTML = '<div class="alert alert-danger">Error loading map data. Please try again.</div>';
            });
    }
}

function initMapPage() {
    console.log('Initializing interactive air quality map page');
    // Show loading indicator
    const mapLoadingElement = document.getElementById('map-loading');
    if (mapLoadingElement) {
        mapLoadingElement.style.display = 'block';
    }

    // Check if we should start with real-time India data
    const realtimeToggle = document.getElementById('realtime-toggle');
    const useRealtimeData = realtimeToggle ? realtimeToggle.checked : true;

    if (useRealtimeData) {
        // Try to get real-time India data first
        fetch('/api/india-aqi-data')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Initialize map with real-time data
                initMap(data);

                // Initialize map filters
                initMapFilters();

                // Update timestamp
                updateLastUpdated(new Date().toISOString());

                // Hide loading indicator
                if (mapLoadingElement) {
                    mapLoadingElement.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error loading real-time data, falling back to static data:', error);

                // Fallback to static marker data
                fetchStaticMarkerData();
            });
    } else {
        // Use static data
        fetchStaticMarkerData();
    }

    // Function to fetch static marker data (used as fallback)
    function fetchStaticMarkerData() {
        fetch('/frontend/static/data/marker_data.json')
            .then(response => {
                if (!response.ok) {
                    // Try alternative path if first one fails
                    return fetch('/static/data/marker_data.json');
                }
                return response;
            })
            .then(response => response.json())
            .then(data => {
                // Initialize map with static data
                initMap(data);

                // Initialize map filters
                initMapFilters();

                // Hide loading indicator
                if (mapLoadingElement) {
                    mapLoadingElement.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error loading marker data:', error);
                const mapContainer = document.getElementById('map-container');
                if (mapContainer) {
                    mapContainer.innerHTML = '<div class="alert alert-danger mt-3">Error loading map data. Please try again.</div>';
                }

                // Hide loading indicator
                if (mapLoadingElement) {
                    mapLoadingElement.style.display = 'none';
                }
            });
    }

    // Add timestamp to the page showing when data was last updated
    const now = new Date();
    const timestampElement = document.getElementById('last-updated-time');
    if (timestampElement) {
        timestampElement.textContent = now.toLocaleString();
    }
}

function initHistoricalPage() {
    console.log('Initializing historical page');
    const countrySelect = document.getElementById('country-select');
    const citySelect = document.getElementById('city-select');

    if (countrySelect) {
        // Load initial country data
        if (countrySelect.value) {
            loadCountryData(countrySelect.value);
        }

        // Add event listener for country selection
        countrySelect.addEventListener('change', function() {
            loadCountryData(this.value);
        });
    }

    if (citySelect) {
        // Add event listener for city selection
        citySelect.addEventListener('change', function() {
            const cityStateValue = this.value;
            if (cityStateValue) {
                const [city, state] = cityStateValue.split('|');
                loadCityData(city, state);
            }
        });
    }

    // Handle comparison feature
    const compareButton = document.getElementById('compare-button');
    if (compareButton) {
        compareButton.addEventListener('click', function() {
            const country1 = document.getElementById('country-select').value;
            const cityStateValue = document.getElementById('city-select').value;

            if (country1 && cityStateValue) {
                const [city, state] = cityStateValue.split('|');

                Promise.all([
                    fetch(`/api/country-data/${country1}`).then(response => response.json()),
                    fetch(`/api/city-data/${city}/${state}`).then(response => response.json())
                ])
                    .then(([countryData, cityData]) => {
                        // Create comparison chart
                        createComparisonChart(
                            'comparison-chart',
                            `${countryData.country} vs ${cityData.city}, ${cityData.state} (2024)`,
                            countryData.months,
                            countryData.monthly_data,
                            countryData.country,
                            cityData.monthly_data,
                            `${cityData.city}, ${cityData.state}`
                        );

                        // Show comparison section
                        document.getElementById('comparison-section').style.display = 'block';
                    })
                    .catch(error => {
                        console.error('Error loading comparison data:', error);
                        alert('Error loading comparison data. Please try again.');
                    });
            } else {
                alert('Please select both a country and a city to compare.');
            }
        });
    }
}

function initMostPollutedPage() {
    console.log('Initializing most polluted page');
    // Load countries chart if element exists
    const countriesChart = document.getElementById('polluted-countries-chart');
    if (countriesChart) {
        // Get top polluted countries
        const countriesTable = document.getElementById('polluted-countries-table');
        if (countriesTable) {
            const rows = countriesTable.querySelectorAll('tbody tr');
            const countries = [];
            const aqiValues = [];

            // Limit to top 20 for better visibility
            const maxRows = Math.min(rows.length, 20);

            for (let i = 0; i < maxRows; i++) {
                const cols = rows[i].querySelectorAll('td');
                if (cols.length >= 3) {
                    countries.push(cols[1].textContent);
                    aqiValues.push(parseFloat(cols[2].textContent));
                }
            }

            createPollutionBarChart(
                'polluted-countries-chart',
                'Top 20 Most Polluted Countries (2024)',
                countries,
                aqiValues
            );
        }
    }

    // Load cities data if select exists
    const citySelect = document.getElementById('city-state-select');
    if (citySelect) {
        citySelect.addEventListener('change', function() {
            const value = this.value;
            if (value) {
                const [city, state] = value.split('|');
                loadCityData(city, state);

                // Show city data section
                document.getElementById('city-data-section').style.display = 'block';
            }
        });
    }

    // Calculate AQI category distribution if element exists
    const categoryDistChart = document.getElementById('category-distribution-chart');
    if (categoryDistChart) {
        // Get AQI values from the table
        const countriesTable = document.getElementById('polluted-countries-table');
        if (countriesTable) {
            const rows = countriesTable.querySelectorAll('tbody tr');
            const categories = {
                'Good': 0,
                'Moderate': 0,
                'Unhealthy for Sensitive Groups': 0,
                'Unhealthy': 0,
                'Very Unhealthy': 0,
                'Hazardous': 0
            };

            rows.forEach(row => {
                const cols = row.querySelectorAll('td');
                if (cols.length >= 3) {
                    const aqi = parseFloat(cols[2].textContent);
                    if (aqi <= 50) {
                        categories['Good']++;
                    } else if (aqi <= 100) {
                        categories['Moderate']++;
                    } else if (aqi <= 150) {
                        categories['Unhealthy for Sensitive Groups']++;
                    } else if (aqi <= 200) {
                        categories['Unhealthy']++;
                    } else if (aqi <= 300) {
                        categories['Very Unhealthy']++;
                    } else {
                        categories['Hazardous']++;
                    }
                }
            });

            createAQICategoryPieChart(
                'category-distribution-chart',
                'AQI Category Distribution',
                Object.values(categories)
            );
        }
    }
}

function getAQIGradient(aqi) {
    let color;

    if (aqi <= 50) {
        color = '#009966'; // Good
    } else if (aqi <= 100) {
        color = '#ffde33'; // Moderate
    } else if (aqi <= 150) {
        color = '#ff9933'; // Unhealthy for Sensitive Groups
    } else if (aqi <= 200) {
        color = '#cc0033'; // Unhealthy
    } else if (aqi <= 300) {
        color = '#660099'; // Very Unhealthy
    } else {
        color = '#7e0023'; // Hazardous
    }

    return `linear-gradient(135deg, ${color}33 0%, ${color}aa 100%)`;
}

function formatDate(date) {
    return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function updateLastUpdated(timestamp) {
    const lastUpdatedEl = document.getElementById('last-updated');
    if (lastUpdatedEl && timestamp) {
        const date = new Date(timestamp);
        lastUpdatedEl.textContent = formatDate(date);
    }
}

function initDarkMode() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const darkModeToggleFloat = document.getElementById('dark-mode-toggle-float');
    const themeText = document.getElementById('theme-text');
    const moonIcon = darkModeToggle ? darkModeToggle.querySelector('i') : null;
    const floatIcon = darkModeToggleFloat ? darkModeToggleFloat.querySelector('i') : null;

    // Check for saved theme preference or respect OS preference
    const prefersDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');

    // Apply theme based on saved preference or OS preference
    if (savedTheme === 'dark' || (!savedTheme && prefersDarkMode)) {
        document.body.classList.add('dark-mode');
        if (themeText) themeText.textContent = 'Light Mode';
        if (moonIcon) {
            moonIcon.classList.remove('fa-moon');
            moonIcon.classList.add('fa-sun');
        }
    }

    // Toggle between light and dark mode
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function(e) {
            e.preventDefault();

            // Toggle dark mode class on body
            document.body.classList.toggle('dark-mode');

            // Update button text and icon
            const isDarkMode = document.body.classList.contains('dark-mode');
            if (themeText) themeText.textContent = isDarkMode ? 'Light Mode' : 'Dark Mode';

            if (moonIcon) {
                if (isDarkMode) {
                    moonIcon.classList.remove('fa-moon');
                    moonIcon.classList.add('fa-sun');
                } else {
                    moonIcon.classList.remove('fa-sun');
                    moonIcon.classList.add('fa-moon');
                }
            }

            // Save preference to localStorage
            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');

            // Update floating button icon
            if (floatIcon) {
                floatIcon.className = isDarkMode ? 'fas fa-sun' : 'fas fa-moon';
            }

            // Update charts if they exist
            updateChartsForTheme();
        });
    }

    // Handle floating dark mode toggle
    if (darkModeToggleFloat) {
        darkModeToggleFloat.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            const isDarkMode = document.body.classList.contains('dark-mode');

            // Update navbar text and icon
            if (themeText) themeText.textContent = isDarkMode ? 'Light Mode' : 'Dark Mode';
            if (moonIcon) {
                moonIcon.className = isDarkMode ? 'fas fa-sun' : 'fas fa-moon';
            }
            if (floatIcon) {
                floatIcon.className = isDarkMode ? 'fas fa-sun' : 'fas fa-moon';
            }

            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
            updateChartsForTheme();
        });
    }
}

function updateChartsForTheme() {
    // Update any existing charts with the new theme colors
    // This would need to be implemented if you have charts that should change with theme
    // For now, this is a placeholder
    if (window.Chart && Chart.instances) {
        Chart.instances.forEach(chart => {
            chart.update();
        });
    }
}