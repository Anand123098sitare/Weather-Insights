// Global constants
const API_BASE_URL = '';  // Empty string for same-origin requests
const API_ENDPOINTS = {
    dashboard: '/api/dashboard/data',
    mapData: '/api/map/data',
    mostPolluted: '/api/most-polluted/data',
    citiesComparison: '/api/cities-for-comparison',
    cityComparison: '/api/city-comparison-data',
    aqiCsvData: '/api/aqi-csv-data',
    heatmapData: '/api/heatmap-data',
    indiaAqi: '/api/india-aqi-data',
    cityAqi: '/api/city-aqi/',
    globalAqi: '/api/global-air-quality-map-data',
    interactiveMapData: '/api/interactive-map-data',
    countryData: '/api/country-data/',
    cityData: '/api/city-data/',
    iqairCountries: '/api/iqair/countries',
    iqairStates: '/api/iqair/states/',
    iqairCities: '/api/iqair/cities/',
    iqairCityData: '/api/iqair/city/',
    iqairNearestCity: '/api/iqair/nearest-city',
    citiesForCountry: '/api/cities/',
    forecast: '/api/forecast',
    weatherCorrelation: '/api/weather-correlation',
    seasonalForecast: '/api/seasonal-forecast',
    healthRecommendations: '/api/health-recommendations'
};

// Utility functions
function getAQICategory(value) {
    if (value <= 50) return { name: 'Good', color: '#009966', class: 'aqi-good' };
    if (value <= 100) return { name: 'Moderate', color: '#ffde33', class: 'aqi-moderate' };
    if (value <= 150) return { name: 'Unhealthy for Sensitive Groups', color: '#ff9933', class: 'aqi-sensitive' };
    if (value <= 200) return { name: 'Unhealthy', color: '#cc0033', class: 'aqi-unhealthy' };
    if (value <= 300) return { name: 'Very Unhealthy', color: '#660099', class: 'aqi-very-unhealthy' };
    return { name: 'Hazardous', color: '#7e0023', class: 'aqi-hazardous' };
}

function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

// API service
const apiService = {
    // Generic fetch method with error handling
    async fetchData(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    // Dashboard data
    async getDashboardData() {
        return this.fetchData(API_ENDPOINTS.dashboard);
    },

    // Map data
    async getMapData() {
        return this.fetchData(API_ENDPOINTS.mapData);
    },

    // Most polluted countries data
    async getMostPollutedData() {
        return this.fetchData(API_ENDPOINTS.mostPolluted);
    },

    // AQI CSV data for tables and charts
    async getAqiCsvData() {
        return this.fetchData(API_ENDPOINTS.aqiCsvData);
    },

    // City-specific AQI data
    async getCityAqiData(cityName) {
        return this.fetchData(`${API_ENDPOINTS.cityAqi}${encodeURIComponent(cityName)}`);
    },

    // Country-specific data
    async getCountryData(countryName) {
        return this.fetchData(`${API_ENDPOINTS.countryData}${encodeURIComponent(countryName)}`);
    }
};

// Chart creation functions
function createCountriesChart(labels, data) {
    const ctx = document.getElementById('countries-chart').getContext('2d');
    
    // Generate colors based on AQI values
    const colors = data.map(value => getAQICategory(value).color);
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'AQI Value',
                data: data,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'AQI Value'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const category = getAQICategory(value).name;
                            return `AQI: ${value} (${category})`;
                        }
                    }
                }
            }
        }
    });
}

