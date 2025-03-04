/**
 * Timezone Detection Script for LearningPulse
 * 
 * This script detects the user's timezone and pre-selects it in the subscription form,
 * improving the user experience by eliminating the need to manually select a timezone.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Function to detect the user's timezone
    function detectUserTimezone() {
        try {
            // Using Intl API to get local timezone
            return Intl.DateTimeFormat().resolvedOptions().timeZone;
        } catch (error) {
            console.warn('Timezone detection failed:', error);
            return null;
        }
    }

    // Function to map detected timezone to closest match in our dropdown
    function findClosestTimezone(detectedZone, availableZones) {
        // Check if we have the comprehensive timezone mapping available
        if (typeof timezoneMapping !== 'undefined') {
            // If the detected zone is in our mapping, use the mapped value
            if (detectedZone in timezoneMapping) {
                const mappedZone = timezoneMapping[detectedZone];
                if (availableZones.includes(mappedZone)) {
                    console.log('Found mapped timezone:', detectedZone, '->', mappedZone);
                    return mappedZone;
                }
            }
        }
        
        // If we have an exact match in available zones, use it
        if (availableZones.includes(detectedZone)) {
            return detectedZone;
        }

        // Common timezone region mappings as fallback
        const regionMappings = {
            'America/': ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles', 'America/Anchorage', 'Pacific/Honolulu'],
            'Europe/': ['Europe/London', 'Europe/Paris'],
            'Asia/': ['Asia/Tokyo'],
            'Australia/': ['Australia/Sydney'],
            'Pacific/': ['Pacific/Honolulu']
        };

        // Try to find a zone in the same region
        for (const [region, zones] of Object.entries(regionMappings)) {
            if (detectedZone.startsWith(region)) {
                // Find the first available zone in this region
                for (const zone of zones) {
                    if (availableZones.includes(zone)) {
                        console.log('Found regional timezone match:', detectedZone, '->', zone);
                        return zone;
                    }
                }
            }
        }

        // Default to Eastern Time if no match
        console.log('No timezone match found, using default:', 'America/New_York');
        return 'America/New_York';
    }

    // Apply timezone selection to the form
    function applyTimezoneSelection(timezone) {
        const timezoneSelect = document.getElementById('timezone');
        if (!timezoneSelect) return;

        // Get all available timezone options
        const availableTimezones = Array.from(timezoneSelect.options).map(option => option.value);
        
        // Find the closest matching timezone
        const closestMatch = findClosestTimezone(timezone, availableTimezones);
        
        // Set the select value
        timezoneSelect.value = closestMatch;
        
        // Add visual indicator that this was auto-detected
        const timezoneLabel = document.querySelector('label[for="timezone"]');
        if (timezoneLabel) {
            const detectedBadge = document.createElement('span');
            detectedBadge.className = 'badge bg-info ms-2 timezone-detected-badge';
            detectedBadge.textContent = 'Auto-detected';
            detectedBadge.style.fontSize = '0.7rem';
            
            // Only add the badge if it doesn't already exist
            if (!timezoneLabel.querySelector('.timezone-detected-badge')) {
                timezoneLabel.appendChild(detectedBadge);
            }
        }
        
        // Set the preferred time input to a reasonable default time (if it's a new subscription)
        const preferredTimeInput = document.getElementById('preferred_time');
        if (preferredTimeInput && !preferredTimeInput.value) {
            // Get the current time in the local timezone
            const now = new Date();
            
            // Set to current time + 2 minutes
            now.setMinutes(now.getMinutes() + 2);
            
            // Extract hours and minutes
            const hours = now.getHours();
            const minutes = now.getMinutes();
            
            // Format as HH:MM
            const suggestedTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
            preferredTimeInput.value = suggestedTime;
            
            // Add a small indicator for this auto-filled time
            const timeLabel = document.querySelector('label[for="preferred_time"]');
            if (timeLabel && !timeLabel.querySelector('.time-suggested-badge')) {
                const suggestedBadge = document.createElement('span');
                suggestedBadge.className = 'badge bg-secondary ms-2 time-suggested-badge';
                suggestedBadge.textContent = 'Suggested';
                suggestedBadge.style.fontSize = '0.7rem';
                timeLabel.appendChild(suggestedBadge);
            }
        }
    }

    // Main function to detect and apply timezone
    function initTimezoneDetection() {
        const detectedTimezone = detectUserTimezone();
        if (detectedTimezone) {
            applyTimezoneSelection(detectedTimezone);
            
            // Store in session storage for use in other forms
            sessionStorage.setItem('detectedTimezone', detectedTimezone);
        }
    }

    // Initialize timezone detection
    initTimezoneDetection();
});