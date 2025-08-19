// Variables globales
const isEditMode = false
let originalData = {}

// Fonctions pour les modals - seulement si l'utilisateur est super admin
function openAddRecruiterModal() {
  const modal = document.getElementById("addRecruiterModal")
  if (modal) {
    modal.classList.add("show")
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
  }
}

function openAddDepartmentHeadModal() {
  const modal = document.getElementById("addDepartmentHeadModal")
  if (modal) {
    modal.classList.add("show")
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
function editUser(userId) {
  console.log("✏️ Édition utilisateur:", userId)
  showNotification("Fonctionnalité en cours de développement", "info")
}

function deactivateUser(userId) {
  if (confirm("Êtes-vous sûr de vouloir désactiver cet utilisateur ?")) {
    console.log("🚫 Désactivation utilisateur:", userId)
    showNotification("Fonctionnalité en cours de développement", "info")
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
