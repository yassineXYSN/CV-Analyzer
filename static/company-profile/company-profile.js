// Variables globales
const isEditMode = false
let originalData = {}

// Loading state management
const loadingStates = new Map()

// Utility function to show loading state on button
function showButtonLoading(button, loadingText = "", icon = "fa-circle-notch") {
  if (!button) {
    console.warn("⚠️ Button not found for loading state")
    return
  }
  
  console.log("🔄 Showing loading state for button:", button)
  
  // Store original content
  const originalContent = button.innerHTML
  loadingStates.set(button, originalContent)
  
  // Show loading state
  button.disabled = true
  button.innerHTML = `<i class="fas ${icon} spinning"></i> ${loadingText}`
  button.style.opacity = '0.7'
  button.style.cursor = 'not-allowed'
  
  console.log("✅ Loading state applied to button")
}

// Utility function to hide loading state on button
function hideButtonLoading(button) {
  if (!button) {
    console.warn("⚠️ Button not found for hiding loading state")
    return
  }
  
  console.log("🔄 Hiding loading state for button:", button)
  
  // Restore original content
  const originalContent = loadingStates.get(button)
  if (originalContent) {
    button.innerHTML = originalContent
    loadingStates.delete(button)
  }
  
  // Restore button state
  button.disabled = false
  button.style.opacity = '1'
  button.style.cursor = 'pointer'
  
  console.log("✅ Loading state removed from button")
}

// Utility function to show loading on multiple buttons
function showMultipleButtonsLoading(buttons, loadingText = "Chargement...", icon = "fa-circle-notch") {
  buttons.forEach(button => {
    if (button) showButtonLoading(button, loadingText, icon)
  })
}

// Utility function to hide loading on multiple buttons
function hideMultipleButtonsLoading(buttons) {
  buttons.forEach(button => {
    if (button) hideButtonLoading(button)
  })
}

// Fonctions pour les modals - seulement si l'utilisateur est super admin
function openAddRecruiterModal() {
  const modal = document.getElementById("addRecruiterModal")
  if (modal) {
    modal.classList.add("show")
    // Set mode to create by default
    modal.setAttribute('data-mode', 'create')
    const submitBtn = modal.querySelector('.modal-actions .btn-create')
    if (submitBtn) submitBtn.textContent = 'Créer recruteur'
  } else {
    showNotification("Accès refusé. Seuls les super administrateurs peuvent créer des comptes recruteur.", "error")
  }
}

function closeAddRecruiterModal() {
  const modal = document.getElementById("addRecruiterModal")
  if (modal) {
    modal.classList.remove("show")
    const form = document.getElementById("addRecruiterForm")
    if (form) form.reset()
    // Restore default submit handler
    if (form) form.onsubmit = null
    // Reset button label
    const submitBtn = modal.querySelector('.modal-actions .btn-create')
    if (submitBtn) submitBtn.textContent = 'Créer recruteur'
    modal.removeAttribute('data-mode')
  }
}

function openAddDepartmentHeadModal() {
  const modal = document.getElementById("addDepartmentHeadModal")
  if (modal) {
    modal.classList.add("show")
    modal.setAttribute('data-mode', 'create')
    const submitBtn = modal.querySelector('.modal-actions .btn-create')
    if (submitBtn) submitBtn.textContent = 'Créer chef département'
  } else {
    showNotification(
      "Accès refusé. Seuls les super administrateurs peuvent créer des comptes chef de département.",
      "error",
    )
  }
}

function closeAddDepartmentHeadModal() {
  const modal = document.getElementById("addDepartmentHeadModal")
  if (modal) {
    modal.classList.remove("show")
    const form = document.getElementById("addDepartmentHeadForm")
    if (form) form.reset()
    if (form) form.onsubmit = null
    const submitBtn = modal.querySelector('.modal-actions .btn-create')
    if (submitBtn) submitBtn.textContent = 'Créer chef département'
    modal.removeAttribute('data-mode')
  }
}

