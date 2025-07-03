// Variables globales
let currentJob = null
let applications = []

// Charger les données du job au chargement de la page
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 Page job-details chargée")
  loadJobData()
})

// Charger les données du job depuis localStorage ou URL
function loadJobData() {
  console.log("📊 Début chargement des données")

  // Essayer de récupérer l'ID depuis l'URL
  const urlParams = new URLSearchParams(window.location.search)
  const jobId = urlParams.get("id")

  console.log("🔍 Job ID depuis URL:", jobId)

  if (jobId) {
    // Charger depuis l'API
    console.log("🌐 Chargement depuis API")
    loadJobFromAPI(jobId)
  } else {
    // Essayer localStorage
    console.log("💾 Tentative chargement depuis localStorage")
    const jobData = localStorage.getItem("selectedJob")
    if (jobData) {
      try {
        currentJob = JSON.parse(jobData)
        console.log("✅ Données chargées depuis localStorage:", currentJob)
        displayJobInfo()
        renderApplications()
      } catch (error) {
        console.error("❌ Erreur parsing localStorage:", error)
        showError("Erreur lors du chargement des données du poste")
      }
    } else {
      console.log("❌ Aucune donnée trouvée")
      showError("Aucun poste sélectionné. Veuillez retourner au dashboard et sélectionner un poste.")
    }
  }
}

// Charger le job depuis l'API
async function loadJobFromAPI(jobId) {
  try {
    console.log(`🔄 Chargement job ID: ${jobId}`)
    showLoading("Chargement des détails du poste...")

    const response = await fetch(`/api/job/${jobId}`)
    console.log("📡 Réponse API:", response.status)

    if (response.ok) {
      const result = await response.json()
      console.log("📦 Données reçues:", result)

      if (result.success) {
        currentJob = result.job
        applications = result.job.applications || []

        console.log("✅ Job chargé:", currentJob.title)
        console.log("👥 Candidatures:", applications.length)

        // Masquer le loading et afficher les données
        hideLoading()
        displayJobInfo()
        renderApplications()
      } else {
        console.error("❌ Erreur API:", result.message)
        showError(result.message || "Erreur lors du chargement du poste")
      }
    } else {
      console.error("❌ Erreur HTTP:", response.status)
      showError("Erreur de connexion au serveur")
    }
  } catch (error) {
    console.error("❌ Erreur critique:", error)
    showError("Erreur lors du chargement des données")
  }
}

// Masquer le loading
function hideLoading() {
  const loadingOverlay = document.querySelector(".loading-overlay")
  if (loadingOverlay) {
    loadingOverlay.remove()
  }
}

// Afficher les informations du job
function displayJobInfo() {
  if (!currentJob) {
    console.error("❌ Aucun job à afficher")
    return
  }

  console.log("🎨 Affichage des informations du job")
  console.log("📋 Données du job:", currentJob)

  try {
    // Vérifier et afficher les informations principales
    const titleElement = document.getElementById("jobTitle")
    if (titleElement) {
      titleElement.textContent = currentJob.title || "Titre non disponible"
      console.log("✅ Titre affiché:", currentJob.title)
    } else {
      console.warn("⚠️ Element jobTitle non trouvé dans le DOM")
    }

    const departmentElement = document.getElementById("jobDepartment")
    if (departmentElement) {
      departmentElement.textContent = currentJob.department_name || "Département non spécifié"
      console.log("✅ Département affiché:", currentJob.department_name)
    } else {
      console.warn("⚠️ Element jobDepartment non trouvé dans le DOM")
    }

    const descriptionElement = document.getElementById("jobDescription")
    if (descriptionElement) {
      descriptionElement.textContent = currentJob.description || "Description non disponible"
      console.log("✅ Description affichée")
    } else {
      console.warn("⚠️ Element jobDescription non trouvé dans le DOM")
    }

    // Responsabilités
    const responsibilitiesElement = document.getElementById("jobResponsibilities")
    if (responsibilitiesElement) {
      responsibilitiesElement.textContent = currentJob.responsibilities || "Aucune responsabilité spécifiée"
      console.log("✅ Responsabilités affichées")
    } else {
      console.warn("⚠️ Element jobResponsibilities non trouvé dans le DOM")
    }

    // Meta informations
    const typeElement = document.getElementById("jobType")
    if (typeElement) {
      typeElement.textContent = (currentJob.employment_type || "").toUpperCase()
    } else {
      console.warn("⚠️ Element jobType non trouvé")
    }

    const priorityElement = document.getElementById("jobPriority")
    if (priorityElement) {
      priorityElement.textContent = (currentJob.priority || "").toUpperCase()
    } else {
      console.warn("⚠️ Element jobPriority non trouvé")
    }

    const deadlineElement = document.getElementById("jobDeadline")
    if (deadlineElement) {
      deadlineElement.textContent = currentJob.deadline
        ? new Date(currentJob.deadline).toLocaleDateString("fr-FR")
        : "Non définie"
    } else {
      console.warn("⚠️ Element jobDeadline non trouvé")
    }

    // Statut
    const statusElement = document.getElementById("jobStatus")
    if (statusElement) {
      statusElement.textContent = (currentJob.status || "").toUpperCase()
      statusElement.className = `status-badge ${currentJob.status || "draft"}`
    } else {
      console.warn("⚠️ Element jobStatus non trouvé")
    }

    // Salaire
    const salaryElement = document.getElementById("jobSalary")
    if (salaryElement) {
      let salaryText = "Non spécifié"
      if (currentJob.salary_min && currentJob.salary_max) {
        salaryText = `€ ${currentJob.salary_min} - ${currentJob.salary_max}`
      } else if (currentJob.salary_min) {
        salaryText = `€ ${currentJob.salary_min}+`
      }
      salaryElement.textContent = salaryText
    } else {
      console.warn("⚠️ Element jobSalary non trouvé")
    }

    // Détails
    const contractTypeElement = document.getElementById("contractType")
    if (contractTypeElement) {
      contractTypeElement.textContent = (currentJob.employment_type || "").toUpperCase()
    } else {
      console.warn("⚠️ Element contractType non trouvé")
    }

    const jobCreatedElement = document.getElementById("jobCreated")
    if (jobCreatedElement) {
      jobCreatedElement.textContent = new Date(currentJob.created_at).toLocaleDateString("fr-FR")
    } else {
      console.warn("⚠️ Element jobCreated non trouvé")
    }

    const assignedEmployeeElement = document.getElementById("assignedEmployee")
    if (assignedEmployeeElement) {
      assignedEmployeeElement.textContent = currentJob.assigned_employee_name || "Non assigné"
    } else {
      console.warn("⚠️ Element assignedEmployee non trouvé")
    }

    // Statistiques réelles
    const applicationsElement = document.getElementById("jobApplications")
    if (applicationsElement) {
      applicationsElement.textContent = currentJob.applications_count || 0
    } else {
      console.warn("⚠️ Element jobApplications non trouvé")
    }

    const daysRemainingElement = document.getElementById("daysRemaining")
    if (daysRemainingElement) {
      if (currentJob.days_remaining !== null && currentJob.days_remaining !== undefined) {
        daysRemainingElement.textContent = currentJob.days_remaining
      } else {
        daysRemainingElement.textContent = "--"
      }
    } else {
      console.warn("⚠️ Element daysRemaining non trouvé")
    }

    console.log("✅ Informations affichées avec succès")
  } catch (error) {
    console.error("❌ Erreur lors de l'affichage:", error)
    showError("Erreur lors de l'affichage des données")
  }
}

