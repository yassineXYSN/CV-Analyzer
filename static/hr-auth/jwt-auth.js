/**
 * JWT Authentication Utility for HR Dashboard
 */
class JWTAuth {
    constructor() {
        this.accessTokenKey = 'hr_access_token';
        this.refreshTokenKey = 'hr_refresh_token';
        this.userKey = 'hr_user';
    }

    /**
     * Store tokens after successful login
     */
    storeTokens(accessToken, refreshToken, user = null) {
        localStorage.setItem(this.accessTokenKey, accessToken);
        localStorage.setItem(this.refreshTokenKey, refreshToken);
        if (user) {
            localStorage.setItem(this.userKey, JSON.stringify(user));
        }
    }

    /**
     * Get access token
     */
    getAccessToken() {
        return localStorage.getItem(this.accessTokenKey);
    }

    /**
     * Get refresh token
     */
    getRefreshToken() {
        return localStorage.getItem(this.refreshTokenKey);
    }

    /**
     * Get stored user data
     */
    getUser() {
        const userData = localStorage.getItem(this.userKey);
        return userData ? JSON.parse(userData) : null;
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.getAccessToken();
    }

    /**
     * Clear all stored authentication data
     */
    clearAuth() {
        localStorage.removeItem(this.accessTokenKey);
        localStorage.removeItem(this.refreshTokenKey);
        localStorage.removeItem(this.userKey);
    }

    /**
     * Get authorization header
     */
    getAuthHeader() {
        const token = this.getAccessToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    /**
     * Make authenticated API request
     */
    async apiRequest(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...this.getAuthHeader(),
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            // If token expired, try to refresh
            if (response.status === 401) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Retry the request with new token
                    const newHeaders = {
                        ...headers,
                        ...this.getAuthHeader()
                    };
                    return await fetch(url, {
                        ...options,
                        headers: newHeaders
                    });
                } else {
                    // Refresh failed, redirect to login
                    this.redirectToLogin();
                    return null;
                }
            }

            return response;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    /**
     * Refresh access token
     */
    async refreshToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            return false;
        }

        try {
            const response = await fetch('/api/hr-refresh-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem(this.accessTokenKey, data.access_token);
                return true;
            } else {
                this.clearAuth();
                return false;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            this.clearAuth();
            return false;
        }
    }

    /**
     * Login with email and password
     */
    async login(email, password) {
        try {
            const response = await fetch('/api/hr-login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (data.success && data.access_token) {
                this.storeTokens(data.access_token, data.refresh_token, data.user);
                return data;
            } else {
                throw new Error(data.message || 'Login failed');
            }
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    }

    /**
     * Logout
     */
    async logout() {
        try {
            // Call logout endpoint if token exists
            if (this.isAuthenticated()) {
                await this.apiRequest('/api/hr-logout', { method: 'POST' });
            }
        } catch (error) {
            console.error('Logout API call failed:', error);
        } finally {
            // Always clear local storage
            this.clearAuth();
            this.redirectToLogin();
        }
    }

    /**
     * Get current user profile
     */
    async getCurrentUser() {
        try {
            const response = await this.apiRequest('/api/hr-me');
            if (response && response.ok) {
                const userData = await response.json();
                localStorage.setItem(this.userKey, JSON.stringify(userData));
                return userData;
            }
            return null;
        } catch (error) {
            console.error('Failed to get current user:', error);
            return null;
        }
    }

    /**
     * Redirect to login page
     */
    redirectToLogin() {
        if (!window.location.pathname.includes('/hr-login')) {
            window.location.href = '/hr-login';
        }
    }

    /**
     * Check authentication and redirect if needed
     */
    requireAuth() {
        if (!this.isAuthenticated()) {
            this.redirectToLogin();
            return false;
        }
        return true;
    }

    /**
     * Initialize authentication check
     */
    init() {
        // Check if we're on a protected page
        const protectedPaths = ['/dashboard', '/company-setup', '/job-details', '/employee-profile'];
        const currentPath = window.location.pathname;
        
        if (protectedPaths.some(path => currentPath.includes(path))) {
            this.requireAuth();
        }

        // Auto-refresh token every 25 minutes (before 30min expiry)
        setInterval(() => {
            if (this.isAuthenticated()) {
                this.refreshToken();
            }
        }, 25 * 60 * 1000);
    }
}

// Create global instance
const jwtAuth = new JWTAuth();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    jwtAuth.init();
});

// Export for use in other scripts
window.jwtAuth = jwtAuth;

