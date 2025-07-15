// Variables globales
let isEditMode = false
let originalData = {}

// Fonctions pour les modals - définies en premier
function openAddRecruiterModal() {
    document.getElementById('addRecruiterModal').classList.add('show');
}

function closeAddRecruiterModal() {
    document.getElementById('addRecruiterModal').classList.remove('show');
    document.getElementById('addRecruiterForm').reset();
}

function openAddDepartmentHeadModal() {
    document.getElementById('addDepartmentHeadModal').classList.add('show');
}

function closeAddDepartmentHeadModal() {
    document.getElementById('addDepartmentHeadModal').classList.remove('show');
    document.getElementById('addDepartmentHeadForm').reset();
}

// Initialisation après chargement du DOM
document.addEventListener("DOMContentLoaded", () => {
  saveOriginalData()
  
  // Attacher les écouteurs d'événements
  const recruiterForm = document.getElementById('addRecruiterForm')
  const deptHeadForm = document.getElementById('addDepartmentHeadForm')
  
  if (recruiterForm) {
    recruiterForm.addEventListener('submit', async function(e) {
      e.preventDefault()
      const formData = new FormData(this)
      
      const userData = {
        email: formData.get('email'),
        password: formData.get('password'),
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        role: 'recruiter',
        permissions: {
          can_manage_applications: formData.get('can_manage_applications') === 'on',
          can_recommend_candidates: formData.get('can_recommend_candidates') === 'on'
        }
      }
      
      await createUser(userData)
    })
  }

  if (deptHeadForm) {
    deptHeadForm.addEventListener('submit', async function(e) {
      e.preventDefault()
      const formData = new FormData(this)
      const departments = Array.from(formData.getAll('departments')).map(id => parseInt(id))
      
      const userData = {
        email: formData.get('email'),
        password: formData.get('password'),
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        role: 'department_head',
        permissions: {
          can_add_department: formData.get('can_add_department') === 'on',
          can_manage_applications: formData.get('can_manage_applications') === 'on'
        },
        departments: departments
      }
      
      await createUser(userData)
    })
  }
})

// Sauvegarder les données originales
function saveOriginalData() {
  const fields = document.querySelectorAll("[data-field]")
  originalData = {}

  fields.forEach((field) => {
    const fieldName = field.getAttribute("data-field")
    if (field.classList.contains("detail-value")) {
      originalData[fieldName] = field.textContent.trim()
    }
  })
}

// Basculer le mode édition
function toggleEditMode() {
  isEditMode = !isEditMode
  const editBtn = document.getElementById("editBtnText")
  const editActions = document.getElementById("editActions")
  const uploadBtn = document.querySelector(".upload-logo-btn")

  if (isEditMode) {
    enterEditMode()
    editBtn.textContent = "Annuler"
    editActions.style.display = "flex"
    uploadBtn.style.display = "flex"
  } else {
    exitEditMode()
    editBtn.textContent = "Modifier"
    editActions.style.display = "none"
    uploadBtn.style.display = "none"
    restoreOriginalData()
  }
}

// Entrer en mode édition
function enterEditMode() {
  const detailValues = document.querySelectorAll(".detail-value")
  const detailInputs = document.querySelectorAll(".detail-input")

  detailValues.forEach((value) => {
    value.style.display = "none"
  })

  detailInputs.forEach((input) => {
    input.style.display = "block"
    const fieldName = input.getAttribute("data-field")
    if (originalData[fieldName]) {
      if (input.tagName === "TEXTAREA") {
        input.value = originalData[fieldName]
      } else if (input.tagName === "SELECT") {
        input.value = originalData[fieldName]
      } else {
        input.value = originalData[fieldName]
      }
    }
  })
}

// Sortir du mode édition
function exitEditMode() {
  const detailValues = document.querySelectorAll(".detail-value")
  const detailInputs = document.querySelectorAll(".detail-input")

  detailValues.forEach((value) => {
    value.style.display = "block"
  })

  detailInputs.forEach((input) => {
    input.style.display = "none"
  })
}

// Restaurer les données originales
function restoreOriginalData() {
  const fields = document.querySelectorAll("[data-field]")

  fields.forEach((field) => {
    const fieldName = field.getAttribute("data-field")
    if (field.classList.contains("detail-value") && originalData[fieldName]) {
      field.textContent = originalData[fieldName]
    }
  })
}

// Annuler les modifications
function cancelEdit() {
  toggleEditMode()
}

