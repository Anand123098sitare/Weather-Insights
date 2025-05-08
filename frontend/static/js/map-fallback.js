/**
 * Map Fallback System
 * Provides an attractive default map with placeholder elements when API data fails to load
 */

function initializeFallbackMap() {
    console.log("Initializing fallback map display");
    
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) return;
    
    // Clear any error messages
    const existingErrors = mapContainer.querySelectorAll('.alert');
    existingErrors.forEach(el => el.remove());
    
    // If map already exists, don't re-initialize
    if (window.fallbackMapInitialized) return;
    
    try {
        // Create fallback map centered at a default location
        const fallbackMap = L.map('map-container', {
            zoomControl: false,
            attributionControl: false
        }).setView([20.5937, 78.9629], 4);

        // Add beautiful map tiles with a stylized look
        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(fallbackMap);
        
        // Add zoom control in an attractive position
        L.control.zoom({
            position: 'bottomright'
        }).addTo(fallbackMap);
        
        // Add sample major cities with decorative markers
        const majorCities = [
            { city: "New Delhi", country: "India", lat: 28.6139, lng: 77.2090, aqi: 85 },
            { city: "Mumbai", country: "India", lat: 19.0760, lng: 72.8777, aqi: 62 },
            { city: "Bangalore", country: "India", lat: 12.9716, lng: 77.5946, aqi: 48 },
            { city: "Kolkata", country: "India", lat: 22.5726, lng: 88.3639, aqi: 76 },
            { city: "Chennai", country: "India", lat: 13.0827, lng: 80.2707, aqi: 53 },
            { city: "Hyderabad", country: "India", lat: 17.3850, lng: 78.4867, aqi: 59 },
            { city: "Pune", country: "India", lat: 18.5204, lng: 73.8567, aqi: 55 },
            { city: "Jaipur", country: "India", lat: 26.9124, lng: 75.7873, aqi: 81 },
            { city: "Lucknow", country: "India", lat: 26.8467, lng: 80.9462, aqi: 88 },
            { city: "Ahmedabad", country: "India", lat: 23.0225, lng: 72.5714, aqi: 72 }
        ];
        
        // Add decorative markers to represent air quality
        majorCities.forEach(city => {
            addDecorativeMarker(fallbackMap, city);
        });
        
        // Add a gradient overlay for visual appeal
        const gradientOverlay = L.divOverlay(
            '<div class="map-gradient-overlay"></div>',
            {
                className: 'map-overlay-container'
            }
        ).addTo(fallbackMap);
        
        // Add an attractive information header
        const infoHeader = L.control({position: 'topleft'});
        infoHeader.onAdd = function(map) {
            const div = L.DomUtil.create('div', 'map-info-header');
            div.innerHTML = `
                <div class="map-data-status">
                    <i class="fas fa-info-circle"></i> 
                    <span>This is a visualization of Air Quality Index (AQI) across major cities.</span>
                </div>
            `;
            return div;
        };
        infoHeader.addTo(fallbackMap);
        
        // Add a visual legend
        addDecorativeLegend(fallbackMap);
        
        // Add pulsing effect to markers for visual interest
        addPulsingEffect();
        
        // Mark as initialized
        window.fallbackMapInitialized = true;
        
        // Create a refresh button that will try to load real data
        addRefreshButton(fallbackMap, mapContainer);
        
    } catch (error) {
        console.error("Error initializing fallback map:", error);
        // If even the fallback fails, show a clean error
        mapContainer.innerHTML = `
            <div class="map-error-container">
                <div class="map-error-icon"><i class="fas fa-map-marked-alt"></i></div>
                <h3>Map Visualization</h3>
                <p>Our interactive air quality map is taking a break. Please check back soon!</p>
                <button class="btn btn-primary mt-3" onclick="window.location.reload()">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
            </div>
        `;
    }
}

// Add decorative markers with nice styling
function addDecorativeMarker(map, cityData) {
    const color = getColorForAQI(cityData.aqi);
    
    // Create decorative marker with pulsing effect
    const markerHtml = `
        <div class="decorative-marker" style="background-color: ${color};">
            <div class="marker-pulse" style="background-color: ${color}"></div>
            <div class="marker-inner">${cityData.aqi}</div>
        </div>
    `;
    
    const icon = L.divIcon({
        html: markerHtml,
        className: 'decorative-marker-container',
        iconSize: [40, 40]
    });
    
    const marker = L.marker([cityData.lat, cityData.lng], {
        icon: icon
    });
    
    // Create an attractive popup
    const popupContent = `
        <div class="decorative-popup">
            <div class="popup-city">${cityData.city}</div>
            <div class="popup-country">${cityData.country}</div>
            <div class="popup-aqi" style="background-color: ${color}">
                <span class="popup-aqi-value">${cityData.aqi}</span>
                <span class="popup-aqi-label">AQI</span>
            </div>
            <div class="popup-category">${getAQICategoryText(cityData.aqi)}</div>
            <div class="popup-note">Sample visualization data</div>
        </div>
    `;
    
    marker.bindPopup(popupContent, {
        className: 'decorative-popup-container',
        maxWidth: 220
    });
    
    marker.addTo(map);
}

