// Initialize map variables
let map = null;
let markers = [];
let markerClusterGroup = null;
let useRealtimeData = true;
let currentCountry = 'India';

document.addEventListener('DOMContentLoaded', function() {
    const mapContainer = document.getElementById('map-container');

    if (mapContainer) {
        // Initialize map centered at India by default
        map = L.map('map-container', {
            zoomControl: false,
            attributionControl: false
        }).setView([20.5937, 78.9629], 5);

        // Set default filters for India
        currentCountry = 'India';

        // Add the base tile layer
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);

        // Initialize marker cluster group
        markerClusterGroup = L.markerClusterGroup({
            disableClusteringAtZoom: 10,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            maxClusterRadius: 40
        });

        // Load India marker data by default
        fetch('/api/india-aqi-data')
            .then(response => response.json())
            .then(data => {
                try {
                    // Make sure we handle any potential NaN or invalid values
                    const cleanedData = (Array.isArray(data) ? data : []).filter(item => {
                        return item && typeof item === 'object' && item.Country === 'India';
                    }).map(item => ({
                        ...item,
                        AQI: !isNaN(parseFloat(item.AQI)) ? parseFloat(item.AQI) : 0,
                        Latitude: !isNaN(parseFloat(item.Latitude)) ? parseFloat(item.Latitude) : 0,
                        Longitude: !isNaN(parseFloat(item.Longitude)) ? parseFloat(item.Longitude) : 0,
                        City: item.City || 'Unknown',
                        Country: item.Country || 'Unknown'
                    }));

                    if (cleanedData.length === 0) {
                        throw new Error('No valid data found');
                    }

                    addMarkers(cleanedData);
                    map.addLayer(markerClusterGroup);

                    // Add legend after markers are loaded
                    addLegend();
                } catch (error) {
                    console.error('Error processing marker data:', error);
                    // Fallback to static data
                    fetch('/static/data/marker_data.json')
                        .then(response => response.json())
                        .then(staticData => {
                            const indiaData = staticData.filter(item => item.Country === 'India');
                            addMarkers(indiaData);
                            map.addLayer(markerClusterGroup);
                            addLegend();
                        });
                }
            })
            .catch(error => {
                console.error('Error loading marker data:', error);
                // Display error message on the map
                const mapContainer = document.getElementById('map-container');
                if (mapContainer) {
                    mapContainer.innerHTML += '<div class="alert alert-danger" style="position:absolute; top:10px; left:10px; z-index:1000;">Error loading map data. Please try refreshing the page.</div>';
                }
            });
    }
});

// Search functionality
document.addEventListener('DOMContentLoaded', function() {
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) return;

    const searchInput = document.getElementById('location-search');
    const searchResults = document.getElementById('search-results');
    if (!searchInput || !searchResults) return;

    let markers = [];

    // Load India-specific marker data
    fetch('/api/india-aqi-data')
        .then(response => response.json())
        .then(data => {
            if (Array.isArray(data)) {
                markers = data.filter(item => item.Country === 'India').map(marker => ({
                    ...marker,
                    // Handle potential NaN values or missing fields
                    City: marker.City || 'Unknown',
                    Country: marker.Country || 'Unknown',
                    AQI: !isNaN(parseFloat(marker.AQI)) ? parseFloat(marker.AQI) : 0,
                    Latitude: !isNaN(parseFloat(marker.Latitude)) ? parseFloat(marker.Latitude) : 0,
                    Longitude: !isNaN(parseFloat(marker.Longitude)) ? parseFloat(marker.Longitude) : 0
                }));
            } else {
                console.error('Invalid marker data format');
            }
        })
        .catch(error => {
            console.error('Error loading marker data:', error);
        });

    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        if (searchTerm.length < 2) {
            searchResults.style.display = 'none';
            return;
        }

        const filteredMarkers = markers.filter(marker =>
            marker.City.toLowerCase().includes(searchTerm) ||
            marker.Country.toLowerCase().includes(searchTerm)
        ).slice(0, 5);

        if (filteredMarkers.length > 0) {
            searchResults.innerHTML = filteredMarkers.map(marker => `
                <div class="search-result-item" data-lat="${marker.Latitude}" data-lng="${marker.Longitude}">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>${marker.City}, ${marker.Country}</span>
                    <span class="search-result-aqi" style="background-color: ${marker.color}">${Math.round(marker.AQI)}</span>
                </div>
            `).join('');
            searchResults.style.display = 'block';

            // Add click handlers to results
            document.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', function() {
                    const lat = parseFloat(this.dataset.lat);
                    const lng = parseFloat(this.dataset.lng);
                    map.setView([lat, lng], 12);
                    searchResults.style.display = 'none';
                    searchInput.value = this.querySelector('span').textContent;
                });
            });
        } else {
            searchResults.style.display = 'none';
        }
    });

    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchResults.contains(e.target) && e.target !== searchInput) {
            searchResults.style.display = 'none';
        }
    });

    // Use current location
    document.getElementById('use-location').addEventListener('click', function() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(position => {
                map.setView([position.coords.latitude, position.coords.longitude], 12);
            });
        }
    });
});