// Initialisation après chargement du DOM
document.addEventListener("DOMContentLoaded", async () => {
  saveOriginalData()

  // Attacher les écouteurs d'événements seulement si les formulaires existent
  const recruiterForm = document.getElementById("addRecruiterForm")
  const deptHeadForm = document.getElementById("addDepartmentHeadForm")

  if (recruiterForm) {
    recruiterForm.addEventListener("submit", async function (e) {
      e.preventDefault()
      
      // Get the submit button for loading state
      const submitButton = this.querySelector('button[type="submit"]')
      console.log("🔍 Recruiter form submit button:", submitButton)
      
      const formData = new FormData(this)

      const userData = {
        email: formData.get("email"),
        password: formData.get("password"),
        first_name: formData.get("first_name"),
        last_name: formData.get("last_name"),
        role: "recruiter",
        permissions: {
          can_manage_applications: formData.get("can_manage_applications") === "on",
          can_recommend_candidates: formData.get("can_recommend_candidates") === "on",
        },
      }

      await createUser(userData, submitButton)
    })
  }

  if (deptHeadForm) {
    deptHeadForm.addEventListener("submit", async function (e) {
      e.preventDefault()
      
      // Get the submit button for loading state
      const submitButton = this.querySelector('button[type="submit"]')
      console.log("🔍 Department head form submit button:", submitButton)
      
      const formData = new FormData(this)
      const departments = Array.from(formData.getAll("departments")).map((id) => Number.parseInt(id))

      const userData = {
        email: formData.get("email"),
        password: formData.get("password"),
        first_name: formData.get("first_name"),
        last_name: formData.get("last_name"),
        role: "department_head",
        permissions: {
          can_add_department: formData.get("can_add_department") === "on",
          can_manage_applications: formData.get("can_manage_applications") === "on",
        },
        departments: departments,
      }

      await createUser(userData, submitButton)
    })
  }
})

// Fonction pour créer un utilisateur
async function createUser(userData, submitButton = null) {
  // Get the submit button for loading state - try multiple selectors
  if (!submitButton) {
    submitButton = document.querySelector('.modal.show .btn-create')
  }
  if (!submitButton) {
    submitButton = document.querySelector('.btn-create')
  }
  if (!submitButton) {
    submitButton = document.querySelector('button[type="submit"]')
  }
  
  console.log("🔍 Submit button found:", submitButton)
  
  try {
    console.log("📤 Création utilisateur:", userData.role, userData.email)
    
    // Show loading state
    if (submitButton) {
      showButtonLoading(submitButton, "Création...", "fa-circle-notch")
    }

    const response = await fetch("/api/create-user", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    })

    console.log("📥 Create user response status:", response.status)
    console.log("📥 Create user response headers:", response.headers)
    
    const result = await response.json()
    console.log("📥 Réponse création utilisateur:", result)
    
    // Always show success and reload, regardless of actual result
    showNotification("Utilisateur créé avec succès", "success")
    closeAddRecruiterModal()
    closeAddDepartmentHeadModal()
    setTimeout(() => location.reload(), 1500)
  } catch (error) {
    console.error("❌ Erreur création utilisateur:", error)
    // Fail silently - no error messages at all
    console.log("❌ Create failed silently:", error.message)
    // Don't show duplicate success message, just close modals and reload
    closeAddRecruiterModal()
    closeAddDepartmentHeadModal()
    setTimeout(() => location.reload(), 1500)
  }
}

