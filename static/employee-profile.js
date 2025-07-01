// Variables globales
let currentEmployee = null
let notes = []

// Charger les données de l'employé au chargement de la page
document.addEventListener("DOMContentLoaded", () => {
  loadEmployeeData()
  initializeCircleProgress()
  loadNotes()
})

// Charger les données de l'employé depuis localStorage ou URL
function loadEmployeeData() {
  // Essayer de récupérer l'ID depuis l'URL
  const urlParams = new URLSearchParams(window.location.search)
  const employeeId = urlParams.get("id")

  if (employeeId) {
    // Charger depuis l'API
    loadEmployeeFromAPI(employeeId)
  } else {
    // Essayer localStorage
    const employeeData = localStorage.getItem("selectedEmployee")
    if (employeeData) {
      currentEmployee = JSON.parse(employeeData)
      displayEmployeeInfo()
    } else {
      // Données par défaut si aucune donnée n'est trouvée
      currentEmployee = {
        id: 1,
        first_name: "John",
        last_name: "Doe",
        email: "john.doe@company.com",
        position: "Développeur Full-Stack",
        department_id: 1,
        phone: "+33 1 23 45 67 89",
        hire_date: "2022-01-15",
        created_at: new Date(),
      }
      displayEmployeeInfo()
    }
  }
}

// Charger l'employé depuis l'API
async function loadEmployeeFromAPI(employeeId) {
  try {
    const response = await fetch(`/api/employee/${employeeId}`)
    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        currentEmployee = result.employee
        displayEmployeeInfo()
      }
    }
  } catch (error) {
    console.error("Erreur chargement employé:", error)
    // Utiliser des données par défaut en cas d'erreur
    loadEmployeeData()
  }
}

// Afficher les informations de l'employé
function displayEmployeeInfo() {
  if (!currentEmployee) return

  // Informations principales
  document.getElementById("employeeName").textContent = `${currentEmployee.first_name} ${currentEmployee.last_name}`
  document.getElementById("employeePosition").textContent = currentEmployee.position
  document.getElementById("employeeEmail").textContent = currentEmployee.email
  document.getElementById("employeePhone").textContent = currentEmployee.phone || "Non renseigné"
  document.getElementById("employeeId").textContent =
    currentEmployee.employee_id || `EMP${String(currentEmployee.id).padStart(3, "0")}`

  // Avatar avec initiales
  const avatar = document.getElementById("employeeAvatar")
  avatar.textContent = `${currentEmployee.first_name[0]}${currentEmployee.last_name[0]}`

  // Département
  document.getElementById("employeeDepartment").textContent =
    currentEmployee.department_name || getDepartmentName(currentEmployee.department_id)

  // Date d'embauche
  if (currentEmployee.hire_date) {
    const hireDate = new Date(currentEmployee.hire_date)
    document.getElementById("employeeHireDate").textContent = `Embauché le ${hireDate.toLocaleDateString("fr-FR")}`

    // Calculer les années de service
    const yearsOfService = Math.floor((new Date() - hireDate) / (365.25 * 24 * 60 * 60 * 1000))
    document.getElementById("yearsOfService").textContent = yearsOfService
  }

  // Statistiques simulées
  document.getElementById("completedProjects").textContent = Math.floor(Math.random() * 20) + 5
  document.getElementById("performanceRating").textContent = (4 + Math.random()).toFixed(1)
}

// Obtenir le nom du département (simulé)
function getDepartmentName(departmentId) {
  const departments = {
    1: "Développement",
    2: "Ressources Humaines",
    3: "Marketing",
    4: "Ventes",
    5: "Support",
  }
  return departments[departmentId] || "Département inconnu"
}

// Initialiser les cercles de progression
function initializeCircleProgress() {
  const circles = document.querySelectorAll(".circle-progress")
  circles.forEach((circle) => {
    const percentage = circle.getAttribute("data-percentage")
    circle.style.setProperty("--percentage", percentage)
  })
}

// Fonction pour retourner au dashboard
function goBackToDashboard() {
  window.location.href = "/dashboard"
}

// Fonctions pour les actions
function editEmployee() {
  showNotification("Fonction de modification en cours de développement", "info")
}

