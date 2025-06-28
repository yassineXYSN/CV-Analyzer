// Variables globales
let currentJob = null
let applications = []
const requiredSkills = ["JavaScript", "React", "Node.js", "MongoDB", "Git", "Agile"]

// Charger les données du job au chargement de la page
document.addEventListener("DOMContentLoaded", () => {
  loadJobData()
  loadApplications()
  renderSkills()
  renderApplications()
  renderTimeline()
})

// Charger les données du job depuis localStorage
function loadJobData() {
  const jobData = localStorage.getItem("selectedJob")
  if (jobData) {
    currentJob = JSON.parse(jobData)
    displayJobInfo()
  } else {
    // Données par défaut si aucune donnée n'est trouvée
    currentJob = {
      id: 1,
      title: "Développeur Full-Stack Senior",
      departmentId: 1,
      type: "cdi",
      salary: "45000-55000",
      description:
        "Nous recherchons un développeur full-stack expérimenté pour rejoindre notre équipe dynamique. Vous travaillerez sur des projets innovants utilisant les dernières technologies web.",
      priority: "normal",
      deadline: "2024-04-15",
      createdAt: new Date(),
    }
    displayJobInfo()
  }
}

// Afficher les informations du job
function displayJobInfo() {
  if (!currentJob) return

  // Informations principales
  document.getElementById("jobTitle").textContent = currentJob.title
  document.getElementById("jobDepartment").textContent = getDepartmentName(currentJob.departmentId)
  document.getElementById("jobDescription").textContent = currentJob.description

  // Badges
  document.getElementById("jobType").textContent = currentJob.type.toUpperCase()

  const priorityElement = document.getElementById("jobPriority")
  priorityElement.textContent = currentJob.priority
  priorityElement.className = `job-badge priority ${currentJob.priority}`

  // Salaire
  document.getElementById("jobSalary").textContent = currentJob.salary ? `€ ${currentJob.salary}` : "Non spécifié"

  // Détails
  document.getElementById("contractType").textContent = currentJob.type.toUpperCase()
  document.getElementById("jobDeadline").textContent = currentJob.deadline
    ? new Date(currentJob.deadline).toLocaleDateString("fr-FR")
    : "Non définie"
  document.getElementById("jobCreated").textContent = new Date(currentJob.createdAt).toLocaleDateString("fr-FR")

  // Employé assigné
  const assignedEmployee = getAssignedEmployee(currentJob.id)
  document.getElementById("assignedEmployee").textContent = assignedEmployee || "Non assigné"

  // Statistiques simulées
  document.getElementById("jobViews").textContent = Math.floor(Math.random() * 500) + 100
  document.getElementById("jobApplications").textContent = applications.length

  // Calculer les jours restants
  if (currentJob.deadline) {
    const deadline = new Date(currentJob.deadline)
    const today = new Date()
    const daysRemaining = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24))
    document.getElementById("daysRemaining").textContent = Math.max(0, daysRemaining)
  }

  // Taux de conversion simulé
  document.getElementById("conversionRate").textContent = (Math.random() * 10).toFixed(1) + "%"
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

// Obtenir l'employé assigné (simulé)
function getAssignedEmployee(jobId) {
  // Simulation - dans une vraie app, ceci viendrait de la base de données
  const employees = ["Marie Dubois", "Pierre Martin", "Sophie Laurent", "Thomas Durand"]
  return Math.random() > 0.5 ? employees[Math.floor(Math.random() * employees.length)] : null
}

// Charger les candidatures
function loadApplications() {
  // Candidatures simulées
  applications = [
    {
      id: 1,
      name: "Marie Dubois",
      email: "marie.dubois@email.com",
      status: "pending",
      appliedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
    },
    {
      id: 2,
      name: "Pierre Martin",
      email: "pierre.martin@email.com",
      status: "reviewed",
      appliedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
    },
    {
      id: 3,
      name: "Sophie Laurent",
      email: "sophie.laurent@email.com",
      status: "accepted",
      appliedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
    },
    {
      id: 4,
      name: "Thomas Durand",
      email: "thomas.durand@email.com",
      status: "pending",
      appliedAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000),
    },
  ]
}

// Rendre les compétences
function renderSkills() {
  const skillsContainer = document.getElementById("requiredSkills")
  skillsContainer.innerHTML = requiredSkills.map((skill) => `<div class="skill-tag">${skill}</div>`).join("")
}