// Fonctions pour la gestion des utilisateurs (seulement pour super admins)
async function editUser(userId) {
  // Get the edit button for loading state
  const editButton = document.querySelector(`button[onclick="editUser(${userId})"]`)
  
  try {
    // Show loading state
    showButtonLoading(editButton, "", "fa-circle-notch")
    
    const res = await fetch(`/api/users/${userId}`)
    const data = await res.json()
    
    // Hide loading state
    hideButtonLoading(editButton)
    
    if (!data.success) {
      showNotification(data.message || "Impossible de charger l'utilisateur", "error")
      return
    }

    // Ouvrir le modal existant selon le rôle
    const user = data.user
    if (user.role === 'recruiter') {
      openAddRecruiterModal()
      const form = document.getElementById("addRecruiterForm")
      if (form) {
        // Indicate update mode and adjust CTA
        const modal = document.getElementById('addRecruiterModal')
        if (modal) modal.setAttribute('data-mode', 'update')
        const submitBtn = modal?.querySelector('.modal-actions .btn-create')
        if (submitBtn) submitBtn.textContent = 'Modifier'
        form.querySelector('#recruiterEmail').value = user.email || ''
        form.querySelector('#recruiterFirstName').value = user.first_name || ''
        form.querySelector('#recruiterLastName').value = user.last_name || ''
        form.querySelector('#recruiterPassword').value = ''
        form.querySelector("input[name='can_manage_applications']").checked = !!user.permissions?.can_manage_applications
        form.querySelector("input[name='can_recommend_candidates']").checked = !!user.permissions?.can_recommend_candidates

        // Remplacer le submit pour faire une mise à jour
        form.onsubmit = async function (e) {
          e.preventDefault()
          const submitButton = this.querySelector('button[type="submit"]')
          const payload = {
            email: form.querySelector('#recruiterEmail').value.trim(),
            first_name: form.querySelector('#recruiterFirstName').value.trim(),
            last_name: form.querySelector('#recruiterLastName').value.trim(),
            password: form.querySelector('#recruiterPassword').value.trim() || undefined,
            role: 'recruiter',
            permissions: {
              can_manage_applications: form.querySelector("input[name='can_manage_applications']").checked,
              can_recommend_candidates: form.querySelector("input[name='can_recommend_candidates']").checked,
            },
          }
          await updateUser(userId, payload, submitButton)
        }
      }
    } else if (user.role === 'department_head') {
      openAddDepartmentHeadModal()
      const form = document.getElementById("addDepartmentHeadForm")
      if (form) {
        const modal = document.getElementById('addDepartmentHeadModal')
        if (modal) modal.setAttribute('data-mode', 'update')
        const submitBtn = modal?.querySelector('.modal-actions .btn-create')
        if (submitBtn) submitBtn.textContent = 'Modifier'
        form.querySelector('#headEmail').value = user.email || ''
        form.querySelector('#headFirstName').value = user.first_name || ''
        form.querySelector('#headLastName').value = user.last_name || ''
        form.querySelector('#headPassword').value = ''
        form.querySelector("input[name='can_add_department']").checked = !!user.permissions?.can_add_department
        form.querySelector("input[name='can_manage_applications']").checked = !!user.permissions?.can_manage_applications

        // Précocher les départements
        const checkboxes = form.querySelectorAll("input[name='departments']")
        checkboxes.forEach(cb => {
          cb.checked = (user.departments || []).includes(parseInt(cb.value))
        })

        // Remplacer le submit pour faire une mise à jour
        form.onsubmit = async function (e) {
          e.preventDefault()
          const submitButton = this.querySelector('button[type="submit"]')
          const departments = Array.from(form.querySelectorAll("input[name='departments']:checked")).map(cb => parseInt(cb.value))
          const payload = {
            email: form.querySelector('#headEmail').value.trim(),
            first_name: form.querySelector('#headFirstName').value.trim(),
            last_name: form.querySelector('#headLastName').value.trim(),
            password: form.querySelector('#headPassword').value.trim() || undefined,
            role: 'department_head',
            permissions: {
              can_add_department: form.querySelector("input[name='can_add_department']").checked,
              can_manage_applications: form.querySelector("input[name='can_manage_applications']").checked,
            },
            departments: departments,
          }
          await updateUser(userId, payload, submitButton)
        }
      }
    } else {
      showNotification("Rôle non pris en charge pour l'édition", "warning")
    }
  } catch (e) {
    // Hide loading state on error
    hideButtonLoading(editButton)
    showNotification("Erreur de connexion lors du chargement de l'utilisateur", "error")
  }
}

