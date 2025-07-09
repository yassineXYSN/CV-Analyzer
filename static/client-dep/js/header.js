// Header Component JavaScript
class HeaderComponent {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    init() {
        this.checkAuthStatus();
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
            const closeDropdown = () => {
                userMenuTrigger.classList.remove('active');
                userDropdown.classList.remove('show');
            };

            userMenuTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                const isOpen = userDropdown.classList.contains('show');

                // Close others if needed
                document.querySelectorAll('.user-dropdown.show').forEach(d => d.classList.remove('show'));
                document.querySelectorAll('.user-menu-trigger.active').forEach(t => t.classList.remove('active'));

                if (!isOpen) {
                    userMenuTrigger.classList.add('active');
                    userDropdown.classList.add('show');
                }
            });

            // Close on outside click
            document.addEventListener('click', (e) => {
                if (!userMenuTrigger.contains(e.target) && !userDropdown.contains(e.target)) {
                    closeDropdown();
                }
            });

            // Close on Esc
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') closeDropdown();
            });
        }
    }

    async checkAuthStatus() {
        this.currentUser = {
        id: 1,
        email: 'johndoe@example.com',
        first_name: 'John',
        last_name: 'Doe',
        google_id: null,
        profile_picture: '', // Or provide a real URL
        is_active: 1,
        is_verified: 1,
        profile: null
    };
    this.setUser(this.currentUser);
        try {
            // First try to check via API
            const response = await fetch('/api/auth/status', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const userData = await response.json();
                if (userData.authenticated && userData.user) {
                    this.setUser(userData.user);
                    console.log('User authenticated via API:', userData.user);
                    if (userData.user.profile === null) {
                        console.log('entering step2');
                        const step2Item = document.getElementById("setupstep2");
                        if (step2Item) {
                            step2Item.style.display = "block";
                        }
                    }
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
        

        const userMenuContainer = document.getElementById('userMenuContainer');
        const guestMenuContainers = document.querySelectorAll('.guest-menu-container');

        if (userMenuContainer) {
            userMenuContainer.style.display = 'block';
        }

        guestMenuContainers.forEach(container => {
            container.style.display = 'none';
        });

        this.updateUserInfo(user);
        this.setupEventListeners();

        // ✅ Set profile link dynamically
        const profileLink = document.getElementById('profileLink');
        if (profileLink && user.id) {
            profileLink.href = `/profile/by_user/${user.id}`;
        }
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
                (page === 'jobs' && currentPath.includes('/jobs')) ||
                (page === 'step2' && currentPath.includes('/signup/step2'))
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