/**
 * Global Air Quality Monitoring Dashboard - Map Module
 * This module handles the interactive air quality map
 * Designed to resemble IQAir's air quality map
 */


/**
 * Initialize the map with air quality markers
 * @param {Array} markerData - Array of marker data objects
 */
function initMap(markerData) {
    // Create the map centered at India by default
    map = L.map('map-container', {
        zoomControl: false,
        attributionControl: false,
    }).setView([20.5937, 78.9629], 4);

    // Add the base tile layer (light style similar to IQAir)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // Add zoom control to bottom right
    L.control.zoom({
        position: 'bottomright'
    }).addTo(map);

    // Add attribution to bottom left
    L.control.attribution({
        position: 'bottomleft',
        prefix: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
    }).addTo(map);

    // Initialize the marker cluster group with custom styling
    markerClusterGroup = L.markerClusterGroup({
        disableClusteringAtZoom: 10,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        maxClusterRadius: 40,
        iconCreateFunction: function(cluster) {
            const count = cluster.getChildCount();
            return L.divIcon({
                html: `<div class="iqair-cluster">${count}</div>`,
                className: '',
                iconSize: L.point(45, 45)
            });
        }
    });

    // Add markers to the map
    addMarkers(markerData);

    // Add the marker cluster group to the map
    map.addLayer(markerClusterGroup);

    // Initialize the map controls
    initMapControls();
}

/**
 * Add markers to the map based on the provided data
 * @param {Array} markerData - Array of marker data objects
 */
function addMarkers(markerData) {
    // Clear existing markers
    if (markerClusterGroup) {
        markerClusterGroup.clearLayers();
    }
    markers = [];

    // Add new markers
    markerData.forEach(data => {
        const lat = parseFloat(data.Latitude);
        const lng = parseFloat(data.Longitude);

        if (!isNaN(lat) && !isNaN(lng)) {
            const marker = createMarker(lat, lng, data);

            // Only add valid markers (createMarker can return null for invalid data)
            if (marker) {
                markers.push(marker);
                markerClusterGroup.addLayer(marker);
            }
        }
    });
}

/**
 * Create a marker with air quality data
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @param {Object} data - Marker data object
 * @returns {L.Marker} - Leaflet marker
 */