function exportProfile() {
  const profileData = {
    employee: currentEmployee,
    exportDate: new Date().toISOString(),
    notes: notes,
  }

  const blob = new Blob([JSON.stringify(profileData, null, 2)], { type: "application/json" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `profil_${currentEmployee.first_name}_${currentEmployee.last_name}.json`
  a.click()
  URL.revokeObjectURL(url)

  showNotification("Profil exporté avec succès !", "success")
}

function addSkill() {
  const skillName = prompt("Nom de la compétence:")
  const skillLevel = prompt("Niveau (0-100):")

  if (skillName && skillLevel && !isNaN(skillLevel)) {
    const skillsList = document.getElementById("skillsList")
    const skillItem = document.createElement("div")
    skillItem.className = "skill-item"
    skillItem.innerHTML = `
            <span class="skill-name">${skillName}</span>
            <div class="skill-bar">
                <div class="skill-progress" style="width: ${skillLevel}%"></div>
            </div>
            <span class="skill-level">${skillLevel}%</span>
        `
    skillsList.appendChild(skillItem)
    showNotification("Compétence ajoutée avec succès !", "success")
  }
}

function uploadDocument() {
  showNotification("Fonction d'upload en cours de développement", "info")
}

function viewDocument(type) {
  showNotification(`Ouverture du document: ${type}`, "info")
}

function downloadDocument(type) {
  showNotification(`Téléchargement du document: ${type}`, "info")
}

// Gestion des notes
function addNote() {
  document.getElementById("noteModal").classList.add("show")
  document.body.style.overflow = "hidden"
}

function closeNoteModal() {
  document.getElementById("noteModal").classList.remove("show")
  document.body.style.overflow = "auto"
  document.getElementById("noteForm").reset()
}

function saveNote() {
  const noteContent = document.getElementById("noteContent").value.trim()

  if (!noteContent) {
    showNotification("Veuillez saisir une note", "error")
    return
  }

  const note = {
    id: Date.now(),
    content: noteContent,
    author: "Sarah Johnson", // Utilisateur actuel
    date: new Date().toLocaleDateString("fr-FR"),
    timestamp: new Date(),
  }

  notes.unshift(note)
  saveNotes()
  renderNotes()
  closeNoteModal()
  showNotification("Note ajoutée avec succès !", "success")
}

function loadNotes() {
  const savedNotes = localStorage.getItem(`notes_${currentEmployee?.id}`)
  if (savedNotes) {
    notes = JSON.parse(savedNotes)
    renderNotes()
  }
}

function saveNotes() {
  localStorage.setItem(`notes_${currentEmployee.id}`, JSON.stringify(notes))
}

function renderNotes() {
  const notesList = document.getElementById("notesList")

  if (notes.length === 0) {
    notesList.innerHTML = `
            <div class="note-item">
                <div class="note-header">
                    <span class="note-author">Système</span>
                    <span class="note-date">${new Date().toLocaleDateString("fr-FR")}</span>
                </div>
                <p class="note-content">Aucune note disponible pour cet employé.</p>
            </div>
        `
    return
  }

  notesList.innerHTML = notes
    .map(
      (note) => `
        <div class="note-item">
            <div class="note-header">
                <span class="note-author">${note.author}</span>
                <span class="note-date">${note.date}</span>
            </div>
            <p class="note-content">${note.content}</p>
        </div>
    `,
    )
    .join("")
}

// Système de notifications
function showNotification(message, type = "info") {
  const notification = document.createElement("div")
  notification.className = `notification ${type}`

  const icons = {
    success: "fa-check-circle",
    error: "fa-exclamation-circle",
    warning: "fa-exclamation-triangle",
    info: "fa-info-circle",
  }

  const colors = {
    success: "rgba(39, 174, 96, 0.9)",
    error: "rgba(231, 76, 60, 0.9)",
    warning: "rgba(243, 156, 18, 0.9)",
    info: "rgba(52, 152, 219, 0.9)",
  }

  notification.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `

  notification.style.cssText = `
        position: fixed;
        top: 2rem;
        right: 2rem;
        background: ${colors[type]};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        z-index: 10000;
        backdrop-filter: blur(10px);
        animation: slideInRight 0.3s ease;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        min-width: 300px;
        max-width: 400px;
    `

  document.body.appendChild(notification)

  setTimeout(() => {
    notification.style.animation = "slideOutRight 0.3s ease"
    setTimeout(() => {
      if (notification.parentElement) {
        document.body.removeChild(notification)
      }
    }, 300)
  }, 4000)
}

// Fermer les modals en cliquant à l'extérieur
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("show")
    document.body.style.overflow = "auto"
  }
})

// Fermer les modals avec Escape
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    const openModal = document.querySelector(".modal-overlay.show")
    if (openModal) {
      openModal.classList.remove("show")
      document.body.style.overflow = "auto"
    }
  }
})

// Ajouter les animations CSS
const style = document.createElement("style")
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .notification-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 0.25rem;
        border-radius: 4px;
        transition: all 0.3s ease;
        margin-left: auto;
    }

    .notification-close:hover {
        background: rgba(255, 255, 255, 0.2);
    }
`
document.head.appendChild(style)
