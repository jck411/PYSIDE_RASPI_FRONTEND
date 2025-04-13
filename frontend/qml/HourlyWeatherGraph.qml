import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

// Hourly Weather Graph Component
Item {
    id: hourlyWeatherGraph
    width: parent.width
    implicitHeight: 300  // Default height that can be adjusted by parent
    
    // --- Properties ---
    property var hourlyForecastData: null  // Expects forecast_hourly data 
    property bool loading: false
    property string sunriseTime: null  // ISO time string for sunrise
    property string sunsetTime: null   // ISO time string for sunset
    
    // Timer to update current time position
    Timer {
        id: currentTimeUpdateTimer
        interval: 60000 // Update every minute
        running: visible
        repeat: true
        onTriggered: {
            tempCanvas.requestPaint();
        }
    }
    
    // --- Functions ---
    // Format time display (e.g. "3 PM")
    function formatHourlyTime(timeString) {
        try {
            // Handle potential time format variations
            var date;
            
            // If the string includes 'T' and ends with 'Z', it's likely an ISO string
            if (typeof timeString === 'string') {
                // Replace 'Z' with +00:00 for better cross-platform compatibility
                var normalizedTimeString = timeString.replace('Z', '+00:00');
                date = new Date(normalizedTimeString);
            } else {
                date = new Date(timeString);
            }
            
            // Check if date is valid
            if (isNaN(date.getTime())) {
                console.error("Invalid date:", timeString);
                return "N/A";
            }
            
            return date.toLocaleTimeString([], {hour: 'numeric', minute:'2-digit', hour12: true});
        } catch (e) {
            console.error("Error formatting time:", e, timeString);
            return "N/A";
        }
    }
    
    // Get hours since midnight
    function getHoursSinceMidnight(timeString) {
        try {
            // Handle potential time format variations
            var date;
            
            // If the string includes 'T' and ends with 'Z', it's likely an ISO string
            if (typeof timeString === 'string') {
                // Replace 'Z' with +00:00 for better cross-platform compatibility
                var normalizedTimeString = timeString.replace('Z', '+00:00');
                date = new Date(normalizedTimeString);
            } else {
                date = new Date(timeString);
            }
            
            // Check if date is valid
            if (isNaN(date.getTime())) {
                console.error("Invalid date for hours calculation:", timeString);
                return 0;
            }
            
            // Convert to local time
            return date.getHours() + (date.getMinutes() / 60);
        } catch (e) {
            console.error("Error calculating hours since midnight:", e, timeString);
            return 0;
        }
    }
    
    // Convert ISO time string to Unix timestamp (seconds since epoch)
    function isoStringToTimestamp(isoString) {
        if (!isoString) return 0;
        var date = new Date(isoString);
        return Math.floor(date.getTime() / 1000);
    }
    
    // Find maximum and minimum temperature in forecast data
    function findTemperatureRange() {
        if (!hourlyForecastData || !hourlyForecastData.properties || !hourlyForecastData.properties.periods) {
            return { min: 0, max: 100 };
        }
        
        var periods = hourlyForecastData.properties.periods;
        var min = 200;  // Start with unreasonably high value
        var max = -200; // Start with unreasonably low value
        
        // Look at first 24 periods (hours)
        var count = Math.min(periods.length, 24);
        for (var i = 0; i < count; i++) {
            var temp = periods[i].temperature;
            if (temp < min) min = temp;
            if (temp > max) max = temp;
        }
        
        // Add padding to range
        min = Math.floor(min - 5);
        max = Math.ceil(max + 5);
        
        return { min: min, max: max };
    }
    
    // Find height position for a temperature value
    function getYPosition(temp, minTemp, maxTemp, graphHeight) {
        // Convert temperature to y-position (higher temp = lower y value)
        var range = maxTemp - minTemp;
        if (range === 0) range = 1;  // Prevent division by zero
        
        // Calculate percentage of range, then map to graph height
        var percentage = 1 - ((temp - minTemp) / range);
        return percentage * (graphHeight - 30) + 15; // 15px padding top/bottom
    }
    
    // Get x-position for a time
    function getTimeXPosition(timeString, width) {
        try {
            // Get hours since midnight (0-24)
            var hoursSinceMidnight = getHoursSinceMidnight(timeString);
            
            // Get the start hour of the first period to determine the time offset
            var startHour = 0;
            if (hourlyForecastData && hourlyForecastData.properties && hourlyForecastData.properties.periods && hourlyForecastData.properties.periods.length > 0) {
                var firstPeriodTime = new Date(hourlyForecastData.properties.periods[0].startTime);
                
                // Check if date is valid
                if (!isNaN(firstPeriodTime.getTime())) {
                    startHour = firstPeriodTime.getHours();
                }
            }
            
            // Calculate the position based on the 24-hour range displayed in the graph
            // Adjust the position to align with the graph's time scale
            var relativeHour = (hoursSinceMidnight - startHour + 24) % 24;
            var position = relativeHour / 24 * width;
            
            // Make sure the position is within the bounds of the graph
            return Math.max(0, Math.min(position, width));
        } catch (e) {
            console.error("Error calculating time position:", e, timeString);
            return 0;
        }
    }
    
    // --- UI ---
    Rectangle {
        id: graphContainer
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.1)
        radius: 10
        
        // Loading indicator
        BusyIndicator {
            anchors.centerIn: parent
            running: loading
            visible: loading
        }
        
        // Error message when data is missing
        Text {
            anchors.centerIn: parent
            text: "Hourly forecast data not available"
            visible: !loading && (!hourlyForecastData || !hourlyForecastData.properties || !hourlyForecastData.properties.periods)
            color: ThemeManager.text_secondary_color
            font.pixelSize: 16
        }
        
        // Graph title
        Item {
            id: titleArea
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 40
            
            Text {
                anchors.centerIn: parent
                text: "24-Hour Temperature & Precipitation Forecast"
                color: ThemeManager.text_primary_color
                font.pixelSize: 16
                font.bold: true
            }
        }
        
        // Graph area
        Item {
            id: graphArea
            anchors.top: titleArea.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 10
            visible: !loading && hourlyForecastData && hourlyForecastData.properties && hourlyForecastData.properties.periods
            
            // Temperature graph (will be drawn on Canvas)
            Canvas {
                id: tempCanvas
                anchors.fill: parent
                
                onPaint: {
                    // Validate data is available
                    if (!hourlyForecastData || !hourlyForecastData.properties || !hourlyForecastData.properties.periods) {
                        return;
                    }
                    
                    var ctx = getContext("2d");
                    var periods = hourlyForecastData.properties.periods;
                    var tempRange = findTemperatureRange();
                    
                    // Clear canvas
                    ctx.clearRect(0, 0, width, height);
                    
                    // Calculate width per hour
                    var hourWidth = width / 24;
                    
                    // Draw sunrise if available
                    if (sunriseTime) {
                        try {
                            var sunriseX = getTimeXPosition(sunriseTime, width);
                            
                            // Draw very faint sunrise line
                            ctx.beginPath();
                            ctx.setLineDash([5, 3]); // Dashed line
                            ctx.lineWidth = 1; // Thinner line
                            // Very faint color
                            ctx.strokeStyle = ThemeManager.isDarkTheme ? 
                                "rgba(255, 215, 0, 0.25)" : // Faint gold
                                "rgba(255, 140, 0, 0.25)"; // Faint orange
                            ctx.moveTo(sunriseX, 70); // Start below sun icon
                            ctx.lineTo(sunriseX, height - 30); // End above time labels
                            ctx.stroke();
                            ctx.setLineDash([]); // Reset to solid line
                            
                            // Draw sunrise label
                            ctx.fillStyle = ThemeManager.isDarkTheme ? "#ffd700" : "#ff8c00";
                            ctx.font = "12px sans-serif";
                            ctx.textAlign = "center";
                            ctx.fillText("Sunrise", sunriseX, 15);
                            
                            // Draw sunrise time
                            ctx.font = "10px sans-serif";
                            ctx.fillText(formatHourlyTime(sunriseTime), sunriseX, 30);
                            
                            // Draw sun icon
                            ctx.beginPath();
                            ctx.arc(sunriseX, 50, 8, 0, 2 * Math.PI);
                            ctx.fillStyle = ThemeManager.isDarkTheme ? "#ffd700" : "#ff8c00";
                            ctx.fill();
                            
                            // Draw rays
                            var rayLength = 5;
                            ctx.beginPath();
                            ctx.lineWidth = 1.5;
                            ctx.strokeStyle = ThemeManager.isDarkTheme ? "#ffd700" : "#ff8c00";
                            
                            // 8 evenly spaced rays
                            for (var i = 0; i < 8; i++) {
                                var angle = i * Math.PI / 4;
                                var startX = sunriseX + Math.cos(angle) * 8;
                                var startY = 50 + Math.sin(angle) * 8;
                                var endX = sunriseX + Math.cos(angle) * (8 + rayLength);
                                var endY = 50 + Math.sin(angle) * (8 + rayLength);
                                
                                ctx.moveTo(startX, startY);
                                ctx.lineTo(endX, endY);
                            }
                            ctx.stroke();
                        } catch (e) {
                            console.error("Error drawing sunrise:", e);
                        }
                    }
                    
                    // Draw sunset if available
                    if (sunsetTime) {
                        try {
                            var sunsetX = getTimeXPosition(sunsetTime, width);
                            
                            // Draw very faint sunset line
                            ctx.beginPath();
                            ctx.setLineDash([5, 3]); // Dashed line
                            ctx.lineWidth = 1; // Thinner line
                            // Very faint color
                            ctx.strokeStyle = ThemeManager.isDarkTheme ? 
                                "rgba(250, 128, 114, 0.25)" : // Faint salmon
                                "rgba(255, 99, 71, 0.25)"; // Faint tomato
                            ctx.moveTo(sunsetX, 60); // Start below sun icon
                            ctx.lineTo(sunsetX, height - 30); // End above time labels
                            ctx.stroke();
                            ctx.setLineDash([]); // Reset to solid line
                            
                            // Draw sunset label
                            ctx.fillStyle = ThemeManager.isDarkTheme ? "#fa8072" : "#ff6347";
                            ctx.font = "12px sans-serif";
                            ctx.textAlign = "center";
                            ctx.fillText("Sunset", sunsetX, 15);
                            
                            // Draw sunset time
                            ctx.font = "10px sans-serif";
                            ctx.fillText(formatHourlyTime(sunsetTime), sunsetX, 30);
                            
                            // Draw half-sun icon
                            ctx.beginPath();
                            ctx.arc(sunsetX, 50, 8, 0, Math.PI, true);
                            ctx.fillStyle = ThemeManager.isDarkTheme ? "#fa8072" : "#ff6347";
                            ctx.fill();
                            
                            // Draw a line for the horizon
                            ctx.beginPath();
                            ctx.moveTo(sunsetX - 8, 50);
                            ctx.lineTo(sunsetX + 8, 50);
                            ctx.lineWidth = 1.5;
                            ctx.strokeStyle = ThemeManager.isDarkTheme ? "#fa8072" : "#ff6347";
                            ctx.stroke();
                        } catch (e) {
                            console.error("Error drawing sunset:", e);
                        }
                    }
                    
                    // Store the current hour for time label bolding - we'll calculate once here
                    // rather than in each repeater item
                    var now = new Date();
                    var currentHour = now.getHours();
                    var currentMinutes = now.getMinutes();
                    
                    // --- Temperature line ---
                    ctx.beginPath();
                    ctx.setLineDash([]); // Solid line
                    ctx.lineWidth = 3;
                    ctx.strokeStyle = ThemeManager.isDarkTheme ? "#ff9966" : "#ff5e13"; // Orange color
                    
                    var tempRangeSize = tempRange.max - tempRange.min;
                    var graphHeight = height - 100; // Reserve space for time labels and rain bars
                    var graphStartY = 70; // Starting Y position for the temperature graph
                    
                    // Map temperature to Y position (reversed, as higher temp should be higher on graph)
                    function tempToY(temp) {
                        return graphStartY + graphHeight - ((temp - tempRange.min) / tempRangeSize * graphHeight);
                    }
                    
                    // Reset to solid line for temperature plot
                    ctx.setLineDash([]);
                    ctx.lineWidth = 3;
                    ctx.strokeStyle = ThemeManager.isDarkTheme ? "#ff9966" : "#ff5e13";
                    
                    // Draw temperature line
                    var count = Math.min(periods.length, 24);
                    for (var i = 0; i < count; i++) {
                        var x = i * hourWidth + (hourWidth / 2); // Center point of each hour
                        var y = tempToY(periods[i].temperature);
                        
                        if (i === 0) {
                            ctx.moveTo(x, y);
                        } else {
                            ctx.lineTo(x, y);
                        }
                        
                        // Draw temperature value (only on even indices to reduce clutter)
                        if (i % 2 === 0) {
                            ctx.fillStyle = ThemeManager.text_primary_color;
                            ctx.font = "bold 12px sans-serif";
                            ctx.textAlign = "center";
                            ctx.fillText(periods[i].temperature + "°", x, y - 10);
                        }
                    }
                    
                    // Stroke the temperature line
                    ctx.stroke();
                    
                    // --- Draw rain probability bars ---
                    // First, find the maximum probability to scale the bars appropriately
                    var maxProb = 0;
                    for (var i = 0; i < count; i++) {
                        if (periods[i].probabilityOfPrecipitation && 
                            periods[i].probabilityOfPrecipitation.value !== null) {
                            var prob = periods[i].probabilityOfPrecipitation.value;
                            if (prob > maxProb) maxProb = prob;
                        }
                    }
                    
                    // Only draw if we have probability data
                    if (maxProb > 0) {
                        var barHeight = 60; // Height for 100% probability
                        var barY = height - barHeight - 30; // Position higher above time labels
                        
                        // Draw each probability bar
                        for (var i = 0; i < count; i++) {
                            var x = i * hourWidth;
                            var prob = 0;
                            
                            if (periods[i].probabilityOfPrecipitation && 
                                periods[i].probabilityOfPrecipitation.value !== null) {
                                prob = periods[i].probabilityOfPrecipitation.value;
                            }
                            
                            if (prob > 0) {
                                var barHeightScaled = (prob / 100) * barHeight;
                                
                                // Draw bar background for better visibility
                                ctx.fillStyle = "rgba(0, 0, 0, 0.3)"; // Darker background
                                ctx.fillRect(x + 2, barY, hourWidth - 4, barHeight);
                                
                                // Draw the actual probability bar with darker blue
                                var blueValue = Math.max(50, 150 - (prob * 2)); // Much darker blue
                                ctx.fillStyle = "rgba(0, " + blueValue + ", 220, 1.0)"; // Full opacity
                                ctx.fillRect(
                                    x + 2, 
                                    barY + barHeight - barHeightScaled, 
                                    hourWidth - 4, 
                                    barHeightScaled
                                );
                                
                                // Add probability text for all probabilities
                                if (hourWidth > 20) {
                                    // Position for text
                                    var textX = x + (hourWidth / 2);
                                    var textY = barY + (barHeight / 2);
                                    
                                    // Different text styling based on theme
                                    if (ThemeManager.isDarkTheme) {
                                        // Draw text outline in dark mode for better contrast
                                        ctx.lineWidth = 3;
                                        ctx.strokeStyle = "rgba(0, 0, 0, 0.7)";
                                        ctx.font = "bold 10px sans-serif";
                                        ctx.textAlign = "center";
                                        ctx.strokeText(Math.round(prob) + "%", textX, textY);
                                        
                                        // Draw text fill
                                        ctx.fillStyle = "white";
                                        ctx.fillText(Math.round(prob) + "%", textX, textY);
                                    } else {
                                        // Simpler text in light mode
                                        ctx.font = "bold 10px sans-serif";
                                        ctx.textAlign = "center";
                                        ctx.fillStyle = "white";
                                        ctx.fillText(Math.round(prob) + "%", textX, textY);
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // Time labels
            Row {
                id: timeLabelsRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 20
                
                // Store the current time information as properties for the repeater
                property int currentHour: {
                    var now = new Date();
                    return now.getHours();
                }
                property int currentMinutes: {
                    var now = new Date();
                    return now.getMinutes();
                }
                
                Repeater {
                    model: hourlyForecastData && hourlyForecastData.properties && hourlyForecastData.properties.periods ? 
                           Math.min(hourlyForecastData.properties.periods.length, 24) : 0
                    
                    Item {
                        width: parent.width / 24
                        height: parent.height
                        
                        // Check if this time is the current hour
                        property bool isCurrentHour: {
                            if (hourlyForecastData && hourlyForecastData.properties && 
                                hourlyForecastData.properties.periods && index < hourlyForecastData.properties.periods.length) {
                                
                                var periodDate = new Date(hourlyForecastData.properties.periods[index].startTime);
                                // If it's a valid date
                                if (!isNaN(periodDate.getTime())) {
                                    var periodHour = periodDate.getHours();
                                    
                                    // Check if it's the current hour
                                    if (periodHour === timeLabelsRow.currentHour) {
                                        return true;
                                    }
                                    
                                    // If we're within the last 15 minutes of the previous hour, 
                                    // also highlight the next hour (transition period)
                                    if (periodHour === (timeLabelsRow.currentHour + 1) % 24 && 
                                        timeLabelsRow.currentMinutes >= 45) {
                                        return true;
                                    }
                                }
                            }
                            return false;
                        }
                        
                        Text {
                            anchors.centerIn: parent
                            text: formatHourlyTime(hourlyForecastData.properties.periods[index].startTime)
                            color: ThemeManager.text_secondary_color
                            font.pixelSize: 10
                            font.bold: isCurrentHour  // Bold if this is the current hour
                            font.pointSize: isCurrentHour ? 12 : 10  // Slightly larger if current hour
                            rotation: 45  // Rotate labels to avoid overlap
                            transformOrigin: Item.Center
                        }
                    }
                }
            }
        }
    }
    
    // Start the timer when component completes
    Component.onCompleted: {
        currentTimeUpdateTimer.start();
        tempCanvas.requestPaint();
    }
    
    // Update the graph when data changes
    onHourlyForecastDataChanged: {
        tempCanvas.requestPaint();
    }
    
    // Force update when visibility changes
    onVisibleChanged: {
        if (visible) {
            tempCanvas.requestPaint();
        }
    }
} 