// Rendre les candidatures
function renderApplications(filter = "all") {
  const container = document.getElementById("applicationsList")

  let filteredApplications = applications
  if (filter !== "all") {
    filteredApplications = applications.filter((app) => app.status === filter)
  }

  if (filteredApplications.length === 0) {
    container.innerHTML = `
            <div class="empty-state">
                <p>Aucune candidature ${filter === "all" ? "" : filter}</p>
            </div>
        `
    return
  }

  container.innerHTML = filteredApplications
    .map(
      (app) => `
        <div class="application-item">
            <div class="applicant-avatar">${app.name
              .split(" ")
              .map((n) => n[0])
              .join("")}</div>
            <div class="applicant-info">
                <div class="applicant-name">${app.name}</div>
                <div class="applicant-email">${app.email}</div>
            </div>
            <div class="application-status ${app.status}">
                ${getStatusText(app.status)}
            </div>
        </div>
    `,
    )
    .join("")
}

// Obtenir le texte du statut
function getStatusText(status) {
  const statusTexts = {
    pending: "En attente",
    reviewed: "Examinée",
    accepted: "Acceptée",
    rejected: "Rejetée",
  }
  return statusTexts[status] || status
}

// Rendre la timeline
function renderTimeline() {
  const timeline = document.getElementById("jobTimeline")
  const timelineItems = [
    {
      icon: "fa-plus",
      title: "Poste créé",
      description: "Le poste a été publié et est maintenant visible",
      date: "Aujourd'hui",
    },
    {
      icon: "fa-eye",
      title: "Première vue",
      description: "Le poste a reçu sa première consultation",
      date: "Il y a 2 heures",
    },
    {
      icon: "fa-file-alt",
      title: "Première candidature",
      description: "Marie Dubois a postulé pour ce poste",
      date: "Il y a 1 jour",
    },
  ]

  timeline.innerHTML = timelineItems
    .map(
      (item) => `
        <div class="timeline-item">
            <div class="timeline-icon"><i class="fas ${item.icon}"></i></div>
            <div class="timeline-content">
                <h4>${item.title}</h4>
                <p>${item.description}</p>
                <span class="timeline-date">${item.date}</span>
            </div>
        </div>
    `,
    )
    .join("")
}

// Fonctions pour les actions
function editJob() {
  showNotification("Fonction de modification en cours de développement", "info")
}

function shareJob() {
  if (navigator.share) {
    navigator
      .share({
        title: currentJob.title,
        text: `Découvrez cette offre d'emploi: ${currentJob.title}`,
        url: window.location.href,
      })
      .then(() => {
        showNotification("Poste partagé avec succès !", "success")
      })
      .catch(() => {
        fallbackShare()
      })
  } else {
    fallbackShare()
  }
}

function fallbackShare() {
  const url = window.location.href
  navigator.clipboard
    .writeText(url)
    .then(() => {
      showNotification("Lien copié dans le presse-papiers !", "success")
    })
    .catch(() => {
      showNotification("Impossible de copier le lien", "error")
    })
}

function closeJob() {
  if (confirm("Êtes-vous sûr de vouloir fermer ce poste ?")) {
    showNotification("Poste fermé avec succès", "success")
    setTimeout(() => {
      window.close()
    }, 2000)
  }
}

// Filtrer les candidatures
function filterApplications(filter) {
  // Mettre à jour les boutons actifs
  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.classList.remove("active")
  })
  event.target.classList.add("active")

  renderApplications(filter)
}

// Gestion des compétences
function addRequiredSkill() {
  document.getElementById("skillModal").classList.add("show")
  document.body.style.overflow = "hidden"
}

function closeSkillModal() {
  document.getElementById("skillModal").classList.remove("show")
  document.body.style.overflow = "auto"
  document.getElementById("skillForm").reset()
}

function saveSkill() {
  const skillName = document.getElementById("skillName").value.trim()

  if (!skillName) {
    showNotification("Veuillez saisir une compétence", "error")
    return
  }

  if (requiredSkills.includes(skillName)) {
    showNotification("Cette compétence existe déjà", "warning")
    return
  }

  requiredSkills.push(skillName)
  renderSkills()
  closeSkillModal()
  showNotification("Compétence ajoutée avec succès !", "success")
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

    .empty-state {
        text-align: center;
        padding: 2rem;
        color: #7f8c8d;
        font-style: italic;
    }
`
document.head.appendChild(style)