// Fonction pour retourner au dashboard
function goBackToDashboard() {
  console.log("🔙 Retour au dashboard")
  window.location.href = "/dashboard"
}

// Rendre les candidatures
function renderApplications(filter = "all") {
  console.log(`👥 Rendu des candidatures (filtre: ${filter})`)

  const container = document.getElementById("applicationsList")
  if (!container) {
    console.error("❌ Container applicationsList non trouvé")
    return
  }

  let filteredApplications = applications
  if (filter !== "all") {
    filteredApplications = applications.filter((app) => app.status === filter)
  }

  console.log(`📊 ${filteredApplications.length} candidatures à afficher`)

  if (filteredApplications.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-inbox"></i>
        <h4>Aucune candidature ${filter === "all" ? "" : filter}</h4>
        <p>Les candidatures apparaîtront ici une fois soumises.</p>
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
            <div class="applicant-title">${app.title || "Candidat"}</div>
            <div class="application-date">
              Candidature: ${new Date(app.application_date).toLocaleDateString("fr-FR")}
            </div>
            ${app.hr_rating ? `<div class="hr-rating">Note HR: ${app.hr_rating}/5 ⭐</div>` : ""}
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
    interview_scheduled: "Entretien programmé",
    interview_completed: "Entretien terminé",
    accepted: "Acceptée",
    rejected: "Rejetée",
    withdrawn: "Retirée",
  }
  return statusTexts[status] || status
}

// Fonctions pour les actions
function editJob() {
  showNotification("Fonction de modification en cours de développement", "info")
}

function shareJob() {
  if (!currentJob) {
    showNotification("Aucun poste à partager", "error")
    return
  }

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
      goBackToDashboard()
    }, 2000)
  }
}

// Filtrer les candidatures
function filterApplications(filter) {
  console.log(`🔍 Filtrage: ${filter}`)

  // Mettre à jour les boutons actifs
  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.classList.remove("active")
  })

  // Trouver le bouton cliqué et l'activer
  const clickedBtn = Array.from(document.querySelectorAll(".filter-btn")).find((btn) =>
    btn.textContent.toLowerCase().includes(filter === "all" ? "toutes" : filter),
  )
  if (clickedBtn) {
    clickedBtn.classList.add("active")
  }

  renderApplications(filter)
}

// Fonctions utilitaires
function showLoading(message) {
  console.log("⏳ Affichage loading:", message)

  // Supprimer le loading existant
  hideLoading()

  const loadingHTML = `
    <div class="loading-overlay">
      <div class="loading-content">
        <i class="fas fa-spinner fa-spin"></i>
        <p>${message}</p>
      </div>
    </div>
  `
  document.body.insertAdjacentHTML("beforeend", loadingHTML)
}

function showError(message) {
  console.log("❌ Affichage erreur:", message)

  const errorHTML = `
    <div class="error-overlay">
      <div class="error-content">
        <i class="fas fa-exclamation-triangle"></i>
        <h2>Erreur</h2>
        <p>${message}</p>
        <button onclick="goBackToDashboard()" class="btn-primary">
          <i class="fas fa-arrow-left"></i> Retour au Dashboard
        </button>
      </div>
    </div>
  `
  document.body.innerHTML = errorHTML
}

// Système de notifications
function showNotification(message, type = "info") {
  console.log(`📢 Notification ${type}:`, message)

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

// Gestion des événements globaux
document.addEventListener("click", (e) => {
  // Gestion des boutons de filtre
  if (e.target.classList.contains("filter-btn")) {
    const filterText = e.target.textContent.toLowerCase()
    let filter = "all"

    if (filterText.includes("attente")) filter = "pending"
    else if (filterText.includes("examinées")) filter = "reviewed"
    else if (filterText.includes("acceptées")) filter = "accepted"

    filterApplications(filter)
  }
})

console.log("✅ Script job-details.js chargé complètement")