function createMarker(lat, lng, data) {
    try {
        // Validate coordinates
        if (isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) {
            console.warn('Invalid coordinates for marker:', data);
            return null;
        }
        
        // Validate required data
        if (!data || typeof data !== 'object') {
            console.warn('Invalid data object for marker');
            return null;
        }

        // Ensure AQI is a valid number
        const aqi = !isNaN(parseFloat(data.AQI)) ? parseFloat(data.AQI) : 0;

        // Determine marker color based on AQI category
        const color = getColorForAQI(aqi);

        // Create a custom div icon similar to IQAir markers
        const markerHtml = `<div class="iqair-main-marker" style="background-color: ${color};">${Math.round(aqi)}</div>`;
        const customIcon = L.divIcon({
            html: markerHtml,
            className: '',
            iconSize: [36, 36]
        });

        // Create the marker with the custom icon and store data for later use
        const marker = L.marker([lat, lng], {
            icon: customIcon,
            data: data
        });

    // Format the location info
    const city = data.City || 'Unknown City';
    const country = data.Country || 'Unknown Country';

    // Handle timestamp formatting
    let timeInfo = '';
    if (data.time) {
        try {
            const date = new Date(data.time);
            // Check if date is valid
            if (!isNaN(date.getTime())) {
                timeInfo = `<div class="popup-last-updated">Last updated: ${date.toLocaleString()}</div>`;
            } else {
                timeInfo = `<div class="popup-last-updated">Last updated: ${data.time}</div>`;
            }
        } catch (e) {
            console.warn('Invalid date format:', data.time);
            timeInfo = `<div class="popup-last-updated">Last updated: Recently</div>`;
        }
    }

    // Get PM2.5 value, checking for both PM2_5 and PM2.5 property names
    const pm25Value = data.PM2_5 !== undefined ? data.PM2_5 : (data['PM2.5'] !== undefined ? data['PM2.5'] : null);
    const pm25Category = data.PM2_5_Category !== undefined ? data.PM2_5_Category : (data['PM2.5_Category'] !== undefined ? data['PM2.5_Category'] : null);

    // Prepare pollutant data with fallbacks for missing values
    const pm25 = pm25Value !== null ? `${pm25Value} ${pm25Category ? `(${pm25Category})` : ''}` : 'N/A';
    const pm10 = data.PM10 !== undefined ? `${data.PM10} ${data.PM10_Category ? `(${data.PM10_Category})` : ''}` : 'N/A';
    const o3 = data.O3 !== undefined ? `${data.O3} ${data.O3_Category ? `(${data.O3_Category})` : ''}` : 'N/A';
    const no2 = data.NO2 !== undefined ? `${data.NO2} ${data.NO2_Category ? `(${data.NO2_Category})` : ''}` : 'N/A';

    // Create popup content
    const popupContent = `
        <div class="marker-popup">
            <div class="location-badge">${country}</div>
            <h5>${city}</h5>
            <div class="aqi-display" style="background-color: ${color}; color: ${getTextColorForBackground(color)}">
                ${Math.round(data.AQI)}
                <div style="font-size: 12px; margin-top: 5px;">${data.AQI_Category || getAQICategoryFromValue(data.AQI)}</div>
            </div>
            <table class="popup-table">
                <tr>
                    <td>PM2.5:</td>
                    <td>${pm25}</td>
                </tr>
                <tr>
                    <td>PM10:</td>
                    <td>${pm10}</td>
                </tr>
                <tr>
                    <td>O3:</td>
                    <td>${o3}</td>
                </tr>
                <tr>
                    <td>NO2:</td>
                    <td>${no2}</td>
                </tr>
            </table>
            ${timeInfo}
        </div>
    `;

    // Bind popup to marker
    marker.bindPopup(popupContent, {
        maxWidth: 300
    });

    return marker;
    } catch (error) {
        console.error('Error creating marker:', error);
        return null;
    }
}

/**
 * Get AQI category label from value
 * @param {number} aqi - AQI value
 * @returns {string} - AQI category name
 */
function getAQICategoryFromValue(aqi) {
    if (aqi <= 50) {
        return "Good";
    } else if (aqi <= 100) {
        return "Moderate";
    } else if (aqi <= 150) {
        return "Unhealthy for Sensitive Groups";
    } else if (aqi <= 200) {
        return "Unhealthy";
    } else if (aqi <= 300) {
        return "Very Unhealthy";
    } else {
        return "Hazardous";
    }
}

/**
 * Initialize the map controls (IQAir-style)
 */
