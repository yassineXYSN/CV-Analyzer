// Variables globales
let currentJob = null
let applications = []
let allCandidates = []

// Charger les données du job au chargement de la page
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 Page job-details chargée")
  loadJobData()
  loadAllCandidates()
})

// Charger tous les candidats disponibles
async function loadAllCandidates() {
  try {
    console.log("👥 Chargement de tous les candidats")

    // Simuler des candidats pour la démo (en production, récupérer depuis l'API)
    allCandidates = [
      {
        id: 1,
        name: "Marie Dubois",
        title: "Développeuse Full-Stack",
        email: "marie.dubois@email.com",
        skills: ["React", "Node.js", "Python"],
        experience: "3 ans",
      },
      {
        id: 2,
        name: "Pierre Martin",
        title: "Designer UX/UI",
        email: "pierre.martin@email.com",
        skills: ["Figma", "Adobe XD", "Sketch"],
        experience: "5 ans",
      },
      {
        id: 3,
        name: "Sophie Laurent",
        title: "Data Scientist",
        email: "sophie.laurent@email.com",
        skills: ["Python", "R", "Machine Learning"],
        experience: "4 ans",
      },
    ]

    console.log(`✅ ${allCandidates.length} candidats chargés`)
  } catch (error) {
    console.error("❌ Erreur chargement candidats:", error)
  }
}

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
    }

    const departmentElement = document.getElementById("jobDepartment")
    if (departmentElement) {
      departmentElement.textContent = currentJob.department_name || "Département non spécifié"
      console.log("✅ Département affiché:", currentJob.department_name)
    }

    const descriptionElement = document.getElementById("jobDescription")
    if (descriptionElement) {
      descriptionElement.textContent = currentJob.description || "Description non disponible"
      console.log("✅ Description affichée")
    }

    // Responsabilités
    const responsibilitiesElement = document.getElementById("jobResponsibilities")
    if (responsibilitiesElement) {
      responsibilitiesElement.textContent = currentJob.responsibilities || "Aucune responsabilité spécifiée"
      console.log("✅ Responsabilités affichées")
    }

    // Meta informations
    const typeElement = document.getElementById("jobType")
    if (typeElement) {
      typeElement.textContent = (currentJob.employment_type || "").toUpperCase()
    }

    const priorityElement = document.getElementById("jobPriority")
    if (priorityElement) {
      priorityElement.textContent = (currentJob.priority || "").toUpperCase()
    }

    const deadlineElement = document.getElementById("jobDeadline")
    if (deadlineElement) {
      deadlineElement.textContent = currentJob.deadline
        ? new Date(currentJob.deadline).toLocaleDateString("fr-FR")
        : "Non définie"
    }

    // Statut
    const statusElement = document.getElementById("jobStatus")
    if (statusElement) {
      statusElement.textContent = (currentJob.status || "").toUpperCase()
      statusElement.className = `status-badge ${currentJob.status || "draft"}`
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
    }

    // Détails
    const contractTypeElement = document.getElementById("contractType")
    if (contractTypeElement) {
      contractTypeElement.textContent = (currentJob.employment_type || "").toUpperCase()
    }

    const jobCreatedElement = document.getElementById("jobCreated")
    if (jobCreatedElement) {
      jobCreatedElement.textContent = new Date(currentJob.created_at).toLocaleDateString("fr-FR")
    }

    const assignedEmployeeElement = document.getElementById("assignedEmployee")
    if (assignedEmployeeElement) {
      assignedEmployeeElement.textContent = currentJob.assigned_employee_name || "Non assigné"
    }

    // Statistiques réelles
    const applicationsElement = document.getElementById("jobApplications")
    if (applicationsElement) {
      applicationsElement.textContent = currentJob.applications_count || 0
    }

    const daysRemainingElement = document.getElementById("daysRemaining")
    if (daysRemainingElement) {
      if (currentJob.days_remaining !== null && currentJob.days_remaining !== undefined) {
        daysRemainingElement.textContent = currentJob.days_remaining
      } else {
        daysRemainingElement.textContent = "--"
      }
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

// Rendre les candidatures avec actions de gestion
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
        <div class="application-item-detailed">
          <div class="candidate-info">
            <div class="candidate-avatar">${app.name
              .split(" ")
              .map((n) => n[0])
              .join("")}</div>
            <div class="candidate-details">
              <div class="candidate-name">${app.name}</div>
              <div class="candidate-title">${app.title || "Candidat"}</div>
              <div class="candidate-meta">
                <span class="application-date">
                  Candidature: ${new Date(app.application_date).toLocaleDateString("fr-FR")}
                </span>
                ${app.hr_rating ? `<span class="hr-rating">Note HR: ${app.hr_rating}/5 ⭐</span>` : ""}
              </div>
            </div>
          </div>
          <div class="application-status-section">
            <div class="status-badge ${app.status}">
              ${getStatusText(app.status)}
            </div>
            <div class="application-actions">
              ${renderCandidateActions(app)}
            </div>
          </div>
        </div>
      `,
    )
    .join("")
}

// Rendre les actions pour chaque candidat
function renderCandidateActions(app) {
  if (app.status === "pending") {
    return `
      <button class="btn-action review" onclick="updateApplicationStatus(${app.id}, 'reviewed')">
        <i class="fas fa-eye"></i> Examiner
      </button>
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${app.name}', '${currentJob.title}', '${currentJob.department_name}')">
        <i class="fas fa-check"></i> Accepter
      </button>
      <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${app.name}', '${currentJob.title}')">
        <i class="fas fa-times"></i> Rejeter
      </button>
    `
  } else if (app.status === "reviewed") {
    return `
      <button class="btn-action schedule" onclick="updateApplicationStatus(${app.id}, 'interview_scheduled')">
        <i class="fas fa-calendar"></i> Programmer entretien
      </button>
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${app.name}', '${currentJob.title}', '${currentJob.department_name}')">
        <i class="fas fa-check-circle"></i> Accepter
      </button>
      <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${app.name}', '${currentJob.title}')">
        <i class="fas fa-times"></i> Rejeter
      </button>
    `
  } else if (app.status === "interview_scheduled") {
    return `
      <button class="btn-action complete" onclick="updateApplicationStatus(${app.id}, 'reviewed')">
        <i class="fas fa-check-double"></i> Entretien terminé
      </button>
      <button class="btn-action accept" onclick="showAcceptConfirmation(${app.id}, '${app.name}', '${currentJob.title}', '${currentJob.department_name}')">
        <i class="fas fa-user-check"></i> Accepter
      </button>
      <button class="btn-action reject" onclick="showRejectConfirmation(${app.id}, '${app.name}', '${currentJob.title}')">
        <i class="fas fa-times"></i> Rejeter
      </button>
    `
  } else {
      return `
        <button class="btn-action info" onclick="viewCandidateProfile(${app.candidate_id})">
          <i class="fas fa-info-circle"></i> Voir profil
        </button>
    `
  }
}

// Afficher les candidats disponibles
function showAvailableCandidates() {
  console.log("👥 Affichage candidats disponibles")

  const container = document.getElementById("availableCandidates")
  if (!container) return

  // Filtrer les candidats qui n'ont pas encore candidaté pour ce poste
  const appliedCandidateIds = applications.map((app) => app.candidate_id)
  const availableCandidates = allCandidates.filter((candidate) => !appliedCandidateIds.includes(candidate.id))

  if (availableCandidates.length === 0) {
    container.innerHTML = `
      <div class="no-candidates">
        <p>Tous les candidats disponibles ont déjà candidaté pour ce poste.</p>
      </div>
    `
  } else {
    container.innerHTML = availableCandidates
      .map(
        (candidate) => `
      <div class="available-candidate">
        <div class="candidate-info">
          <div class="candidate-avatar">${candidate.name
            .split(" ")
            .map((n) => n[0])
            .join("")}</div>
          <div class="candidate-details">
            <h4>${candidate.name}</h4>
            <p>${candidate.title}</p>
            <div class="candidate-skills">
              ${candidate.skills.map((skill) => `<span class="skill-tag">${skill}</span>`).join("")}
            </div>
            <small>${candidate.experience} d'expérience</small>
          </div>
        </div>
        <div class="candidate-actions">
          <button class="btn-secondary" onclick="viewCandidateProfile(${candidate.id})">
            <i class="fas fa-eye"></i> Voir profil
          </button>
          <button class="btn-primary" onclick="addCandidateToJob(${candidate.id})">
            <i class="fas fa-plus"></i> Ajouter au poste
          </button>
        </div>
      </div>
    `,
      )
      .join("")
  }

  container.style.display = container.style.display === "none" ? "block" : "none"
}

// Ajouter un candidat au poste
async function addCandidateToJob(candidateId) {
  console.log(`➕ Ajout candidat ${candidateId} au poste ${currentJob.id}`)

  try {
    // Simuler l'ajout (en production, appeler l'API)
    const candidate = allCandidates.find((c) => c.id === candidateId)
    if (!candidate) return

    const newApplication = {
      id: Date.now(), // ID temporaire
      candidate_id: candidateId,
      name: candidate.name,
      title: candidate.title,
      status: "pending",
      application_date: new Date().toISOString(),
      hr_rating: null,
      hr_notes: null,
    }

    applications.push(newApplication)

    showNotification(`${candidate.name} a été ajouté(e) aux candidatures pour ce poste`, "success")

    // Rafraîchir l'affichage
    renderApplications()
    showAvailableCandidates() // Rafraîchir la liste des candidats disponibles
  } catch (error) {
    console.error("❌ Erreur ajout candidat:", error)
    showNotification("Erreur lors de l'ajout du candidat", "error")
  }
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

// Fonction pour afficher la modal de confirmation d'acceptation
function showAcceptConfirmation(applicationId, candidateName, jobTitle, departmentName) {
  console.log(`🎉 Affichage confirmation acceptation pour ${candidateName}`)

  const modal = document.createElement("div")
  modal.className = "modal-overlay"

  modal.innerHTML = `
    <div class="confirmation-modal">
      <div class="modal-content">
        <div class="modal-header">
          <div class="confirmation-icon accept">
            <i class="fas fa-user-check"></i>
          </div>
          <h3>Confirmer l'acceptation</h3>
          <p>Accepter la candidature de <strong>${candidateName}</strong></p>
        </div>
        
        <div class="candidate-modal-info">
          <div class="candidate-modal-avatar">${candidateName
            .split(" ")
            .map((n) => n[0])
            .join("")}</div>
          <div class="candidate-modal-details">
            <h4>${candidateName}</h4>
            <p>Poste: ${jobTitle} - ${departmentName}</p>
          </div>
        </div>
        
        <div class="modal-body">
          <p><strong>Actions automatiques qui seront effectuées :</strong></p>
          <div class="confirmation-details">
            <ul class="confirmation-list">
              <li><i class="fas fa-user-plus"></i> Création automatique de l'employé dans le système</li>
              <li><i class="fas fa-briefcase"></i> Attribution du poste "${jobTitle}" à l'employé</li>
              <li><i class="fas fa-building"></i> Assignation au département "${departmentName}"</li>
              <li><i class="fas fa-check-circle"></i> Marquage du poste comme pourvu</li>
              <li><i class="fas fa-times-circle"></i> Rejet automatique des autres candidatures</li>
              <li><i class="fas fa-calendar-check"></i> Date d'embauche fixée à aujourd'hui</li>
            </ul>
          </div>
          <div class="warning-note">
            <i class="fas fa-exclamation-triangle"></i>
            <p>Cette action est irréversible et modifiera définitivement le statut du poste.</p>
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="btn-confirm" onclick="confirmAcceptApplication(${applicationId})">
            <i class="fas fa-check"></i> Confirmer l'acceptation
          </button>
          <button class="btn-cancel" onclick="closeConfirmationModal()">
            <i class="fas fa-times"></i> Annuler
          </button>
        </div>
      </div>
    </div>
  `

  document.body.appendChild(modal)

  // Animation d'entrée
  requestAnimationFrame(() => {
    modal.style.opacity = "1"
  })

  // Fermer la modal en cliquant à l'extérieur
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeConfirmationModal()
    }
  })

  // Fermer avec Escape
  document.addEventListener("keydown", handleEscapeKey)
}

// Fonction pour afficher la modal de confirmation de rejet
function showRejectConfirmation(applicationId, candidateName, jobTitle) {
  console.log(`❌ Affichage confirmation rejet pour ${candidateName}`)

  const modal = document.createElement("div")
  modal.className = "modal-overlay"

  modal.innerHTML = `
    <div class="confirmation-modal">
      <div class="modal-content">
        <div class="modal-header">
          <div class="confirmation-icon reject">
            <i class="fas fa-user-times"></i>
          </div>
          <h3>Confirmer le rejet</h3>
          <p>Rejeter la candidature de <strong>${candidateName}</strong></p>
        </div>
        
        <div class="candidate-modal-info">
          <div class="candidate-modal-avatar">${candidateName
            .split(" ")
            .map((n) => n[0])
            .join("")}</div>
          <div class="candidate-modal-details">
            <h4>${candidateName}</h4>
            <p>Poste: ${jobTitle}</p>
          </div>
        </div>
        
        <div class="modal-body">
          <p><strong>Conséquences du rejet :</strong></p>
          <div class="confirmation-details">
            <ul class="confirmation-list">
              <li><i class="fas fa-times-circle"></i> La candidature sera marquée comme rejetée</li>
              <li><i class="fas fa-envelope"></i> Le candidat sera notifié automatiquement</li>
              <li><i class="fas fa-archive"></i> Le dossier sera archivé dans l'historique</li>
              <li><i class="fas fa-ban"></i> Le candidat ne pourra plus postuler pour ce poste</li>
            </ul>
          </div>
          <div class="warning-note">
            <i class="fas fa-exclamation-triangle"></i>
            <p>Cette action est définitive. Le candidat sera informé du rejet de sa candidature.</p>
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="btn-confirm reject" onclick="confirmRejectApplication(${applicationId})">
            <i class="fas fa-times"></i> Confirmer le rejet
          </button>
          <button class="btn-cancel" onclick="closeConfirmationModal()">
            <i class="fas fa-arrow-left"></i> Annuler
          </button>
        </div>
      </div>
    </div>
  `

  document.body.appendChild(modal)

  // Animation d'entrée
  requestAnimationFrame(() => {
    modal.style.opacity = "1"
  })

  // Fermer la modal en cliquant à l'extérieur
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeConfirmationModal()
    }
  })

  // Fermer avec Escape
  document.addEventListener("keydown", handleEscapeKey)
}

// Fonction pour gérer la touche Escape
function handleEscapeKey(e) {
  if (e.key === "Escape") {
    closeConfirmationModal()
  }
}

// Fonction pour fermer la modal de confirmation avec animation
function closeConfirmationModal() {
  const modal = document.querySelector(".modal-overlay")
  if (modal) {
    // Animation de sortie
    modal.classList.add("closing")
    modal.querySelector(".confirmation-modal").classList.add("closing")

    setTimeout(() => {
      modal.remove()
      document.removeEventListener("keydown", handleEscapeKey)
    }, 300)
  }
}

// Fonction pour confirmer l'acceptation - CORRIGÉE
async function confirmAcceptApplication(applicationId) {
  try {
    closeConfirmationModal()
    showLoading("Traitement de l'acceptation...")

    const response = await fetch(`/api/accept-application/${applicationId}`, {
      method: "POST",
    })

    const result = await response.json()
    hideLoading()

    if (response.ok && result.success) {
      showNotification(result.message || "Candidat accepté avec succès", "success")
      loadJobData()  // Mise à jour de l'affichage
    } else {
      // ✅ Affichage du message d'erreur retourné
      console.warn("Erreur renvoyée:", result)
      showNotification(result.message || "Erreur lors de l'acceptation", "error")
    }

  } catch (error) {
    console.error("❌ Erreur réseau ou système:", error)
    hideLoading()
    showNotification("Erreur inattendue lors de la communication avec le serveur", "error")
  }
}


// Fonction pour confirmer le rejet
async function confirmRejectApplication(applicationId) {
  console.log(`❌ Confirmation rejet candidature ${applicationId}`)

  try {
    closeConfirmationModal()
    showLoading("Traitement du rejet...")

    const response = await fetch(`/api/applications/${applicationId}/update-status`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        status: "rejected",
        hr_notes: "Candidature rejetée via la page détails du poste",
      }),
    })

    const result = await response.json()
    hideLoading()

    if (result.success) {
      console.log("❌ Candidature rejetée avec succès")
      showNotification(result.message || "Candidature rejetée", "success")

      // Recharger les données du poste
      if (currentJob && currentJob.id) {
        await loadJobFromAPI(currentJob.id)
      }

      console.log("✅ Données rechargées après rejet")
    } else {
      console.error("❌ Erreur rejet candidature:", result.message)
      showNotification(result.message, "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ Erreur réseau rejet candidature:", error)
    showNotification("Erreur de connexion lors du rejet", "error")
  }
}

// Fonction pour mettre à jour le statut d'une candidature
async function updateApplicationStatus(applicationId, newStatus) {
  console.log(`📝 Mise à jour statut candidature ${applicationId} vers ${newStatus}`)

  try {
    const response = await fetch(`/api/applications/${applicationId}/update-status`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        status: newStatus,
      }),
    })

    const result = await response.json()

    if (result.success) {
      console.log(`✅ Statut mis à jour vers ${newStatus}`)
      showNotification(result.message, "success")

      // Recharger les candidatures
      if (currentJob && currentJob.id) {
        await loadJobFromAPI(currentJob.id)
      }
    } else {
      console.error("❌ Erreur mise à jour statut:", result.message)
      showNotification(result.message, "error")
    }
  } catch (error) {
    console.error("❌ Erreur réseau mise à jour statut:", error)
    showNotification("Erreur de connexion", "error")
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

function viewCandidateProfile(candidateId) {
  console.log(`👤 Voir profil candidat ${candidateId}`)
  window.open(`/employee-profile?candidate_id=${candidateId}`, "_blank")
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

