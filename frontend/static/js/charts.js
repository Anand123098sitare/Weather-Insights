/**
 * Global Air Quality Monitoring Dashboard - Charts Module
 * This module handles all chart creation and updates
 */

// Initialize charts object to store references to charts
let charts = {};

// Destroy existing chart if it exists
function destroyChart(chartId) {
    const chartInstance = Chart.getChart(chartId);
    if (chartInstance) {
        chartInstance.destroy();
    }
    if (charts[chartId]) {
        delete charts[chartId];
    }
}

// Chart utility functions
function getAQICategory(value) {
    if (value <= 50) return 'Good';
    if (value <= 100) return 'Moderate';
    if (value <= 150) return 'Unhealthy for Sensitive Groups';
    if (value <= 200) return 'Unhealthy';
    if (value <= 300) return 'Very Unhealthy';
    return 'Hazardous';
}

function getChartColor(value) {
    if (value <= 50) return '#00e400';
    if (value <= 100) return '#ffff00';
    if (value <= 150) return '#ff7e00';
    if (value <= 200) return '#ff0000';
    if (value <= 300) return '#8f3f97';
    return '#7e0023';
}

// Create and update charts
function createBarChart(elementId, labels, data, title) {
    const ctx = document.getElementById(elementId).getContext('2d');
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: data.map(getChartColor),
                borderColor: data.map(getChartColor),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            return `AQI: ${value} (${getAQICategory(value)})`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Air Quality Index (AQI)'
                    }
                }
            }
        }
    });
}


/**
 * Create a line chart showing monthly AQI data
 * @param {string} elementId - The ID of the canvas element
 * @param {string} title - Chart title
 * @param {array} labels - Array of month labels
 * @param {array} data - Array of AQI values
 * @param {string} color - Line color
 */
function createMonthlyAQIChart(elementId, title, labels, data, color = '#1a73e8') {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Determine gradient colors based on AQI values
    const gradientColors = data.map(value => getAQIColor(value));
    
    // Get background gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, `${color}33`); // Add transparency
    gradient.addColorStop(1, `${color}00`);
    
    // Create or update chart
    if (charts[elementId]) {
        charts[elementId].data.labels = labels;
        charts[elementId].data.datasets[0].data = data;
        charts[elementId].data.datasets[0].pointBackgroundColor = gradientColors;
        charts[elementId].options.plugins.title.text = title;
        charts[elementId].update();
    } else {
        charts[elementId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'AQI Value',
                    data: data,
                    borderColor: color,
                    backgroundColor: gradient,
                    pointBackgroundColor: gradientColors,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                return `AQI: ${value} (${getAQICategory(value)})`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: title,
                        font: {
                            size: 16
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Air Quality Index (AQI)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value;
                            }
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Month'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
}

/**
 * Create a bar chart showing most polluted countries/cities
 * @param {string} elementId - The ID of the canvas element
 * @param {string} title - Chart title
 * @param {array} labels - Array of country/city names
 * @param {array} data - Array of AQI values
 */
function createPollutionBarChart(elementId, title, labels, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Get colors based on AQI values
    const backgroundColors = data.map(value => getAQIColor(value));
    
    // Create or update chart
    if (charts[elementId]) {
        charts[elementId].data.labels = labels;
        charts[elementId].data.datasets[0].data = data;
        charts[elementId].data.datasets[0].backgroundColor = backgroundColors;
        charts[elementId].options.plugins.title.text = title;
        charts[elementId].update();
    } else {
        charts[elementId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'AQI Value',
                    data: data,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors.map(color => color + '99'),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                return `AQI: ${value} (${getAQICategory(value)})`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: title,
                        font: {
                            size: 16
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Air Quality Index (AQI)'
                        }
                    }
                }
            }
        });
    }
}

/**
 * Create a pie chart showing distribution of AQI categories
 * @param {string} elementId - The ID of the canvas element
 * @param {string} title - Chart title
 * @param {array} data - Array of counts for each category
 */
