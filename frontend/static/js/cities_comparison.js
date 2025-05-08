/**
 * Cities Comparison JavaScript
 * Handles functionality for city comparison charts using data from Indian cities CSV file
 */

document.addEventListener('DOMContentLoaded', function() {
    // Cities data will be loaded here
    let comparisonChart = null;
    let seasonalComparisonChart = null;
    let countryChart = null;

    // Month labels for charts
    const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    console.log('City dropdowns loaded from server-side data');
    
    // Update the placeholder to show we're ready for comparison
    const city1Select = document.getElementById('city1-select');
    const city2Select = document.getElementById('city2-select');
    
    // Check if we already have options (server-side rendering)
    const cityCount = city1Select.options.length - 1; // Subtract 1 for the placeholder
    
    if (cityCount > 0) {
        console.log(`Found ${cityCount} cities already loaded in the dropdowns`);
        document.getElementById('city-comparison-placeholder').innerHTML = 
            `<div class="mb-4 opacity-50">
                <i class="fas fa-chart-bar fa-4x"></i>
            </div>
            <h4>Select Two Indian Cities Above to Compare</h4>
            <p class="text-muted">The chart will display monthly air quality trends for both cities.</p>
            <p class="text-muted">You'll see detailed seasonal patterns, peak pollution months, and air quality variations across the year.</p>`;
    }
    
    // Set up compare button event listener
    const compareButton = document.getElementById('compare-cities-button');
    if (compareButton) {
        compareButton.addEventListener('click', function() {
            compareCities();
        });
    }
    
    // Function to compare the selected cities
    function compareCities() {
        const city1Select = document.getElementById('city1-select');
        const city2Select = document.getElementById('city2-select');
        
        if (!city1Select.value || !city2Select.value) {
            alert('Please select two cities to compare');
            return;
        }
        
        // Get selected city and state names
        const [city1Name, city1State] = city1Select.value.split('|');
        const [city2Name, city2State] = city2Select.value.split('|');
        
        console.log(`Comparing: ${city1Name}, ${city1State} with ${city2Name}, ${city2State}`);
        
        // Show loading message
        document.getElementById('city-comparison-placeholder').innerHTML = 
            `<div class="mb-4 text-primary">
                <i class="fas fa-spinner fa-spin fa-4x"></i>
            </div>
            <h4>Loading comparison data...</h4>
            <p class="text-muted">Please wait while we retrieve detailed air quality information.</p>`;
        
        // Fetch the detailed comparison data from our new endpoint
        fetch(`/api/city-comparison-data?city1=${encodeURIComponent(city1Name)}&state1=${encodeURIComponent(city1State)}&city2=${encodeURIComponent(city2Name)}&state2=${encodeURIComponent(city2State)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Check if we have data for both cities
                if (!data.city1 || !data.city2) {
                    throw new Error('Missing city data in the response');
                }
                
                console.log('Comparing cities:', data.city1.city, 'and', data.city2.city);
                
                // Show the chart container
                document.querySelector('.chart-container').style.display = 'block';
                
                // Create the comparison charts
                createComparisonChart(data.city1, data.city2);
                
                // Show the city stats comparison section
                createCityStatsCards(data.city1, data.city2);
                
                // Create seasonal comparison chart
                createSeasonalComparisonChart(data.city1, data.city2);
                
                // Hide the placeholder
                document.getElementById('city-comparison-placeholder').style.display = 'none';
            })
            .catch(error => {
                console.error('Error in city comparison:', error);
                document.getElementById('city-comparison-placeholder').innerHTML = 
                    `<div class="mb-4 text-danger">
                        <i class="fas fa-exclamation-triangle fa-4x"></i>
                    </div>
                    <h4>Failed to load comparison data</h4>
                    <p class="text-muted">Unable to retrieve detailed air quality data. Please try again later.</p>`;
            });
    }
    
    // Function to create city stats cards for comparison
    function createCityStatsCards(city1Data, city2Data) {
        const cityStatsContainer = document.getElementById('city-stats-comparison');
        cityStatsContainer.style.display = 'flex';
        
        // Helper function to get AQI class
        function getAQIClass(aqi) {
            if (aqi <= 50) return 'good';
            if (aqi <= 100) return 'moderate';
            if (aqi <= 150) return 'sensitive';
            if (aqi <= 200) return 'unhealthy';
            if (aqi <= 300) return 'very-unhealthy';
            return 'hazardous';
        }
        
        // Create city info cards
        cityStatsContainer.innerHTML = `
            <div class="city-info-card">
                <div class="city-info-header aqi-${getAQIClass(city1Data.avg_aqi)}">
                    <h4>${city1Data.city}, ${city1Data.state}</h4>
                    <div class="aqi-badge">${city1Data.avg_aqi}</div>
                </div>
                <div class="city-info-body">
                    <div class="info-row">
                        <span>Peak Pollution:</span>
                        <span class="text-danger">${city1Data.peak_month} (${city1Data.peak_value})</span>
                    </div>
                    <div class="info-row">
                        <span>Cleanest Month:</span>
                        <span class="text-success">${city1Data.cleanest_month} (${city1Data.cleanest_value})</span>
                    </div>
                    <div class="info-row">
                        <span>Winter Avg:</span>
                        <span>${city1Data.seasonal_data.winter}</span>
                    </div>
                    <div class="info-row">
                        <span>Summer Avg:</span>
                        <span>${city1Data.seasonal_data.summer}</span>
                    </div>
                    <div class="info-row">
                        <span>Monsoon Avg:</span>
                        <span>${city1Data.seasonal_data.monsoon}</span>
                    </div>
                    <div class="info-row">
                        <span>Post-Monsoon Avg:</span>
                        <span>${city1Data.seasonal_data.post_monsoon}</span>
                    </div>
                </div>
            </div>
            
            <div class="city-info-card">
                <div class="city-info-header aqi-${getAQIClass(city2Data.avg_aqi)}">
                    <h4>${city2Data.city}, ${city2Data.state}</h4>
                    <div class="aqi-badge">${city2Data.avg_aqi}</div>
                </div>
                <div class="city-info-body">
                    <div class="info-row">
                        <span>Peak Pollution:</span>
                        <span class="text-danger">${city2Data.peak_month} (${city2Data.peak_value})</span>
                    </div>
                    <div class="info-row">
                        <span>Cleanest Month:</span>
                        <span class="text-success">${city2Data.cleanest_month} (${city2Data.cleanest_value})</span>
                    </div>
                    <div class="info-row">
                        <span>Winter Avg:</span>
                        <span>${city2Data.seasonal_data.winter}</span>
                    </div>
                    <div class="info-row">
                        <span>Summer Avg:</span>
                        <span>${city2Data.seasonal_data.summer}</span>
                    </div>
                    <div class="info-row">
                        <span>Monsoon Avg:</span>
                        <span>${city2Data.seasonal_data.monsoon}</span>
                    </div>
                    <div class="info-row">
                        <span>Post-Monsoon Avg:</span>
                        <span>${city2Data.seasonal_data.post_monsoon}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Function to create comparison chart
    function createComparisonChart(city1Data, city2Data) {
        const chartContext = document.getElementById('cities-comparison-chart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (comparisonChart) {
            comparisonChart.destroy();
        }
        
        // Prepare chart data
        const chartData = {
            labels: monthLabels,
            datasets: [
                {
                    label: city1Data.city,
                    data: city1Data.monthly_data,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderWidth: 2,
                    pointRadius: 4,
                    tension: 0.1
                },
                {
                    label: city2Data.city,
                    data: city2Data.monthly_data,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderWidth: 2,
                    pointRadius: 4,
                    tension: 0.1
                }
            ]
        };
        
        // Chart configuration
        const chartConfig = {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Monthly AQI Comparison: ${city1Data.city} vs ${city2Data.city}`,
                        font: {
                            size: 16
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                let category = '';
                                
                                if (value <= 50) category = '(Good)';
                                else if (value <= 100) category = '(Moderate)';
                                else if (value <= 150) category = '(Unhealthy for Sensitive Groups)';
                                else if (value <= 200) category = '(Unhealthy)';
                                else if (value <= 300) category = '(Very Unhealthy)';
                                else category = '(Hazardous)';
                                
                                return `${context.dataset.label}: ${value} ${category}`;
                            }
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
                        grid: {
                            color: 'rgba(200, 200, 200, 0.2)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Month'
                        },
                        grid: {
                            color: 'rgba(200, 200, 200, 0.2)'
                        }
                    }
                }
            }
        };
        
        // Create the chart
        comparisonChart = new Chart(chartContext, chartConfig);
        
        // Show the city comparison section
        document.querySelector('.chart-container').style.display = 'block';
    }
    
    // Function to create seasonal comparison chart
    function createSeasonalComparisonChart(city1Data, city2Data) {
        const chartContext = document.getElementById('seasonal-comparison-chart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (seasonalComparisonChart) {
            seasonalComparisonChart.destroy();
        }
        
        // Show the seasonal comparison section
        document.getElementById('seasonal-comparison-section').style.display = 'block';
        
        // Prepare chart data
        const chartData = {
            labels: ['Winter', 'Summer', 'Monsoon', 'Post-Monsoon'],
            datasets: [
                {
                    label: city1Data.city,
                    data: [
                        city1Data.seasonal_data.winter,
                        city1Data.seasonal_data.summer,
                        city1Data.seasonal_data.monsoon,
                        city1Data.seasonal_data.post_monsoon
                    ],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderWidth: 2,
                    pointRadius: 5
                },
                {
                    label: city2Data.city,
                    data: [
                        city2Data.seasonal_data.winter,
                        city2Data.seasonal_data.summer,
                        city2Data.seasonal_data.monsoon,
                        city2Data.seasonal_data.post_monsoon
                    ],
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderWidth: 2,
                    pointRadius: 5
                }
            ]
        };
        
        // Chart configuration
        const chartConfig = {
            type: 'radar',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Seasonal AQI Comparison',
                        font: {
                            size: 16
                        }
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            color: 'rgba(200, 200, 200, 0.3)'
                        },
                        grid: {
                            color: 'rgba(200, 200, 200, 0.3)'
                        },
                        pointLabels: {
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        suggestedMin: 0
                    }
                }
            }
        };
        
        // Create the chart
        seasonalComparisonChart = new Chart(chartContext, chartConfig);
    }
    
    // Get AQI category based on value
    function getAQICategory(aqi) {
        if (aqi <= 50) return 'Good';
        if (aqi <= 100) return 'Moderate';
        if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
        if (aqi <= 200) return 'Unhealthy';
        if (aqi <= 300) return 'Very Unhealthy';
        return 'Hazardous';
    }
    
    // Country comparison functionality
    
    // Set up country comparison event listener
    const country1Select = document.getElementById('country1-select');
    const country2Select = document.getElementById('country2-select');
    const compareCountriesButton = document.getElementById('compare-countries-button');
    
    if (compareCountriesButton) {
        compareCountriesButton.addEventListener('click', function() {
            compareCountries();
        });
    }
    
    // Function to toggle country comparison placeholder visibility
    function toggleCountryComparisonPlaceholder(show) {
        const placeholder = document.getElementById('country-comparison-placeholder');
        if (placeholder) {
            placeholder.style.display = show ? 'block' : 'none';
        }
    }
    
    // Function to compare selected countries
    function compareCountries() {
        if (!country1Select || !country2Select) {
            console.error('Country select elements not found');
            return;
        }
        
        const country1 = country1Select.value;
        const country2 = country2Select.value;
        
        if (!country1 || !country2) {
            alert('Please select two countries to compare');
            return;
        }
        
        // Show loading message
        const countryComparisonPlaceholder = document.getElementById('country-comparison-placeholder');
        countryComparisonPlaceholder.innerHTML = `
            <div class="mb-4 text-primary">
                <i class="fas fa-spinner fa-spin fa-4x"></i>
            </div>
            <h4>Loading comparison data...</h4>
            <p class="text-muted">Please wait while we retrieve detailed air quality information from world_most_polluted_countries_.csv.</p>`;
            
        // Fetch data from our country comparison API
        fetch(`/api/country-comparison-data?country1=${encodeURIComponent(country1)}&country2=${encodeURIComponent(country2)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Country comparison data:', data);
                
                // Create the comparison chart
                createCountryComparisonChart(data.country1, data.country2);
                
                // Create the country stats cards
                createCountryStatsCards(data.country1, data.country2);
                
                // Toggle visibility
                toggleCountryComparisonPlaceholder(false);
            })
            .catch(error => {
                console.error('Error in country comparison:', error);
                countryComparisonPlaceholder.innerHTML = `
                    <div class="mb-4 text-danger">
                        <i class="fas fa-exclamation-triangle fa-4x"></i>
                    </div>
                    <h4>Failed to load comparison data</h4>
                    <p class="text-muted">Unable to retrieve air quality data for these countries. Please try again later.</p>
                    <p class="text-muted small">Error: ${error.message}</p>`;
            });
    }
    
    // Function to create country comparison chart
    function createCountryComparisonChart(country1Data, country2Data) {
        const chartContext = document.getElementById('countries-comparison-chart').getContext('2d');
        const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        
        // Destroy existing chart if it exists
        if (countryChart) {
            countryChart.destroy();
        }
        
        // Create chart
        countryChart = new Chart(chartContext, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: country1Data.country,
                        data: country1Data.monthly_data,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderWidth: 2,
                        pointRadius: 4,
                        tension: 0.1
                    },
                    {
                        label: country2Data.country,
                        data: country2Data.monthly_data,
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderWidth: 2,
                        pointRadius: 4,
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Monthly AQI Comparison: ${country1Data.country} vs ${country2Data.country}`,
                        font: {
                            size: 16
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                if (value === null) return `${context.dataset.label}: No data available`;
                                
                                let category = '';
                                
                                if (value <= 50) category = '(Good)';
                                else if (value <= 100) category = '(Moderate)';
                                else if (value <= 150) category = '(Unhealthy for Sensitive Groups)';
                                else if (value <= 200) category = '(Unhealthy)';
                                else if (value <= 300) category = '(Very Unhealthy)';
                                else category = '(Hazardous)';
                                
                                return `${context.dataset.label}: ${value} ${category}`;
                            }
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
                        grid: {
                            color: 'rgba(200, 200, 200, 0.2)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Month'
                        },
                        grid: {
                            color: 'rgba(200, 200, 200, 0.2)'
                        }
                    }
                }
            }
        });
    }
    
    // Function to create country stats cards
    function createCountryStatsCards(country1Data, country2Data) {
        // Add stats cards if needed, similar to city stats cards
        // For now, we'll just focus on the chart visualization
        
        // You could create a dedicated container for country stats and populate it here
        // Example:
        /*
        const countryStatsContainer = document.getElementById('country-stats-comparison');
        if (countryStatsContainer) {
            countryStatsContainer.innerHTML = `
                <div class="country-stats-card">
                    <h4>${country1Data.country}</h4>
                    <p>Average AQI: ${country1Data.avg_aqi}</p>
                    <p>Rank: ${country1Data.rank}</p>
                </div>
                <div class="country-stats-card">
                    <h4>${country2Data.country}</h4>
                    <p>Average AQI: ${country2Data.avg_aqi}</p>
                    <p>Rank: ${country2Data.rank}</p>
                </div>
            `;
        }
        */
    }
    
    // Get color based on AQI value
    function getAQIColor(aqi) {
        if (aqi <= 50) return '#009966'; // Good
        if (aqi <= 100) return '#ffde33'; // Moderate
        if (aqi <= 150) return '#ff9933'; // Unhealthy for Sensitive Groups
        if (aqi <= 200) return '#cc0033'; // Unhealthy
        if (aqi <= 300) return '#660099'; // Very Unhealthy
        return '#7e0023'; // Hazardous
    }
});