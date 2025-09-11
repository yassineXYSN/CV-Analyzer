
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

        // Login type switching
        function switchLoginType(type) {
            const hrForm = document.getElementById('hrLoginForm');
            const superAdminForm = document.getElementById('superAdminLoginForm');
            
            // Internal buttons (both forms have the same IDs)
            const hrBtnInternal = document.getElementById('hrLoginBtnInternal');
            const superAdminBtnInternal = document.getElementById('superAdminLoginBtnInternal');
            
            if (type === 'hr') {
                hrForm.style.display = 'block';
                superAdminForm.style.display = 'none';
                
                // Update internal buttons
                if (hrBtnInternal) {
                    hrBtnInternal.classList.add('active');
                    superAdminBtnInternal.classList.remove('active');
                }
                
                // Update body class for HR theme
                document.body.classList.remove('super-admin-theme');
                document.body.classList.add('hr-theme');
            } else if (type === 'super_admin') {
                hrForm.style.display = 'none';
                superAdminForm.style.display = 'block';
                
                // Update internal buttons
                if (hrBtnInternal) {
                    hrBtnInternal.classList.remove('active');
                    superAdminBtnInternal.classList.add('active');
                }
                
                // Update body class for Super Admin theme
                document.body.classList.remove('hr-theme');
                document.body.classList.add('super-admin-theme');
            }
        }

        // HR Form submission with detailed logging
        document.getElementById('hrLoginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            console.log('🔐 FRONTEND: Début du processus de connexion');
            
            const submitBtn = document.querySelector('#hrLoginForm .submit-btn');
            const btnContent = document.querySelector('#hrLoginForm .btn-content');
            const loadingSpinner = document.querySelector('#hrLoginForm .loading-spinner');
            const errorMessage = document.querySelector('#hrLoginForm .error-message');
            const successMessage = document.querySelector('#hrLoginForm .success-message');
            const errorText = document.querySelector('#hrLoginForm .error-message .message-text');
            const successText = document.querySelector('#hrLoginForm .success-message .message-text');
            
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

        // Auto-focus on first input and set default theme
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🎯 FRONTEND: Page chargée, focus sur email');
            
            // Set default HR theme
            document.body.classList.add('hr-theme');
            
            document.getElementById('email').focus();
        });

        // Handle Enter key in password field
        document.getElementById('password').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('loginForm').dispatchEvent(new Event('submit'));
            }
        });

        // Super Admin Form submission
        document.getElementById('superAdminLoginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            console.log('👑 FRONTEND: Début du processus de connexion Super Admin');
            
            const submitBtn = document.querySelector('#superAdminLoginForm .submit-btn');
            const btnContent = document.querySelector('#superAdminLoginForm .btn-content');
            const loadingSpinner = document.querySelector('#superAdminLoginForm .loading-spinner');
            const errorMessage = document.querySelector('#superAdminLoginForm .error-message');
            const successMessage = document.querySelector('#superAdminLoginForm .success-message');
            const errorText = document.querySelector('#superAdminLoginForm .error-message .message-text');
            const successText = document.querySelector('#superAdminLoginForm .success-message .message-text');
            
            // Get form data
            const email = document.getElementById('superAdminEmail').value.trim();
            const password = document.getElementById('superAdminPassword').value;
            
            // Validation
            if (!email || !password) {
                errorText.textContent = 'Veuillez remplir tous les champs';
                errorMessage.style.display = 'block';
                successMessage.style.display = 'none';
                return;
            }
            
            // Show loading state
            btnContent.style.display = 'none';
            loadingSpinner.style.display = 'flex';
            submitBtn.disabled = true;
            errorMessage.style.display = 'none';
            successMessage.style.display = 'none';
            
            try {
                console.log('👑 FRONTEND: Envoi de la requête de connexion Super Admin');
                
                const response = await fetch('/super-admin/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password })
                });
                
                const data = await response.json();
                console.log('👑 FRONTEND: Réponse reçue:', data);
                
                if (data.success) {
                    successText.textContent = 'Connexion Super Admin réussie ! Redirection...';
                    successMessage.style.display = 'block';
                    
                    // Redirect to super admin dashboard
                    setTimeout(() => {
                        window.location.href = '/super-admin/';
                    }, 1500);
                } else {
                    errorText.textContent = data.message || 'Identifiants Super Admin incorrects';
                    errorMessage.style.display = 'block';
                }
            } catch (error) {
                console.error('👑 FRONTEND: Erreur de connexion Super Admin:', error);
                errorText.textContent = 'Erreur de connexion. Veuillez réessayer.';
                errorMessage.style.display = 'block';
            } finally {
                // Reset button state
                btnContent.style.display = 'flex';
                loadingSpinner.style.display = 'none';
                submitBtn.disabled = false;
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
   