// Sauvegarder les modifications
function saveChanges() {
  const detailInputs = document.querySelectorAll(".detail-input")
  const detailValues = document.querySelectorAll(".detail-value")

  // Mettre à jour les valeurs affichées avec les nouvelles données
  detailInputs.forEach((input) => {
    const fieldName = input.getAttribute("data-field")
    const correspondingValue = document.querySelector(`.detail-value[data-field="${fieldName}"]`)

    if (correspondingValue) {
      correspondingValue.textContent = input.value
    }
  })

  // Sauvegarder les nouvelles données comme données originales
  saveOriginalData()

  // Sortir du mode édition
  isEditMode = false
  const editBtn = document.getElementById("editBtnText")
  const editActions = document.getElementById("editActions")
  const uploadBtn = document.querySelector(".upload-logo-btn")

  exitEditMode()
  editBtn.textContent = "Modifier"
  editActions.style.display = "none"
  uploadBtn.style.display = "none"

  // Afficher un message de confirmation
  showNotification("Profil mis à jour avec succès !", "success")
}

// Télécharger un logo
function uploadLogo() {
  const input = document.createElement("input")
  input.type = "file"
  input.accept = "image/*"

  input.onchange = (event) => {
    const file = event.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const logoPlaceholder = document.getElementById("companyLogo")
        logoPlaceholder.innerHTML = `<img src="${e.target.result}" alt="Logo" style="width: 100%; height: 100%; object-fit: cover; border-radius: 16px;">`
        showNotification("Logo mis à jour !", "success")
      }
      reader.readAsDataURL(file)
    }
  }

  input.click()
}

// Retourner au dashboard
function goBack() {
  if (isEditMode) {
    if (confirm("Vous avez des modifications non sauvegardées. Voulez-vous vraiment quitter ?")) {
      window.location.href = "/dashboard"
    }
  } else {
    window.location.href = "/dashboard"
  }
}

// Afficher une notification
function showNotification(message, type = "info") {
  const notification = document.createElement("div")
  notification.className = `notification ${type}`
  
  // Icône en fonction du type de notification
  let icon = "fa-info-circle"
  if (type === "success") icon = "fa-check-circle"
  if (type === "error") icon = "fa-exclamation-circle"
  if (type === "warning") icon = "fa-exclamation-triangle"
  
  notification.innerHTML = `
    <div class="notification-content">
      <i class="fas ${icon}"></i>
      <span>${message}</span>
    </div>
    <button class="notification-close" onclick="this.parentElement.remove()">
      <i class="fas fa-times"></i>
    </button>
  `
  
  // Styles pour la notification
  notification.style.cssText = `
    position: fixed;
    top: 2rem;
    right: 2rem;
    background: var(--card-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-color);
    border-left: 4px solid;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    z-index: 10000;
    min-width: 320px;
    max-width: 450px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    transform: translateX(100%);
    transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  `
  
  // Couleur de la bordure en fonction du type
  if (type === "success") notification.style.borderLeftColor = "var(--success-color)"
  if (type === "error") notification.style.borderLeftColor = "var(--error-color)"
  if (type === "warning") notification.style.borderLeftColor = "var(--warning-color)"
  if (type === "info") notification.style.borderLeftColor = "var(--info-color)"
  
  document.body.appendChild(notification)
  
  // Animation d'entrée
  setTimeout(() => {
    notification.style.transform = "translateX(0)"
  }, 100)
  
  // Suppression automatique après 5 secondes (sauf pour les erreurs)
  if (type !== "error") {
    setTimeout(() => {
      notification.style.transform = "translateX(100%)"
      setTimeout(() => {
        if (notification.parentElement) {
          notification.remove()
        }
      }, 300)
    }, 5000)
  }
}

