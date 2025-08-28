// Variables globales
const isEditMode = false
let originalData = {}

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

      await createUser(userData)
    })
  }

  if (deptHeadForm) {
    deptHeadForm.addEventListener("submit", async function (e) {
      e.preventDefault()
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

      await createUser(userData)
    })
  }
})

// Fonction pour créer un utilisateur
async function createUser(userData) {
  try {
    console.log("📤 Création utilisateur:", userData.role, userData.email)

    const response = await fetch("/api/create-user", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    })

    const result = await response.json()
    console.log("📥 Réponse création utilisateur:", result)

    if (result.success) {
      showNotification(result.message, "success")
      closeAddRecruiterModal()
      closeAddDepartmentHeadModal()
      setTimeout(() => location.reload(), 1500)
    } else {
      showNotification("Erreur: " + result.message, "error")
    }
  } catch (error) {
    console.error("❌ Erreur création utilisateur:", error)
    showNotification("Erreur de connexion au serveur", "error")
  }
}

// Fonctions pour la gestion des utilisateurs (seulement pour super admins)
async function editUser(userId) {
  try {
    const res = await fetch(`/api/users/${userId}`)
    const data = await res.json()
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
          await updateUser(userId, payload)
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
          await updateUser(userId, payload)
        }
      }
    } else {
      showNotification("Rôle non pris en charge pour l'édition", "warning")
    }
  } catch (e) {
    showNotification("Erreur de connexion lors du chargement de l'utilisateur", "error")
  }
}

async function updateUser(userId, payload) {
  try {
    const res = await fetch(`/api/users/${userId}/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    if (data.success) {
      showNotification(data.message || 'Utilisateur mis à jour', 'success')
      setTimeout(() => window.location.reload(), 1200)
    } else {
      showNotification(data.message || 'Erreur lors de la mise à jour', 'error')
    }
  } catch (e) {
    showNotification('Erreur réseau lors de la mise à jour', 'error')
  }
}

async function deactivateUser(userId) {
  if (!confirm("Êtes-vous sûr de vouloir supprimer cet utilisateur ?")) return
  try {
    const res = await fetch(`/api/users/${userId}`, { method: 'DELETE' })
    const data = await res.json()
    if (data.success) {
      showNotification(data.message || 'Utilisateur supprimé', 'success')
      setTimeout(() => window.location.reload(), 1200)
    } else {
      showNotification(data.message || 'Suppression échouée', 'error')
    }
  } catch (e) {
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