function createDistributionChart(categoryData) {
    const ctx = document.getElementById('aqi-distribution-chart').getContext('2d');
    
    // Prepare data
    const labels = [
        'Good',
        'Moderate',
        'Unhealthy for Sensitive Groups',
        'Unhealthy',
        'Very Unhealthy',
        'Hazardous'
    ];
    
    const colors = [
        '#009966', // Good
        '#ffde33', // Moderate
        '#ff9933', // Unhealthy for Sensitive Groups
        '#cc0033', // Unhealthy
        '#660099', // Very Unhealthy
        '#7e0023'  // Hazardous
    ];
    
    const data = [
        categoryData.Good || 0,
        categoryData.Moderate || 0,
        categoryData['Unhealthy for Sensitive Groups'] || 0,
        categoryData.Unhealthy || 0,
        categoryData['Very Unhealthy'] || 0,
        categoryData.Hazardous || 0
    ];
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${context.label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Dashboard initialization
async function initDashboard() {
    try {
        // Fetch dashboard data
        const dashboardData = await apiService.getDashboardData();
        console.log('Dashboard data:', dashboardData);
        
        // Update global AQI value
        const globalAqiElement = document.getElementById('global-aqi-value');
        const globalAqiCategory = document.getElementById('global-aqi-category');
        const aqi = dashboardData.global_avg_aqi;
        const aqiInfo = getAQICategory(aqi);
        
        globalAqiElement.textContent = Math.round(aqi);
        globalAqiElement.className = aqiInfo.class;
        globalAqiCategory.textContent = aqiInfo.name;
        globalAqiCategory.className = `mb-0 ${aqiInfo.class}`;
        
        // Update countries monitor count
        const monitoredCountriesElement = document.getElementById('monitored-countries');
        monitoredCountriesElement.textContent = dashboardData.monitored_countries_count;
        
        // Update progress bar
        const totalCountries = 195; // Approximate number of countries in the world
        const coverage = Math.round((dashboardData.monitored_countries_count / totalCountries) * 100);
        const progressBar = document.getElementById('coverage-progress');
        progressBar.style.width = `${coverage}%`;
        progressBar.setAttribute('aria-valuenow', coverage);
        
        // Update last updated time
        const updateTimeElement = document.getElementById('update-time');
        updateTimeElement.textContent = formatDateTime(dashboardData.timestamp);
        
        // Update countries chart
        const topCountries = dashboardData.top_polluted_countries;
        const countryLabels = topCountries.map(c => c.Country);
        const countryValues = topCountries.map(c => c['2024 Avg']);
        createCountriesChart(countryLabels, countryValues);
        
        // Update top countries list
        const topCountriesList = document.getElementById('top-countries-list');
        topCountriesList.innerHTML = '';
        topCountries.slice(0, 5).forEach((country, index) => {
            const aqiValue = country['2024 Avg'];
            const aqiInfo = getAQICategory(aqiValue);
            
            const listItem = document.createElement('div');
            listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            listItem.innerHTML = `
                <div>
                    <span class="fw-bold">${index + 1}. ${country.Country}</span>
                </div>
                <span class="badge ${aqiInfo.class} rounded-pill">${Math.round(aqiValue)}</span>
            `;
            topCountriesList.appendChild(listItem);
        });
        
        // Fetch AQI CSV data for category distribution
        const aqiCsvData = await apiService.getAqiCsvData();
        console.log('AQI CSV data:', aqiCsvData);
        
        // Update category counts
        const categoryCounts = aqiCsvData.category_counts;
        document.getElementById('category-good').textContent = categoryCounts['Good'] || 0;
        document.getElementById('category-moderate').textContent = categoryCounts['Moderate'] || 0;
        document.getElementById('category-sensitive').textContent = categoryCounts['Unhealthy for Sensitive Groups'] || 0;
        document.getElementById('category-unhealthy').textContent = categoryCounts['Unhealthy'] || 0;
        document.getElementById('category-very-unhealthy').textContent = categoryCounts['Very Unhealthy'] || 0;
        document.getElementById('category-hazardous').textContent = categoryCounts['Hazardous'] || 0;
        
        // Create distribution chart
        createDistributionChart(categoryCounts);
        
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        // Show error message to the user
        alert('Failed to load dashboard data. Please check the console for more information.');
    }
}

// Initialize the application based on the current page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Air Quality Dashboard initialized');
    
    // Identify the current page
    const currentPath = window.location.pathname;
    const pageName = currentPath.split('/').pop() || 'index.html';
    
    // Initialize appropriate functionality based on page
    if (pageName === 'index.html' || pageName === '') {
        console.log('Initializing home page');
        initDashboard();
    } else if (pageName === 'map.html') {
        console.log('Initializing map page');
        // Map page initialization would go here
    } else if (pageName === 'compare.html') {
        console.log('Initializing comparison page');
        // Comparison page initialization would go here
    } else if (pageName === 'health.html') {
        console.log('Initializing health page');
        // Health page initialization would go here
    }
});