// Add a visually appealing legend
function addDecorativeLegend(map) {
    const legend = L.control({position: 'bottomleft'});
    
    legend.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'decorative-legend');
        div.innerHTML = `
            <div class="legend-title">Air Quality Index</div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #009966"></span>
                <span class="legend-text">0-50: Good</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #ffde33"></span>
                <span class="legend-text">51-100: Moderate</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #ff9933"></span>
                <span class="legend-text">101-150: Unhealthy for Sensitive Groups</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #cc0033"></span>
                <span class="legend-text">151-200: Unhealthy</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #660099"></span>
                <span class="legend-text">201-300: Very Unhealthy</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #7e0023"></span>
                <span class="legend-text">300+: Hazardous</span>
            </div>
        `;
        return div;
    };
    
    legend.addTo(map);
}

// Add a refresh button overlay
function addRefreshButton(map, container) {
    const refreshBtnDiv = document.createElement('div');
    refreshBtnDiv.className = 'map-refresh-overlay';
    refreshBtnDiv.innerHTML = `
        <button id="map-try-again" class="btn btn-primary">
            <i class="fas fa-sync-alt"></i> Try to load real data
        </button>
    `;
    
    container.appendChild(refreshBtnDiv);
    
    // Add click handler to attempt to reload real data
    document.getElementById('map-try-again').addEventListener('click', function() {
        // Try to reload the real map data
        window.location.reload();
    });
}

// Add CSS animations for pulsing effect
function addPulsingEffect() {
    // Check if we already added the style
    if (document.getElementById('map-pulse-styles')) return;
    
    const styleElement = document.createElement('style');
    styleElement.id = 'map-pulse-styles';
    styleElement.textContent = `
        @keyframes pulse {
            0% {
                transform: scale(1);
                opacity: 1;
            }
            100% {
                transform: scale(1.8);
                opacity: 0;
            }
        }
        
        .marker-pulse {
            position: absolute;
            border-radius: 50%;
            width: 100%;
            height: 100%;
            opacity: 0.5;
            z-index: -1;
            animation: pulse 2s infinite;
        }
        
        .decorative-marker {
            position: relative;
            width: 36px;
            height: 36px;
            border-radius: 18px;
            color: white;
            font-weight: bold;
            text-align: center;
            line-height: 36px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        .marker-inner {
            position: relative;
            z-index: 2;
        }
        
        .decorative-marker-container {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .decorative-popup {
            padding: 10px;
            text-align: center;
        }
        
        .popup-city {
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 2px;
        }
        
        .popup-country {
            color: #666;
            margin-bottom: 10px;
        }
        
        .popup-aqi {
            width: 70px;
            height: 70px;
            border-radius: 35px;
            margin: 0 auto 10px;
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }
        
        .popup-aqi-value {
            font-size: 24px;
            font-weight: bold;
            line-height: 1;
        }
        
        .popup-aqi-label {
            font-size: 12px;
        }
        
        .popup-category {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .popup-note {
            font-size: 11px;
            color: #999;
            font-style: italic;
        }
        
        .decorative-legend {
            background: white;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 250px;
            opacity: 0.9;
        }
        
        .legend-title {
            font-weight: bold;
            margin-bottom: 8px;
            text-align: center;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        
        .legend-color {
            width: 20px;
            height: 12px;
            margin-right: 8px;
            border-radius: 3px;
        }
        
        .legend-text {
            font-size: 12px;
        }
        
        .map-refresh-overlay {
            position: absolute;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        }
        
        .map-data-status {
            background: rgba(255,255,255,0.9);
            padding: 8px 12px;
            border-radius: 5px;
            margin: 10px;
            font-size: 14px;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .map-data-status i {
            margin-right: 8px;
            color: #3498db;
        }
        
        .map-gradient-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(to bottom, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
            pointer-events: none;
        }
        
        .map-error-container {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .map-error-icon {
            font-size: 40px;
            color: #3498db;
            margin-bottom: 15px;
        }
    `;
    
    document.head.appendChild(styleElement);
}

// Get appropriate AQI color
function getColorForAQI(aqi) {
    if (aqi <= 50) {
        return "#009966"; // Good
    } else if (aqi <= 100) {
        return "#ffde33"; // Moderate
    } else if (aqi <= 150) {
        return "#ff9933"; // Unhealthy for Sensitive Groups
    } else if (aqi <= 200) {
        return "#cc0033"; // Unhealthy
    } else if (aqi <= 300) {
        return "#660099"; // Very Unhealthy
    } else {
        return "#7e0023"; // Hazardous
    }
}

// Get AQI category text
function getAQICategoryText(aqi) {
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

// L.divOverlay - for adding div overlays to the map
L.divOverlay = function(html, options) {
    return new L.DivOverlay(html, options);
};

L.DivOverlay = L.Layer.extend({
    initialize: function(html, options) {
        this._html = html;
        L.setOptions(this, options);
    },
    
    onAdd: function(map) {
        this._map = map;
        this._container = L.DomUtil.create('div', this.options.className || '');
        this._container.innerHTML = this._html;
        
        map.getPanes().overlayPane.appendChild(this._container);
        return this;
    },
    
    onRemove: function(map) {
        if (this._container) {
            L.DomUtil.remove(this._container);
        }
    }
});

// Handle the error case by creating a fallback map display
function handleMapError() {
    console.log("Handling map error with fallback display");
    
    // Initialize fallback map with attractive visual elements
    initializeFallbackMap();
}