function initMapControls() {
    // Refresh button
    const refreshBtn = document.getElementById('map-refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            refreshMapData();
        });
    }

    // My location button
    const locateBtn = document.getElementById('map-locate-btn');
    if (locateBtn) {
        locateBtn.addEventListener('click', function() {
            locateUser();
        });
    }

    // Fullscreen button
    const fullscreenBtn = document.getElementById('map-fullscreen-btn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', function() {
            toggleFullscreen();
        });
    }

    // Real-time API data toggle
    const realtimeToggle = document.getElementById('realtime-toggle');
    if (realtimeToggle) {
        realtimeToggle.addEventListener('change', function() {
            useRealtimeData = this.checked;
            refreshMapData();

            // Update real-time indicator
            const indicator = document.querySelector('.live-data-badge');
            if (indicator) {
                indicator.style.display = useRealtimeData ? 'flex' : 'none';
            }
        });
    }

    // Focus on India button
    const focusIndiaBtn = document.getElementById('focus-india-btn');
    if (focusIndiaBtn) {
        focusIndiaBtn.addEventListener('click', function() {
            map.setView([20.5937, 78.9629], 4);
            document.getElementById('country-select').value = 'India';
            currentCountry = 'India';
            filterMarkersForIndia();
            // Update weather info after region change
            updateWeatherInfo();
        });
    }

    // Global view button
    const viewGlobalBtn = document.getElementById('view-global-btn');
    if (viewGlobalBtn) {
        viewGlobalBtn.addEventListener('click', function() {
            map.setView([20.0, 0.0], 2);
            document.getElementById('country-select').value = 'All';
            currentCountry = 'All';
            filterMarkers('All', 'All', 'All');
            // Update weather info after region change
            updateWeatherInfo();
        });
    }

    // Initial weather info update
    updateWeatherInfo();
}

/**
 * Get color for AQI value
 * @param {number} aqi - Air Quality Index value
 * @returns {string} - CSS color code
 */
function getColorForAQI(aqi) {
    if (aqi <= 50) {
        return '#009966'; // Good
    } else if (aqi <= 100) {
        return '#ffde33'; // Moderate
    } else if (aqi <= 150) {
        return '#ff9933'; // Unhealthy for Sensitive Groups
    } else if (aqi <= 200) {
        return '#cc0033'; // Unhealthy
    } else if (aqi <= 300) {
        return '#660099'; // Very Unhealthy
    } else {
        return '#7e0023'; // Hazardous
    }
}

/**
 * Get text color for background color
 * @param {string} backgroundColor - Background color
 * @returns {string} - Text color (white or black)
 */
function getTextColorForBackground(backgroundColor) {
    // Yellow/moderate color needs dark text, others use white
    if (backgroundColor === '#ffde33') {
        return '#000000';
    }
    return '#ffffff';
}

/**
 * Add AQI legend to the map
 */
function addLegend() {
    const legend = L.control({ position: 'bottomright' });

    legend.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'aqi-legend');
        div.innerHTML = `
            <div style="background: white; padding: 10px; border-radius: 5px; box-shadow: 0 1px 5px rgba(0,0,0,0.4)">
                <h6 style="margin-top: 0; margin-bottom: 5px;">Air Quality Index</h6>
                <div><i style="background: #009966; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Good (0-50)</div>
                <div><i style="background: #ffde33; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Moderate (51-100)</div>
                <div><i style="background: #ff9933; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Unhealthy for Sensitive Groups (101-150)</div>
                <div><i style="background: #cc0033; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Unhealthy (151-200)</div>
                <div><i style="background: #660099; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Very Unhealthy (201-300)</div>
                <div><i style="background: #7e0023; width: 18px; height: 18px; display: inline-block; margin-right: 5px;"></i> Hazardous (301+)</div>
            </div>
        `;
        return div;
    };

    legend.addTo(map);
}

/**
 * Filter markers based on user selection
 * @param {string} continent - Selected continent
 * @param {string} country - Selected country
 * @param {string} city - Selected city
 */
function filterMarkers(continent, country, city) {
    // Show loading indicator
    document.getElementById('map-loading').style.display = 'block';

    // Fetch filtered data from the API
    fetch(`/api/filter-markers?continent=${continent}&country=${country}&city=${city}`)
        .then(response => response.json())
        .then(data => {
            // Update markers on the map
            addMarkers(data);

            // Update weather info with the new marker data
            updateWeatherInfo();

            // Hide loading indicator
            document.getElementById('map-loading').style.display = 'none';
        })
        .catch(error => {
            console.error('Error filtering markers:', error);
            // Hide loading indicator
            document.getElementById('map-loading').style.display = 'none';

            // Show error message
            alert('Error filtering markers. Please try again.');
        });
}

/**
 * Initialize event listeners for map filters
 */
