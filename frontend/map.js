// Map initialization and functionality
let map;
let markers = [];
let markerData = [];

// Initialize the map when the page is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing map page');
    initMap();
    loadMapData();
    setupFilterListeners();
});

function initMap() {
    // Create the map centered on the world
    map = L.map('map-container').setView([20, 0], 2);
    
    // Add the tile layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18
    }).addTo(map);
    
    // Add a scale control
    L.control.scale().addTo(map);
}

async function loadMapData() {
    try {
        // Fetch map data from the API
        const mapData = await apiService.getMapData();
        console.log('Map data loaded:', mapData);
        
        // Store the marker data
        markerData = mapData.markers;
        
        // Populate filter dropdowns
        populateFilterDropdowns(mapData.continents, mapData.countries);
        
        // Add markers to the map
        addMarkersToMap(markerData);
        
        // Update last updated time
        document.getElementById('map-update-time').textContent = formatDateTime(mapData.timestamp);
        
    } catch (error) {
        console.error('Failed to load map data:', error);
        document.getElementById('map-container').innerHTML = `
            <div class="alert alert-danger text-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Failed to load map data. Please try again later.
            </div>
        `;
    }
}

function populateFilterDropdowns(continents, countries) {
    // Populate continent dropdown
    const continentSelect = document.getElementById('continent-filter');
    continents.forEach(continent => {
        const option = document.createElement('option');
        option.value = continent;
        option.textContent = continent;
        continentSelect.appendChild(option);
    });
    
    // Populate country dropdown
    const countrySelect = document.getElementById('country-filter');
    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        countrySelect.appendChild(option);
    });
}

function addMarkersToMap(markers) {
    // Clear existing markers
    clearMarkers();
    
    // Add new markers
    markers.forEach(marker => {
        if (!marker.Latitude || !marker.Longitude) return;
        
        // Get marker color based on AQI category
        const color = marker.color || getAQICategory(marker.AQI).color;
        
        // Create custom icon
        const markerIcon = L.divIcon({
            className: 'custom-marker',
            html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`,
            iconSize: [15, 15],
            iconAnchor: [7, 7]
        });
        
        // Create marker with popup
        const mapMarker = L.marker([marker.Latitude, marker.Longitude], {
            icon: markerIcon,
            title: marker.City
        }).addTo(map);
        
        // Create popup content
        const popupContent = `
            <div class="marker-popup">
                <h5>${marker.City}, ${marker.Country}</h5>
                <div class="aqi-value" style="color: ${color}">
                    AQI: ${Math.round(marker.AQI)}
                </div>
                <div>${marker.AQI_Category}</div>
                <hr>
                <div class="pollutant-levels">
                    <div class="pollutant-item">
                        <span>PM2.5:</span>
                        <span>${marker['PM2.5'] || 'N/A'}</span>
                    </div>
                    <div class="pollutant-item">
                        <span>PM10:</span>
                        <span>${marker['PM10'] || 'N/A'}</span>
                    </div>
                    <div class="pollutant-item">
                        <span>O3:</span>
                        <span>${marker['O3'] || 'N/A'}</span>
                    </div>
                    <div class="pollutant-item">
                        <span>NO2:</span>
                        <span>${marker['NO2'] || 'N/A'}</span>
                    </div>
                </div>
                <div class="mt-2 small text-muted">
                    Last updated: ${marker.time || 'Unknown'}
                </div>
            </div>
        `;
        
        // Bind popup to marker
        mapMarker.bindPopup(popupContent);
        
        // Store marker for later reference
        markers.push({
            marker: mapMarker,
            data: marker
        });
    });
}

function clearMarkers() {
    // Remove all markers from the map
    markers.forEach(item => {
        map.removeLayer(item.marker);
    });
    
    // Clear markers array
    markers = [];
}

function setupFilterListeners() {
    // Continent filter
    document.getElementById('continent-filter').addEventListener('change', applyFilters);
    
    // Country filter
    document.getElementById('country-filter').addEventListener('change', applyFilters);
    
    // AQI category filters
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', applyFilters);
    });
    
    // Search button
    document.getElementById('search-btn').addEventListener('click', searchLocation);
    
    // Reset filters button
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
    
    // Search input - search on Enter key
    document.getElementById('search-input').addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            searchLocation();
        }
    });
}

function applyFilters() {
    // Get filter values
    const continent = document.getElementById('continent-filter').value;
    const country = document.getElementById('country-filter').value;
    
    // Get selected AQI categories
    const selectedCategories = [];
    document.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
        selectedCategories.push(checkbox.value);
    });
    
    // Filter marker data based on selection
    const filteredMarkers = markerData.filter(marker => {
        // Filter by continent
        if (continent && marker.Continent !== continent) return false;
        
        // Filter by country
        if (country && marker.Country !== country) return false;
        
        // Filter by AQI category
        if (!selectedCategories.includes(marker.AQI_Category)) return false;
        
        return true;
    });
    
    // Update markers on the map
    addMarkersToMap(filteredMarkers);
}

function searchLocation() {
    const searchTerm = document.getElementById('search-input').value.trim().toLowerCase();
    
    if (!searchTerm) return;
    
    // Find matching markers
    const matchingMarkers = markerData.filter(marker => {
        const cityMatch = marker.City && marker.City.toLowerCase().includes(searchTerm);
        const countryMatch = marker.Country && marker.Country.toLowerCase().includes(searchTerm);
        return cityMatch || countryMatch;
    });
    
    if (matchingMarkers.length > 0) {
        // Add the matching markers to the map
        addMarkersToMap(matchingMarkers);
        
        // Zoom to the first matching marker
        map.setView([matchingMarkers[0].Latitude, matchingMarkers[0].Longitude], 10);
        
        // Show a message with the number of results
        const resultMessage = `Found ${matchingMarkers.length} location(s) matching "${searchTerm}"`;
        console.log(resultMessage);
    } else {
        // No matches found
        alert(`No locations found matching "${searchTerm}". Please try a different search term.`);
    }
}

function resetFilters() {
    // Reset continent filter
    document.getElementById('continent-filter').value = '';
    
    // Reset country filter
    document.getElementById('country-filter').value = '';
    
    // Reset AQI category filters (check all)
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = true;
    });
    
    // Clear search input
    document.getElementById('search-input').value = '';
    
    // Reset map view
    map.setView([20, 0], 2);
    
    // Show all markers
    addMarkersToMap(markerData);
}