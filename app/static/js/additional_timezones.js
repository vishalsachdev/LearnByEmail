/**
 * Additional timezone data for improved timezone detection
 * 
 * This contains a more comprehensive mapping of timezones that 
 * can be detected by browsers to our simplified dropdown options.
 */

// More comprehensive timezone mappings 
const timezoneMapping = {
    // North America
    'America/New_York': 'America/New_York',
    'America/Detroit': 'America/New_York',
    'America/Toronto': 'America/New_York',
    'America/Montreal': 'America/New_York',
    'America/Indiana': 'America/New_York',
    'US/Eastern': 'America/New_York',
    
    'America/Chicago': 'America/Chicago',
    'America/Winnipeg': 'America/Chicago',
    'America/Mexico_City': 'America/Chicago',
    'US/Central': 'America/Chicago',
    
    'America/Denver': 'America/Denver',
    'America/Phoenix': 'America/Denver',
    'America/Edmonton': 'America/Denver',
    'US/Mountain': 'America/Denver',
    
    'America/Los_Angeles': 'America/Los_Angeles',
    'America/Vancouver': 'America/Los_Angeles',
    'US/Pacific': 'America/Los_Angeles',
    
    'America/Anchorage': 'America/Anchorage',
    'US/Alaska': 'America/Anchorage',
    
    'Pacific/Honolulu': 'Pacific/Honolulu',
    'US/Hawaii': 'Pacific/Honolulu',
    
    // Europe
    'Europe/London': 'Europe/London',
    'Europe/Dublin': 'Europe/London',
    'Europe/Lisbon': 'Europe/London',
    'GMT': 'Europe/London',
    'UTC': 'Europe/London',
    
    'Europe/Paris': 'Europe/Paris',
    'Europe/Berlin': 'Europe/Paris',
    'Europe/Madrid': 'Europe/Paris',
    'Europe/Rome': 'Europe/Paris',
    'Europe/Amsterdam': 'Europe/Paris',
    'Europe/Brussels': 'Europe/Paris',
    'Europe/Vienna': 'Europe/Paris',
    'Europe/Warsaw': 'Europe/Paris',
    'Europe/Prague': 'Europe/Paris',
    'Europe/Copenhagen': 'Europe/Paris',
    'Europe/Stockholm': 'Europe/Paris',
    'Europe/Budapest': 'Europe/Paris',
    'Europe/Zurich': 'Europe/Paris',
    
    // Asia
    'Asia/Tokyo': 'Asia/Tokyo',
    'Asia/Seoul': 'Asia/Tokyo',
    'Asia/Shanghai': 'Asia/Tokyo',
    'Asia/Hong_Kong': 'Asia/Tokyo',
    'Asia/Taipei': 'Asia/Tokyo',
    'Asia/Singapore': 'Asia/Tokyo',
    'Asia/Manila': 'Asia/Tokyo',
    'Japan': 'Asia/Tokyo',
    
    // Australia
    'Australia/Sydney': 'Australia/Sydney',
    'Australia/Melbourne': 'Australia/Sydney',
    'Australia/Brisbane': 'Australia/Sydney',
    'Australia/Adelaide': 'Australia/Sydney',
    'Australia/Perth': 'Australia/Sydney'
};