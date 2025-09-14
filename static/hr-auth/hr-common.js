/**
 * Common HR Authentication and Security Functions
 */

// Check if user is authenticated
function checkAuthentication() {
    const token = localStorage.getItem('hr_access_token');
    if (!token) {
        console.log("❌ HR COMMON: No authentication token found, redirecting to login");
        window.location.replace("/enterprise-login");
        return false;
    }
    
    // Verify token is not expired (basic check)
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const now = Math.floor(Date.now() / 1000);
        if (payload.exp && payload.exp < now) {
            console.log("❌ HR COMMON: Token expired, redirecting to login");
            localStorage.clear();
            window.location.replace("/enterprise-login");
            return false;
        }
    } catch (error) {
        console.log("❌ HR COMMON: Invalid token, redirecting to login");
        localStorage.clear();
        window.location.replace("/enterprise-login");
        return false;
    }
    
    return true;
}

// Prevent back button from showing cached pages
window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        // Page was loaded from cache, check authentication again
        console.log("🔄 HR COMMON: Page loaded from cache, checking authentication");
        if (!checkAuthentication()) {
            return;
        }
    }
});

// Prevent back button navigation after logout
window.addEventListener('popstate', function(event) {
    const token = localStorage.getItem('hr_access_token');
    if (!token) {
        console.log("🚫 HR COMMON: Back button blocked - no authentication");
        window.location.replace("/enterprise-login");
    }
});

// Enhanced logout function
function logout() {
    console.log("🚪 HR COMMON: Déconnexion")
    
    // Clear all authentication data
    localStorage.removeItem('hr_access_token');
    localStorage.removeItem('hr_refresh_token');
    localStorage.removeItem('hr_user');
    
    // Clear session storage as well
    sessionStorage.clear();
    
    // Force reload to clear any cached data
    window.location.replace("/enterprise-login");
}

// Initialize authentication check on page load
document.addEventListener("DOMContentLoaded", function() {
    console.log("🔐 HR COMMON: Initializing authentication check");
    
    // Check authentication first
    if (!checkAuthentication()) {
        return;
    }
    
    console.log("✅ HR COMMON: Authentication successful");
});

// Export functions for use in other scripts
window.hrAuth = {
    checkAuthentication,
    logout
};