// Ajouter les animations CSS
const style = document.createElement("style")
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`
document.head.appendChild(style)

// Gestion des raccourcis clavier
document.addEventListener("keydown", (e) => {
  // Ctrl/Cmd + S pour sauvegarder
  if ((e.ctrlKey || e.metaKey) && e.key === "s") {
    e.preventDefault()
    if (isEditMode) {
      saveChanges()
    }
  }

  // Escape pour annuler
  if (e.key === "Escape" && isEditMode) {
    cancelEdit()
  }
})

// Prévenir la perte de données
window.addEventListener("beforeunload", (e) => {
  if (isEditMode) {
    e.preventDefault()
    e.returnValue = "Vous avez des modifications non sauvegardées. Voulez-vous vraiment quitter ?"
  }
})

// Fonction pour créer un utilisateur
async function createUser(userData) {
    try {
        const response = await fetch('/api/create-user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        })
        
        const result = await response.json()
        if (result.success) {
            showNotification('Utilisateur créé avec succès !', 'success')
            closeAddRecruiterModal()
            closeAddDepartmentHeadModal()
            setTimeout(() => location.reload(), 1500)
        } else {
            showNotification('Erreur: ' + result.message, 'error')
        }
    } catch (error) {
        showNotification('Erreur de connexion au serveur', 'error')
    }
}

// Fonction pour éditer l'entreprise
function editCompany() {
  window.location.href = '/company-setup'
}

// Fonction pour aller au tableau de bord
function goToDashboard() {
  window.location.href = '/dashboard'
}

// Fonction pour configurer l'entreprise
function goToSetup() {
  window.location.href = '/company-setup'
}

// Gestion du logo
let selectedLogoFile = null;
let isUploading = false;

function handleFileSelect(file) {
    console.log('📁 Fichier sélectionné:', file.name, file.type, file.size);
    
    // Vérifier le type de fichier
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/svg+xml'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Format de fichier non supporté. Utilisez PNG, JPG, GIF ou SVG.', 'error');
        return;
    }
    
    // Vérifier la taille (5MB max)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        showNotification('Le fichier est trop volumineux. Taille maximum: 5MB', 'error');
        return;
    }
    
    selectedLogoFile = file;
    
    // Afficher l'aperçu
    const reader = new FileReader();
    reader.onload = function(e) {
        showLogoPreview(e.target.result, file);
    };
    reader.readAsDataURL(file);
}

function showLogoPreview(imageSrc, file) {
    console.log('👁️ Affichage aperçu pour:', file.name);
    
    // Masquer la zone d'upload et afficher l'aperçu
    document.getElementById('logoUploadSection').style.display = 'none';
    document.getElementById('logoPreviewSection').style.display = 'block';
    
    // Mettre à jour les images d'aperçu
    document.getElementById('previewImage').src = imageSrc;
    document.getElementById('previewSmall').src = imageSrc;
    document.getElementById('previewMedium').src = imageSrc;
    
    // Mettre à jour les informations du fichier
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
    
    // Obtenir les dimensions de l'image
    const img = new Image();
    img.onload = function() {
        document.getElementById('fileDimensions').textContent = `${this.width}x${this.height}px`;
    };
    img.src = imageSrc;
    
    // Activer le bouton de sauvegarde
    document.getElementById('saveLogoBtn').disabled = false;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function saveLogo() {
    if (!selectedLogoFile || isUploading) {
        console.log('❌ Pas de fichier sélectionné ou upload en cours');
        return;
    }
    
    console.log('📤 Début upload logo:', selectedLogoFile.name);
    
    isUploading = true;
    const saveBtn = document.getElementById('saveLogoBtn');
    const saveText = document.getElementById('saveButtonText');
    
    // Mettre à jour l'interface
    saveBtn.disabled = true;
    saveText.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Upload en cours...';
    
    const formData = new FormData();
    formData.append('logo', selectedLogoFile);
    
    try {
        showNotification('Upload du logo en cours...', 'info');
        
        console.log('🌐 Envoi requête vers /api/upload-logo');
        
        const response = await fetch('/api/upload-logo', {
            method: 'POST',
            body: formData
        });
        
        console.log('📡 Réponse reçue:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('📋 Résultat:', result);
        
        if (result.success) {
            showNotification('Logo mis à jour avec succès !', 'success');
            
            // Mettre à jour l'affichage du logo dans la page
            updateLogoDisplay(result.logo_url);
            
            // Fermer le modal après un délai
            setTimeout(() => {
                closeLogoModal();
            }, 1500);
        } else {
            throw new Error(result.message || 'Erreur lors de l\'upload');
        }
        
    } catch (error) {
        console.error('❌ Erreur upload logo:', error);
        showNotification('Erreur lors de l\'upload: ' + error.message, 'error');
        
        // Réinitialiser l'interface
        saveBtn.disabled = false;
        saveText.innerHTML = '<i class="fas fa-save"></i> Enregistrer le logo';
    } finally {
        isUploading = false;
    }
}

async function removeCompanyLogo() {
    try {
        console.log('🗑️ Début suppression logo');
        showNotification('Suppression du logo...', 'info');
        
        const response = await fetch('/api/remove-logo', {
            method: 'DELETE'
        });
        
        console.log('📡 Réponse suppression:', response.status);
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('📋 Résultat suppression:', result);
        
        if (result.success) {
            showNotification('Logo supprimé avec succès !', 'success');
            
            // Mettre à jour l'affichage
            updateLogoDisplay(null);
            closeLogoModal();
        } else {
            throw new Error(result.message || 'Erreur lors de la suppression');
        }
        
    } catch (error) {
        console.error('❌ Erreur suppression logo:', error);
        showNotification('Erreur lors de la suppression: ' + error.message, 'error');
    }
}

function updateLogoDisplay(logoUrl) {
    console.log('🔄 Mise à jour affichage logo:', logoUrl);
    const logoContainer = document.querySelector('.company-logo');
    
    if (logoUrl) {
        logoContainer.innerHTML = `
            <img src="${logoUrl}" alt="Logo entreprise" id="companyLogoImg">
            <div class="logo-overlay">
                <i class="fas fa-camera"></i>
                <span>Changer</span>
            </div>
        `;
    } else {
        logoContainer.innerHTML = `
            <i class="fas fa-building" id="companyLogoIcon"></i>
            <div class="logo-overlay">
                <i class="fas fa-camera"></i>
                <span>Ajouter</span>
            </div>
        `;
    }
}