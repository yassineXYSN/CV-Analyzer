
// Vérifier si le paramètre d'URL 'message' est 'email_verified'
        document.addEventListener('DOMContentLoaded', function() {
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('message') === 'email_verified') {
                openPopup();
            }
        });

        function openPopup() {
            const popup = document.getElementById('emailVerifiedPopup');
            popup.classList.add('active');
        }

        function closePopup() {
            const popup = document.getElementById('emailVerifiedPopup');
            popup.classList.remove('active');
        }

        // Fermer la popup en cliquant à l'extérieur
        document.getElementById('emailVerifiedPopup').addEventListener('click', function(e) {
            if (e.target === this) {
                closePopup();
            }
        });

        // Toggle password visibility
        function togglePassword(fieldId) {
            const field = document.getElementById(fieldId);
            const toggle = field.nextElementSibling;
            const icon = toggle.querySelector('i');
            
            if (field.type === 'password') {
                field.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                field.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        }

        // Form submission with detailed logging
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            console.log('🔐 FRONTEND: Début du processus de connexion');
            
            const submitBtn = document.querySelector('.submit-btn');
            const btnContent = document.querySelector('.btn-content');
            const loadingSpinner = document.querySelector('.loading-spinner');
            const errorMessage = document.querySelector('.error-message');
            const successMessage = document.querySelector('.success-message');
            const errorText = document.querySelector('.error-message .message-text');
            const successText = document.querySelector('.success-message .message-text');
            
            // Get form data
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            
            console.log('📧 FRONTEND: Email saisi:', email);
            
            // Validation
            if (!email || !password) {
                console.log('❌ FRONTEND: Validation échouée - champs vides');
                showError('Veuillez remplir tous les champs');
                return;
            }
            
            // Hide messages
            errorMessage.style.display = 'none';
            successMessage.style.display = 'none';
            
            // Show loading state
            btnContent.style.display = 'none';
            loadingSpinner.style.display = 'flex';
            submitBtn.disabled = true;
            
            console.log('📤 FRONTEND: Envoi de la requête à /api/hr-login');
            
            try {
                // Call the API
                const response = await fetch('/api/hr-login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                });
                
                console.log('📥 FRONTEND: Réponse reçue, status:', response.status);
                const result = await response.json();
                console.log('📋 FRONTEND: Résultat:', result);
                
                if (result.success) {
                    console.log('✅ FRONTEND: Connexion réussie');
                    console.log('🎯 FRONTEND: Redirection vers:', result.redirect_url);
                    
                    // Store JWT tokens
                    if (result.access_token && result.refresh_token) {
                        console.log('💾 FRONTEND: Stockage des tokens JWT');
                        localStorage.setItem('hr_access_token', result.access_token);
                        localStorage.setItem('hr_refresh_token', result.refresh_token);
                        if (result.user) {
                            localStorage.setItem('hr_user', JSON.stringify(result.user));
                        }
                    } else {
                        console.warn('⚠️ FRONTEND: Aucun token JWT reçu');
                    }
                    
                    // Success
                    successText.textContent = result.message || 'Connexion réussie ! Redirection en cours...';
                    successMessage.style.display = 'flex';
                    
                    // Redirect after delay
                    setTimeout(() => {
                        console.log('🔄 FRONTEND: Redirection en cours...');
                        window.location.href = result.redirect_url || '/dashboard';
                    }, 1500);
                } else {
                    console.log('❌ FRONTEND: Erreur de connexion:', result.message);
                    // Error from API
                    showError(result.message || 'Erreur de connexion');
                }
                
            } catch (error) {
                console.error('❌ FRONTEND: Erreur réseau:', error);
                showError('Erreur de connexion au serveur. Veuillez réessayer.');
            }
            
            function showError(message) {
                console.log('⚠️ FRONTEND: Affichage erreur:', message);
                errorText.textContent = message;
                errorMessage.style.display = 'flex';
                
                // Reset button state
                btnContent.style.display = 'flex';
                loadingSpinner.style.display = 'none';
                submitBtn.disabled = false;
            }
        });

        // Input focus effects
        document.querySelectorAll('.form-input').forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
            });
            
            // Real-time validation
            input.addEventListener('input', function() {
                if (this.validity.valid) {
                    this.parentElement.classList.remove('error');
                } else {
                    this.parentElement.classList.add('error');
                }
            });
        });

        // Auto-focus on first input
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🎯 FRONTEND: Page chargée, focus sur email');
            document.getElementById('email').focus();
        });

        // Handle Enter key in password field
        document.getElementById('password').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('loginForm').dispatchEvent(new Event('submit'));
            }
        });

        // Social login handlers (placeholder)
        document.querySelectorAll('.social-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const provider = this.classList.contains('google-btn') ? 'Google' : 
                               this.classList.contains('microsoft-btn') ? 'Microsoft' : 'LinkedIn';
                alert(`Connexion ${provider} - Fonctionnalité à venir`);
            });
        });
   