function initMapFilters() {
    const continentSelect = document.getElementById('continent-select');
    const countrySelect = document.getElementById('country-select');
    const citySelect = document.getElementById('city-select');
    const resetButton = document.getElementById('reset-button');

    continentSelect.addEventListener('change', function() {
        filterMarkers(
            continentSelect.value,
            countrySelect.value,
            citySelect.value
        );
    });

    countrySelect.addEventListener('change', function() {
        filterMarkers(
            continentSelect.value,
            countrySelect.value,
            citySelect.value
        );
    });

    citySelect.addEventListener('change', function() {
        filterMarkers(
            continentSelect.value,
            countrySelect.value,
            citySelect.value
        );
    });

    resetButton.addEventListener('click', function() {
        continentSelect.value = 'All';
        countrySelect.value = 'All';
        citySelect.value = 'All';
        filterMarkers('All', 'All', 'All');
    });
}

/**
 * Resize map when container size changes
 */
function handleResize() {
    if (map) {
        map.invalidateSize();
    }
}

// Add event listener for window resize
window.addEventListener('resize', handleResize);

// Add event listener for tab changes that might affect map size
document.addEventListener('shown.bs.tab', function(e) {
    if (e.target.getAttribute('href') === '#map-tab') {
        handleResize();
    }
});

/**
 * Refresh map data with real-time API data (if enabled)
 */
function refreshMapData() {
    // Show loading indicator
    document.getElementById('map-loading').style.display = 'block';

    if (useRealtimeData && currentCountry === 'India') {
        // Fetch real-time data from India API
        fetch('/api/india-aqi-data?refresh=true')
            .then(response => response.json())
            .then(data => {
                // Update the markers
                addMarkers(data);
                // Hide loading indicator
                // Update weather info with the new marker data
                updateWeatherInfo();
                document.getElementById('map-loading').style.display = 'none';
                // Update last updated timestamp
                updateLastUpdated(new Date().toISOString());
            })
            .catch(error => {
                console.error('Error refreshing map data:', error);
                document.getElementById('map-loading').style.display = 'none';
                alert('Error refreshing data. Please try again.');
            });
    } else {
        // Use the regular filter API
        const continentSelect = document.getElementById('continent-select');
        const countrySelect = document.getElementById('country-select');
        const citySelect = document.getElementById('city-select');

        let apiUrl = `/api/filter-markers?continent=${continentSelect.value}&country=${countrySelect.value}&city=${citySelect.value}`;

        // Add real-time flag if using real-time data
        if (useRealtimeData) {
            apiUrl += '&use_api=true';
        }

        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                // Update the markers
                addMarkers(data);
                // Hide loading indicator
                // Update weather info with the new marker data
                updateWeatherInfo();
                document.getElementById('map-loading').style.display = 'none';
                // Update last updated timestamp
                updateLastUpdated(new Date().toISOString());
            })
            .catch(error => {
                console.error('Error refreshing map data:', error);
                document.getElementById('map-loading').style.display = 'none';
                alert('Error refreshing data. Please try again.');
            });
    }
}

/**
 * Filter markers specifically for India with real-time data
 */
function filterMarkersForIndia() {
    // Show loading indicator
    document.getElementById('map-loading').style.display = 'block';

    // Use real-time data if enabled
    if (useRealtimeData) {
        fetch('/api/india-aqi-data')
            .then(response => response.json())
            .then(data => {
                // Update markers on the map
                addMarkers(data);
                // Hide loading indicator
                document.getElementById('map-loading').style.display = 'none';
            })
            .catch(error => {
                console.error('Error fetching India data:', error);
                // Fallback to regular filter
                filterMarkers('Asia', 'India', 'All');
            });
    } else {
        // Use the stored data
        filterMarkers('Asia', 'India', 'All');
    }
}

/**
 * Locate the user's position and zoom the map to that location
 */
