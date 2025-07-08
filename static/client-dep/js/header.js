console.log('Header component script loaded');
// Header Component JavaScript
class HeaderComponent {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        console.log('HeaderComponent initialized');
        this.checkAuthStatus();
        console.log('checkAuthStatus called');
        this.setActivePage();
    }

    setupEventListeners() {
        // Hamburger menu
        const hamburger = document.getElementById('hamburger');
        const navMenu = document.getElementById('navMenu');
        
        if (hamburger && navMenu) {
            hamburger.addEventListener('click', () => {
                hamburger.classList.toggle('active');
                navMenu.classList.toggle('active');
                
                // Prevent body scroll when menu is open
                if (navMenu.classList.contains('active')) {
                    document.body.style.overflow = 'hidden';
                } else {
                    document.body.style.overflow = 'auto';
                }
            });
        }

        // User menu dropdown - FIXED
        const userMenuTrigger = document.getElementById('userMenuTrigger');
        const userDropdown = document.getElementById('userDropdown');
        
        if (userMenuTrigger && userDropdown) {
            userMenuTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                userMenuTrigger.classList.toggle('active');
                userDropdown.classList.toggle('show');
            });

            // Close dropdown when clicking outside - FIXED
            document.addEventListener('click', (e) => {
                if (!userMenuTrigger.contains(e.target) && 
                    !userDropdown.contains(e.target) &&
                    userDropdown.classList.contains('show')) {
                    userMenuTrigger.classList.remove('active');
                    userDropdown.classList.remove('show');
                }
            });
        }

        // Close mobile menu when clicking on links
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (navMenu && navMenu.classList.contains('active')) {
                    hamburger.classList.remove('active');
                    navMenu.classList.remove('active');
                    document.body.style.overflow = 'auto';
                }
            });
        });
    }

    async checkAuthStatus() {
        try {
            console.log('Checking authentication status...');
            // First try to check via API
            const response = await fetch('/api/auth/status', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const userData = await response.json();
                if (userData.authenticated && userData.user) {
                    this.setUser(userData.user);
                    return;
                }
            }
            
            // Fallback: check if we have user data passed from the server
            if (window.currentUser) {
                this.setUser(window.currentUser);
                return;
            }
            
            // If no user data found, set as guest
            this.setGuest();
            
        } catch (error) {
            console.log('Auth check failed, checking for server-side user data');
            
            // Fallback: check if we have user data from server
            if (window.currentUser) {
                this.setUser(window.currentUser);
            } else {
                this.setGuest();
            }
        }
    }

    setUser(user) {
        this.currentUser = user;
        
        // Show user menu, hide guest menu
        const userMenuContainer = document.getElementById('userMenuContainer');
        const guestMenuContainers = document.querySelectorAll('.guest-menu-container');
        
        if (userMenuContainer) {
            userMenuContainer.style.display = 'block';
        }
        
        guestMenuContainers.forEach(container => {
            container.style.display = 'none';
        });

        // Update user info in the menu
        this.updateUserInfo(user);
    }

    setGuest() {
        this.currentUser = null;
        
        // Hide user menu, show guest menu
        const userMenuContainer = document.getElementById('userMenuContainer');
        const guestMenuContainers = document.querySelectorAll('.guest-menu-container');
        
        if (userMenuContainer) {
            userMenuContainer.style.display = 'none';
        }
        
        guestMenuContainers.forEach(container => {
            container.style.display = 'block';
        });
    }

    updateUserInfo(user) {
        const userName = document.getElementById('userName');
        const userFullName = document.getElementById('userFullName');
        const userEmail = document.getElementById('userEmail');
        const userAvatar = document.getElementById('userAvatar');
        const userAvatarLarge = document.getElementById('userAvatarLarge');

        if (userName) {
            userName.textContent = user.first_name || user.name || 'Utilisateur';
        }

        if (userFullName) {
            userFullName.textContent = `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.name || 'Utilisateur';
        }

        if (userEmail) {
            userEmail.textContent = user.email || '';
        }

        // Set avatar initials
        const initials = this.getInitials(user.first_name, user.last_name, user.name);
        if (userAvatar) {
            const profilePic = user.profile_picture || "/static/client-dep/images/placeholder.svg";
            userAvatar.innerHTML = `
                <img src="${profilePic}" alt="Photo de profil" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">
            `;
        }
        if (userAvatarLarge) {
            userAvatarLarge.textContent = initials;
        }
    }

    getInitials(firstName, lastName, fullName) {
        if (firstName && lastName) {
            return `${firstName[0]}${lastName[0]}`.toUpperCase();
        } else if (fullName) {
            const names = fullName.split(' ');
            if (names.length >= 2) {
                return `${names[0][0]}${names[1][0]}`.toUpperCase();
            } else {
                return names[0][0].toUpperCase();
            }
        }
        return 'U';
    }

    setActivePage() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link[data-page]');
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            const page = link.getAttribute('data-page');
            
            if (
                (page === 'home' && currentPath === '/') ||
                (page === 'analyze' && currentPath.includes('/analyze')) ||
                (page === 'jobs' && currentPath.includes('/jobs'))
            ) {
                link.classList.add('active');
            }
        });
    }

    async logout() {
        try {
            const response = await fetch('/logout', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Clear any client-side user data
                window.currentUser = null;
                this.setGuest();
                
                // Show success message
                if (window.showToast) {
                    window.showToast('Déconnexion réussie', 'success');
                }
                
                // Redirect to home page after a short delay
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                console.error('Logout failed');
                if (window.showToast) {
                    window.showToast('Erreur lors de la déconnexion', 'error');
                }
            }
        } catch (error) {
            console.error('Logout error:', error);
            if (window.showToast) {
                window.showToast('Erreur lors de la déconnexion', 'error');
            }
        }
    }

    // Method to manually set user (for when user logs in)
    static setCurrentUser(user) {
        if (window.headerComponent) {
            window.headerComponent.setUser(user);
        }
    }

    // Method to manually set guest (for when user logs out)
    static setGuest() {
        if (window.headerComponent) {
            window.headerComponent.setGuest();
        }
    }

    // Static logout method for onclick handlers
    static logout() {
        if (window.headerComponent) {
            window.headerComponent.logout();
        }
    }
}

// Initialize header component when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.headerComponent = new HeaderComponent();
});

// Export for use in other scripts