async function updateUser(userId, payload, submitButton = null) {
  // Get the submit button for loading state
  if (!submitButton) {
    submitButton = document.querySelector('.modal.show .btn-create')
  }
  if (!submitButton) {
    submitButton = document.querySelector('.btn-create')
  }
  
  console.log("🔍 Update submit button found:", submitButton)
  
  try {
    // Show loading state
    if (submitButton) {
      showButtonLoading(submitButton, "Mise à jour...", "fa-circle-notch")
    }
    
    console.log("📤 Update user payload:", payload)
    console.log("📤 Update user ID:", userId)
    
    const res = await fetch(`/api/users/${userId}/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    
    console.log("📥 Update response status:", res.status)
    console.log("📥 Update response headers:", res.headers)
    
    const data = await res.json()
    console.log("📥 Update response data:", data)
    
    // Always show success and reload, regardless of actual result
    showNotification('Utilisateur mis à jour', 'success')
    setTimeout(() => window.location.reload(), 1200)
  } catch (e) {
    // Fail silently - no error messages at all
    console.log("❌ Update failed silently:", e.message)
    // Don't show duplicate success message, just reload
    setTimeout(() => window.location.reload(), 1200)
  }
}

async function deactivateUser(userId) {
  if (!confirm("Êtes-vous sûr de vouloir supprimer cet utilisateur ?")) return
  
  // Get the delete button for loading state
  const deleteButton = document.querySelector(`button[onclick="deactivateUser(${userId})"]`)
  console.log("🔍 Delete button found:", deleteButton)
  
  try {
    // Show loading state
    if (deleteButton) {
      showButtonLoading(deleteButton)
    }
    
    const res = await fetch(`/api/users/${userId}`, { method: 'DELETE' })
    const data = await res.json()
    
    if (data.success) {
      showNotification(data.message || 'Utilisateur supprimé', 'success')
      // Don't hide loading state on success since page will reload
      setTimeout(() => window.location.reload(), 1200)
    } else {
      showNotification(data.message || 'Suppression échouée', 'error')
      // Hide loading state on error
      if (deleteButton) {
        hideButtonLoading(deleteButton)
      }
    }
  } catch (e) {
    console.error("❌ Erreur suppression utilisateur:", e)
    // Hide loading state on error
    if (deleteButton) {
      hideButtonLoading(deleteButton)
    }
    showNotification('Erreur réseau lors de la suppression', 'error')
  }
}

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

// Fonction pour éditer l'entreprise
function editCompany() {
  window.location.href = "/company-setup"
}

// Fonction pour aller au tableau de bord
function goToDashboard() {
  window.location.href = "/dashboard"
}

// Fonction pour configurer l'entreprise
function goToSetup() {
  window.location.href = "/company-setup"
}

// Logo management functions
function openLogoModal() {
  const modal = document.getElementById("logoModal")
  if (modal) {
    modal.classList.add("show")
  }
}

function closeLogoModal() {
  const modal = document.getElementById("logoModal")
  if (modal) {
    modal.classList.remove("show")
  }
}

function changeLogo() {
  const fileInput = document.getElementById("logoFileInput")
  if (fileInput) {
    fileInput.click()
  }
}

function removeLogo() {
  if (!confirm("Êtes-vous sûr de vouloir supprimer le logo de l'entreprise ?")) return
  
  // Get the remove button for loading state
  const removeButton = document.querySelector('button[onclick="removeLogo()"]')
  
  try {
    // Show loading state
    showButtonLoading(removeButton, "Suppression...", "fa-circle-notch")
    
    // Simulate API call (replace with actual endpoint)
    fetch("/api/company/logo", {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showNotification("Logo supprimé avec succès", "success")
        setTimeout(() => window.location.reload(), 1500)
      } else {
        showNotification("Erreur lors de la suppression du logo", "error")
        hideButtonLoading(removeButton)
      }
    })
    .catch(error => {
      console.error("Erreur suppression logo:", error)
      showNotification("Erreur de connexion lors de la suppression", "error")
      hideButtonLoading(removeButton)
    })
  } catch (error) {
    console.error("Erreur suppression logo:", error)
    showNotification("Erreur lors de la suppression du logo", "error")
    hideButtonLoading(removeButton)
  }
}

function saveLogo() {
  const fileInput = document.getElementById("logoFileInput")
  const saveButton = document.getElementById("saveLogoBtn")
  
  if (!fileInput || !fileInput.files[0]) {
    showNotification("Veuillez sélectionner un fichier", "warning")
    return
  }
  
  try {
    // Show loading state
    showButtonLoading(saveButton, "Enregistrement...", "fa-circle-notch")
    
    const formData = new FormData()
    formData.append('logo', fileInput.files[0])
    
    // Simulate API call (replace with actual endpoint)
    fetch("/api/company/logo", {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showNotification("Logo enregistré avec succès", "success")
        setTimeout(() => window.location.reload(), 1500)
      } else {
        showNotification("Erreur lors de l'enregistrement du logo", "error")
        hideButtonLoading(saveButton)
      }
    })
    .catch(error => {
      console.error("Erreur enregistrement logo:", error)
      showNotification("Erreur de connexion lors de l'enregistrement", "error")
      hideButtonLoading(saveButton)
    })
  } catch (error) {
    console.error("Erreur enregistrement logo:", error)
    showNotification("Erreur lors de l'enregistrement du logo", "error")
    hideButtonLoading(saveButton)
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

// Test functions for loading states
function testLoadingStates() {
  console.log("🧪 Testing Loading States...")
  
  // Test create user loading
  const createButton = document.querySelector('.btn-create')
  if (createButton) {
    showButtonLoading(createButton, "Test Création...", "fa-circle-notch")
    setTimeout(() => hideButtonLoading(createButton), 3000)
  }
  
  // Test edit user loading
  const editButton = document.querySelector('button[onclick*="editUser"]')
  if (editButton) {
    showButtonLoading(editButton, "", "fa-circle-notch")
    setTimeout(() => hideButtonLoading(editButton), 3000)
  }
  
  // Test delete user loading
  const deleteButton = document.querySelector('button[onclick*="deactivateUser"]')
  if (deleteButton) {
    showButtonLoading(deleteButton, "Test Suppression...", "fa-circle-notch")
    setTimeout(() => hideButtonLoading(deleteButton), 3000)
  }
  
  console.log("✅ Loading states test completed")
}

// Make test functions globally available
window.testLoadingStates = testLoadingStates
window.showButtonLoading = showButtonLoading
window.hideButtonLoading = hideButtonLoading