function createAQICategoryPieChart(elementId, title, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const labels = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous'];
    const colors = [
        '#009966', // Good
        '#ffde33', // Moderate
        '#ff9933', // Unhealthy for Sensitive Groups
        '#cc0033', // Unhealthy
        '#660099', // Very Unhealthy
        '#7e0023'  // Hazardous
    ];
    
    // Create or update chart
    if (charts[elementId]) {
        charts[elementId].data.datasets[0].data = data;
        charts[elementId].options.plugins.title.text = title;
        charts[elementId].update();
    } else {
        charts[elementId] = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${context.label}: ${value} (${percentage}%)`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: title,
                        font: {
                            size: 16
                        }
                    }
                }
            }
        });
    }
}

/**
 * Create comparison chart for two locations
 * @param {string} elementId - The ID of the canvas element
 * @param {string} title - Chart title
 * @param {array} labels - Array of month labels
 * @param {array} data1 - Array of AQI values for first location
 * @param {string} label1 - Label for first location
 * @param {array} data2 - Array of AQI values for second location
 * @param {string} label2 - Label for second location
 */
function createComparisonChart(elementId, title, labels, data1, label1, data2, label2) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Create or update chart
    if (charts[elementId]) {
        charts[elementId].data.labels = labels;
        charts[elementId].data.datasets[0].data = data1;
        charts[elementId].data.datasets[0].label = label1;
        charts[elementId].data.datasets[1].data = data2;
        charts[elementId].data.datasets[1].label = label2;
        charts[elementId].options.plugins.title.text = title;
        charts[elementId].update();
    } else {
        charts[elementId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: label1,
                        data: data1,
                        borderColor: '#1a73e8',
                        backgroundColor: '#1a73e833',
                        pointBackgroundColor: '#1a73e8',
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        tension: 0.3
                    },
                    {
                        label: label2,
                        data: data2,
                        borderColor: '#ea4335',
                        backgroundColor: '#ea433533',
                        pointBackgroundColor: '#ea4335',
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                return `${context.dataset.label}: ${value} (${getAQICategory(value)})`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: title,
                        font: {
                            size: 16
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Air Quality Index (AQI)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Month'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
}

/**
 * Get color based on AQI value
 * @param {number} aqi - Air Quality Index value
 * @returns {string} - CSS color code
 */
function getAQIColor(aqi) {
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
 * Get AQI category based on value
 * @param {number} aqi - Air Quality Index value
 * @returns {string} - AQI category
 */
function getAQICategory(aqi) {
    if (aqi <= 50) {
        return 'Good';
    } else if (aqi <= 100) {
        return 'Moderate';
    } else if (aqi <= 150) {
        return 'Unhealthy for Sensitive Groups';
    } else if (aqi <= 200) {
        return 'Unhealthy';
    } else if (aqi <= 300) {
        return 'Very Unhealthy';
    } else {
        return 'Hazardous';
    }
}

/**
 * Load country data and update charts
 * @param {string} country - Country name
 */
function loadCountryData(country) {
    fetch(`/api/country-data/${country}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Country data not found');
            }
            return response.json();
        })
        .then(data => {
            // Update the country info section
            document.getElementById('country-name').textContent = data.country;
            document.getElementById('country-avg-aqi').textContent = data.avg_aqi;
            document.getElementById('country-rank').textContent = data.rank;
            
            // Set class for AQI value display
            const aqiValueEl = document.getElementById('country-avg-aqi');
            aqiValueEl.className = 'aqi-value';
            aqiValueEl.classList.add(getAQIValueClass(data.avg_aqi));
            
            // Create or update monthly chart
            createMonthlyAQIChart(
                'country-monthly-chart',
                `Monthly AQI for ${data.country} (2024)`,
                data.months,
                data.monthly_data
            );
        })
        .catch(error => {
            console.error('Error loading country data:', error);
            document.getElementById('country-data-container').innerHTML = 
                `<div class="alert alert-danger">Error loading data for ${country}. Please try again.</div>`;
        });
}

/**
 * Load city data and update charts
 * @param {string} city - City name
 * @param {string} state - State name
 */
function loadCityData(city, state) {
    fetch(`/api/city-data/${city}/${state}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('City data not found');
            }
            return response.json();
        })
        .then(data => {
            // Update the city info section
            document.getElementById('city-name').textContent = data.city;
            document.getElementById('city-state').textContent = data.state;
            
            // Calculate city average AQI
            const avgAQI = data.monthly_data.reduce((sum, val) => sum + val, 0) / data.monthly_data.length;
            document.getElementById('city-avg-aqi').textContent = avgAQI.toFixed(1);
            
            // Set class for AQI value display
            const aqiValueEl = document.getElementById('city-avg-aqi');
            aqiValueEl.className = 'aqi-value';
            aqiValueEl.classList.add(getAQIValueClass(avgAQI));
            
            // Create or update monthly chart
            createMonthlyAQIChart(
                'city-monthly-chart',
                `Monthly AQI for ${data.city}, ${data.state} (2024)`,
                data.months,
                data.monthly_data,
                '#ea4335'
            );
        })
        .catch(error => {
            console.error('Error loading city data:', error);
            document.getElementById('city-data-container').innerHTML = 
                `<div class="alert alert-danger">Error loading data for ${city}, ${state}. Please try again.</div>`;
        });
}

/**
 * Get CSS class for AQI value styling
 * @param {number} aqi - Air Quality Index value
 * @returns {string} - CSS class name
 */
function getAQIValueClass(aqi) {
    if (aqi <= 50) {
        return 'aqi-good-bg';
    } else if (aqi <= 100) {
        return 'aqi-moderate-bg';
    } else if (aqi <= 150) {
        return 'aqi-sensitive-bg';
    } else if (aqi <= 200) {
        return 'aqi-unhealthy-bg';
    } else if (aqi <= 300) {
        return 'aqi-very-unhealthy-bg';
    } else {
        return 'aqi-hazardous-bg';
    }
}