function locateUser() {
    if (navigator.geolocation) {
        // Show loading indicator
        document.getElementById('map-loading').style.display = 'block';

        navigator.geolocation.getCurrentPosition(
            // Success callback
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                // Zoom to user's location
                map.setView([lat, lng], 10);

                // Create a temporary marker
                const userMarker = L.marker([lat, lng], {
                    icon: L.divIcon({
                        html: '<i class="fas fa-map-marker-alt" style="color: #0071bc; font-size: 24px;"></i>',
                        className: '',
                        iconSize: [24, 24]
                    })
                }).addTo(map);

                // Add a popup
                userMarker.bindPopup('Your location').openPopup();

                // Remove the marker after 5 seconds
                setTimeout(() => {
                    map.removeLayer(userMarker);
                }, 5000);

                // Hide loading indicator
                document.getElementById('map-loading').style.display = 'none';
            },
            // Error callback
            function(error) {
                console.error('Error getting user location:', error);
                alert('Unable to get your location. Please make sure location services are enabled in your browser.');
                // Hide loading indicator
                document.getElementById('map-loading').style.display = 'none';
            }
        );
    } else {
        alert('Geolocation is not supported by your browser.');
    }
}

/**
 * Toggle fullscreen mode for the map container
 */
function toggleFullscreen() {
    const mapContainer = document.getElementById('map-container');
    const fullscreenBtn = document.getElementById('map-fullscreen-btn');

    if (!document.fullscreenElement) {
        // Enter fullscreen
        if (mapContainer.requestFullscreen) {
            mapContainer.requestFullscreen();
        } else if (mapContainer.mozRequestFullScreen) {
            mapContainer.mozRequestFullScreen();
        } else if (mapContainer.webkitRequestFullscreen) {
            mapContainer.webkitRequestFullscreen();
        } else if (mapContainer.msRequestFullscreen) {
            mapContainer.msRequestFullscreen();
        }

        // Change icon
        const icon = fullscreenBtn.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-compress';
        }
    } else {
        // Exit fullscreen
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }

        // Change icon back
        const icon = fullscreenBtn.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-expand';
        }
    }

    // Resize the map after a short delay to ensure it renders correctly
    setTimeout(() => {
        handleResize();
    }, 100);
}

/**
 * Update the last updated timestamp display
 * @param {string} timestamp - ISO date string
 */
function updateLastUpdated(timestamp) {
    const date = new Date(timestamp);
    const formattedDate = date.toLocaleString();

    // Update the timestamp in the UI if there's an element for it
    const timestampElement = document.getElementById('last-updated-time');
    if (timestampElement) {
        timestampElement.textContent = formattedDate;
    }
}

/**
 * Update the weather information display in the IQAir-style map
 * Uses the most recent marker data for wind and temperature
 */
function updateWeatherInfo() {
    // Update main AQI display
    const currentAQI = document.getElementById('current-aqi');
    const aqiCategory = document.getElementById('aqi-category');
    const pm10Value = document.getElementById('pm10-value');
    const pm25Value = document.getElementById('pm25-value');
    const temperatureValue = document.getElementById('temperature-value');
    const humidityValue = document.getElementById('humidity-value');
    const windSpeedEl = document.getElementById('wind-speed');
    const windDirectionEl = document.getElementById('wind-direction');
    const uvIndexEl = document.getElementById('uv-index');
    const aqiMascot = document.getElementById('aqi-mascot');

    if (!windSpeedEl || !temperatureValue) {
        return; // Elements not found
    }

    // Find an appropriate marker with weather data
    if (markers && markers.length > 0) {
        // Set default values
        let windSpeed = "3.5 km/h";
        let temperature = "28°C";
        let windDirection = 120;
        let found = false;

        // Look for markers with weather data
        for (const marker of markers) {
            if (marker && marker.options && marker.options.data) {
                const data = marker.options.data;

                // Check if this marker has wind speed data
                if (data.wind_speed) {
                    windSpeed = `${data.wind_speed} km/h`;
                    found = true;
                }

                // Check if this marker has temperature data
                if (data.temperature) {
                    temperature = `${data.temperature}°C`;
                    found = true;
                }

                // Check if this marker has wind direction data
                if (data.wind_direction) {
                    windDirection = data.wind_direction;
                    found = true;
                }

                // If we found data, we can stop looking
                if (found) {
                    break;
                }
            }
        }

        // Update the wind speed display
        windSpeedEl.textContent = windSpeed;

        // Update the temperature display
        temperatureValue.textContent = temperature;

        // Rotate the wind icon based on wind direction
        const windIcon = document.querySelector('.iqair-wind i');
        if (windIcon) {
            windIcon.style.transform = `rotate(${windDirection}deg)`;
        }
    }
}