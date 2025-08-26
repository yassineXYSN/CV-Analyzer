// Enhanced Job Details with Original Layout + AI Compatibility
// Based on load-current-user.tsx with AI compatibility features

// Variables globales
let currentJob = null
let applications = []
let currentUser = null
const filteredApplications = []

// Initialize the page
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 Initialisation de la page détails du poste")
  loadJobFromAPI()
})

async function loadJobFromAPI() {
  const urlParams = new URLSearchParams(window.location.search)
  const jobId = urlParams.get("id")

  if (!jobId) {
    showError("ID du poste manquant dans l'URL")
    return
  }

  try {
    showLoading("Chargement des données du poste...")

    // Load job data
    const response = await fetch(`/api/job/${jobId}`)
    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        currentJob = result.job
        applications = result.job.applications || []

        console.log("✅ Poste chargé:", currentJob.title)
        console.log("👥 Candidatures:", applications.length)

        // Try to load applications from alternative endpoints if none found
        if (applications.length === 0) {
          console.log("🔍 Tentative de chargement des candidatures depuis d'autres endpoints...")
          await loadApplicationsFromAlternativeEndpoints(jobId)
        }

        await calculateCompatibilityForApplications()

        hideLoading()
        displayJobInfo()
        renderApplicationsWithOriginalLayout()
        updateCompatibilityStats()
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
    hideLoading()
    showError("Erreur lors du chargement des données")
  }
}

async function loadApplicationsFromAlternativeEndpoints(jobId) {
  const endpoints = [
    `/api/applications?job_id=${jobId}`,
    `/api/applications/job/${jobId}`,
    `/api/job/${jobId}/applications`,
  ]

  for (const endpoint of endpoints) {
    try {
      console.log(`🔍 Tentative: ${endpoint}`)
      const response = await fetch(endpoint)
      if (response.ok) {
        const result = await response.json()
        if (result.success && result.applications && result.applications.length > 0) {
          applications = result.applications
          console.log(`✅ Applications chargées depuis ${endpoint}: ${applications.length}`)
          return
        }
      }
    } catch (error) {
      console.log(`❌ Échec ${endpoint}:`, error.message)
    }
  }
}

async function calculateCompatibilityForApplications() {
  console.log("🧮 Calcul de compatibilité IA pour toutes les candidatures")

  for (let i = 0; i < applications.length; i++) {
    const app = applications[i]
    if (!app) continue

    try {
      console.log(`📊 Calcul compatibilité pour ${app.name || app.candidate_name}`)
      const response = await fetch(`/api/application/${app.id}/compatibility`)
      const result = await response.json()

      if (result.success) {
        applications[i].compatibility_percentage = result.compatibility_percentage || 0
        applications[i].compatibility_source = result.compatibility_source || "calculated"
        applications[i].compatibility_reason = result.compatibility_reason || null
        applications[i].matched_skills_count = result.matched_skills_count || 0
        applications[i].missing_skills_count = result.missing_skills_count || 0
        applications[i].total_job_skills = result.total_job_skills || 0
        applications[i].matched_skills = result.matched_skills || []
        applications[i].missing_skills = result.missing_skills || []

        console.log(
          `✅ Compatibilité calculée pour ${app.name}: ${applications[i].compatibility_percentage}% (${applications[i].compatibility_source})`,
        )
      } else {
        console.warn(`⚠️ Erreur calcul compatibilité pour ${app.name}:`, result.message)
        applications[i].compatibility_percentage = 0
        applications[i].compatibility_source = "error"
      }
    } catch (error) {
      console.error(`❌ Erreur réseau compatibilité pour ${app.name}:`, error)
      applications[i].compatibility_percentage = 0
      applications[i].compatibility_source = "error"
    }
  }

  console.log("✅ Calcul de compatibilité terminé pour toutes les candidatures")
}

// Display job information
function displayJobInfo() {
  if (!currentJob) return

  document.title = `${currentJob.title} - Détails du poste`

  // Update job header
  const jobTitle = document.getElementById("jobTitle")
  const jobDepartment = document.getElementById("jobDepartment")
  const jobLocation = document.getElementById("jobLocation")
  const jobSalary = document.getElementById("jobSalary")
  const jobDescription = document.getElementById("jobDescription")

  if (jobTitle) jobTitle.textContent = currentJob.title
  if (jobDepartment) jobDepartment.textContent = currentJob.department_name || "Département non spécifié"
  if (jobLocation) jobLocation.textContent = currentJob.location || "Lieu non spécifié"
  if (jobSalary) jobSalary.textContent = currentJob.salary_range || "Salaire non spécifié"
  if (jobDescription) jobDescription.textContent = currentJob.description || "Description non disponible"

  // Render job skills
  renderJobSkills()
}

// Render job skills
function renderJobSkills() {
  const skillsContainer = document.getElementById("jobSkills")
  if (!skillsContainer || !currentJob.skills) return

  skillsContainer.innerHTML = currentJob.skills
    .map((skill) => {
      const skillLevel = skill.skill_level || "intermediate"
      const isRequired = skill.is_required || false

      return `
        <div class="skill-tag ${skillLevel} ${isRequired ? "required" : "optional"}">
          <span class="skill-name">${skill.skill_name}</span>
          <span class="skill-level">${skillLevel.charAt(0).toUpperCase() + skillLevel.slice(1)}</span>
          ${isRequired ? '<i class="fas fa-star required-star"></i>' : ""}
        </div>
      `
    })
    .join("")
}

function renderApplicationsWithOriginalLayout(filter = "all") {
  console.log(`👥 Rendu des candidatures avec layout original (filtre: ${filter})`)

  const container = document.getElementById("applicationsList")
  if (!container) {
    console.error("❌ Container applicationsList non trouvé")
    return
  }

  let filteredApplications = applications
  if (filter !== "all") {
    filteredApplications = applications.filter((app) => app && app.status === filter)
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
    .map((app) => {
      if (!app) return ""

      const candidateName = app.name || app.candidate_name || "Candidat Anonyme"
      const candidateEmail = app.email || app.candidate_email || "Email non disponible"
      const compatibilityPercentage = app.compatibility_percentage || 0
      const compatibilitySource = app.compatibility_source || "calculated"
      const compatibilityReason = app.compatibility_reason || null

      let avatarText = "?"
      if (candidateName && candidateName !== "Candidat Anonyme") {
        try {
          avatarText = candidateName
            .split(" ")
            .map((n) => (n && n[0] ? n[0].toUpperCase() : ""))
            .join("")
            .substring(0, 2)
        } catch (e) {
          avatarText = candidateName.substring(0, 2).toUpperCase()
        }
      }

      return `
        <div class="application-card ${app.status}" data-application-id="${app.id}">
          <div class="application-header">
            <div class="candidate-info">
              <div class="candidate-avatar">${avatarText}</div>
              <div class="candidate-details">
                <h4 class="candidate-name">${candidateName}</h4>
                <p class="candidate-email">${candidateEmail}</p>
                <span class="application-status ${app.status}">${getStatusText(app.status)}</span>
              </div>
            </div>
            
            <!-- AI Compatibility Badge -->
            <div class="compatibility-badge ${getCompatibilityClass(compatibilityPercentage)}">
              <div class="compatibility-score">
                ${compatibilityPercentage}%
                <i class="fas fa-${getCompatibilityIcon(compatibilityPercentage)}"></i>
              </div>
              ${compatibilitySource === "ai" ? '<div class="ai-indicator" title="Analysé par IA">🤖 IA</div>' : ""}
            </div>
          </div>

          <!-- AI Compatibility Reason -->
          ${
            compatibilityReason
              ? `
            <div class="ai-compatibility-reason">
              <div class="ai-analysis-header">
                <i class="fas fa-robot"></i>
                <strong>Analyse IA:</strong>
              </div>
              <p class="ai-reason-text">${compatibilityReason}</p>
            </div>
          `
              : ""
          }

          <div class="compatibility-details">
            <div class="skills-summary">
              <span class="skill-stat matched">
                <i class="fas fa-check-circle"></i>
                ${app.matched_skills_count || 0} compétences correspondantes
              </span>
              <span class="skill-stat missing">
                <i class="fas fa-times-circle"></i>
                ${(app.total_job_skills || 0) - (app.matched_skills_count || 0)} manquantes
              </span>
              <span>Total: ${app.total_job_skills || 0} compétences</span>
            </div>
            
            <div class="compatibility-actions">
              <button class="btn-compatibility-details" onclick="viewCompatibilityDetails(${app.id})">
                <i class="fas fa-search"></i> Détails compatibilité
              </button>
            </div>
          </div>

          ${
            app.is_recommended && app.recommendation_comment
              ? `
            <div class="recommendation-comment">
              <i class="fas fa-comment-alt"></i>
              <strong>Commentaire de recommandation:</strong>
              <p>"${app.recommendation_comment}"</p>
              ${app.recommended_by ? `<small>— ${app.recommended_by}</small>` : ""}
            </div>
          `
              : ""
          }

          <!-- Original action buttons layout -->
          <div class="application-actions">
            ${renderCandidateActions(app)}
          </div>
        </div>
      `
    })
    .join("")
}

function renderCandidateActions(app) {
  console.log(`🎯 Rendu actions pour ${app.name}:`, {
    userRole: currentUser?.role,
    appStatus: app.status,
    isRecommended: app.is_recommended,
  })

  // For employees: only view and recommend actions
  if (currentUser?.role === "employee") {
    if (app.is_recommended) {
      return `
        <button class="btn-action info" onclick="viewCandidateProfile(${app.candidate_id})">
          <i class="fas fa-info-circle"></i> Voir profil
        </button>
        <span class="recommended-badge">
          <i class="fas fa-thumbs-up"></i> Déjà recommandé
        </span>
      `
    } else {
      return `
        <button class="btn-action info" onclick="viewCandidateProfile(${app.candidate_id})">
          <i class="fas fa-info-circle"></i> Voir profil
        </button>
        <button class="btn-action recommend" onclick="recommendCandidate(${app.id}, '${app.name}')">
          <i class="fas fa-thumbs-up"></i> Recommander
        </button>
      `
    }
  }

  // For recruiters and admins: full action buttons
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

async function viewCompatibilityDetails(applicationId) {
  console.log("🔍 Affichage détails compatibilité pour candidature:", applicationId)

  try {
    showLoading("Chargement des détails de compatibilité...")
    const response = await fetch(`/api/application/${applicationId}/compatibility`)
    const result = await response.json()
    hideLoading()

    if (result.success) {
      showDarkCompatibilityModal(result)
    } else {
      showNotification("Erreur lors du chargement des détails de compatibilité", "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ Erreur chargement détails compatibilité:", error)
    showNotification("Erreur de connexion", "error")
  }
}

function showDarkCompatibilityModal(compatibilityData) {
  const modal = document.createElement("div")
  modal.className = "modal-overlay compatibility-modal-overlay"
  modal.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(10px);
    display: flex; align-items: center; justify-content: center;
    z-index: 25000; padding: 2rem;
  `

  modal.innerHTML = `
    <div class="modal-content" style="max-width: 900px; width: 95%; max-height: 90vh; overflow-y: auto; background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%); border-radius: 20px; border: 2px solid rgba(59, 130, 246, 0.4); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);">
      <div class="modal-header" style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 2rem; border-radius: 20px 20px 0 0; border-bottom: 1px solid rgba(59, 130, 246, 0.2);">
        <h3 style="margin: 0; display: flex; align-items: center; gap: 1rem; font-size: 1.5rem;">
          <i class="fas fa-chart-pie" style="color: #3b82f6;"></i> 
          Analyse Détaillée de Compatibilité
          ${compatibilityData.compatibility_source === "ai" ? '<span style="color: #10b981; font-size: 0.9rem; margin-left: 1rem;">🤖 Analysé par IA</span>' : ""}
        </h3>
        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()" style="position: absolute; top: 2rem; right: 2rem; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); color: white; width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 1.2rem;">&times;</button>
      </div>
      
      <div class="modal-body" style="padding: 2rem; background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);">
        ${
          compatibilityData.compatibility_reason
            ? `
          <div class="ai-reasoning-section" style="margin-bottom: 2rem; padding: 1.5rem; background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05)); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px;">
            <h4 style="color: #10b981; margin: 0 0 1rem 0; display: flex; align-items: center; gap: 0.5rem;">
              <i class="fas fa-robot"></i> Analyse IA
            </h4>
            <p style="color: #f8fafc; margin: 0; line-height: 1.6; font-size: 1.1rem;">${compatibilityData.compatibility_reason}</p>
          </div>
        `
            : ""
        }
        
        <div class="compatibility-overview" style="display: grid; grid-template-columns: auto 1fr; gap: 2rem; align-items: center; margin-bottom: 2rem; padding: 2rem; background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05)); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 16px;">
          <div class="compatibility-score">
            <div class="score-circle ${getCompatibilityClass(compatibilityData.compatibility_percentage)}" style="width: 120px; height: 120px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; background: conic-gradient(${compatibilityData.compatibility_percentage >= 75 ? "#10b981" : compatibilityData.compatibility_percentage >= 50 ? "#f59e0b" : compatibilityData.compatibility_percentage >= 25 ? "#ef4444" : "#6b7280"} ${compatibilityData.compatibility_percentage * 3.6}deg, rgba(255, 255, 255, 0.1) 0deg); position: relative;">
              <div style="position: absolute; inset: 8px; background: linear-gradient(145deg, #0f172a, #1e293b); border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <span style="font-size: 2rem; font-weight: bold; color: white;">${compatibilityData.compatibility_percentage}%</span>
                <span style="font-size: 0.8rem; color: #cbd5e1; text-transform: uppercase; letter-spacing: 1px;">Compatibilité</span>
              </div>
            </div>
          </div>
          
          <div class="compatibility-summary">
            <div style="display: flex; align-items: center; gap: 1rem; margin: 1rem 0; padding: 1rem; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px;">
              <i class="fas fa-check-circle" style="color: #10b981; font-size: 1.5rem;"></i>
              <span style="color: #f8fafc; font-weight: 500; font-size: 1.1rem;">${compatibilityData.matched_count} compétences correspondantes</span>
            </div>
            <div style="display: flex; align-items: center; gap: 1rem; margin: 1rem 0; padding: 1rem; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px;">
              <i class="fas fa-times-circle" style="color: #ef4444; font-size: 1.5rem;"></i>
              <span style="color: #f8fafc; font-weight: 500; font-size: 1.1rem;">${compatibilityData.missing_count} compétences manquantes</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="modal-footer" style="padding: 1.5rem 2rem; border-top: 1px solid rgba(59, 130, 246, 0.2); background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 0 0 20px 20px; display: flex; justify-content: flex-end;">
        <button onclick="this.closest('.modal-overlay').remove()" style="padding: 0.875rem 1.75rem; border: none; border-radius: 12px; font-weight: 600; cursor: pointer; background: linear-gradient(135deg, #64748b, #475569); color: white; border: 1px solid rgba(100, 116, 139, 0.3);">Fermer</button>
      </div>
    </div>
  `

  document.body.appendChild(modal)
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.remove()
  })
}

// Helper functions
function getCompatibilityClass(percentage) {
  if (percentage >= 75) return "high"
  if (percentage >= 50) return "medium"
  if (percentage >= 25) return "low"
  return "very-low"
}

function getCompatibilityIcon(percentage) {
  if (percentage >= 75) return "star"
  if (percentage >= 50) return "star-half-alt"
  if (percentage >= 25) return "exclamation-triangle"
  return "times-circle"
}

function getStatusText(status) {
  const statusTexts = {
    pending: "En attente",
    reviewed: "Examiné",
    interview_scheduled: "Entretien programmé",
    accepted: "Accepté",
    rejected: "Rejeté",
  }
  return statusTexts[status] || status
}

function updateCompatibilityStats() {
  if (applications.length === 0) {
    const avgElement = document.getElementById("averageCompatibility")
    if (avgElement) avgElement.textContent = "--"
    return
  }

  const totalCompatibility = applications.reduce((sum, app) => sum + (app.compatibility_percentage || 0), 0)
  const averageCompatibility = Math.round(totalCompatibility / applications.length)

  const avgElement = document.getElementById("averageCompatibility")
  if (avgElement) {
    avgElement.textContent = `${averageCompatibility}%`
  }
}

// Fonction pour retourner au dashboard
function goBackToDashboard() {
  console.log("🔙 Retour au dashboard")
  window.location.href = "/dashboard"
}

// Obtenir le texte du statut
const statusMap = {
  pending: "En attente",
  reviewed: "Examinée",
  interview_scheduled: "Entretien programmé",
  accepted: "Acceptée",
  rejected: "Rejetée",
  open: "Ouvert",
  closed: "Fermé",
  filled: "Pourvu",
}

// FONCTION CORRIGÉE: Afficher la modal de confirmation de recommandation
function showRecommendConfirmation(applicationId, candidateName, jobTitle) {
  console.log(`👍 Affichage confirmation recommandation pour ${candidateName} (ID: ${applicationId})`)

  if (!currentUser || currentUser.role !== "department_head") {
    showNotification("Seuls les chefs de département peuvent recommander des candidatures", "warning")
    return
  }

  const safeCandidateName = candidateName.replace(/'/g, "\\'").replace(/"/g, '\\"')
  const safeJobTitle = jobTitle.replace(/'/g, "\\'").replace(/"/g, '\\"')

  const modal = document.createElement("div")
  modal.className = "modal-overlay"
  modal.style.opacity = "1"

  modal.innerHTML = `
  <div class="confirmation-modal">
    <div class="modal-content">
      <div class="modal-header">
        <div class="confirmation-icon recommend">
          <i class="fas fa-thumbs-up"></i>
        </div>
        <h3>Recommander cette candidature</h3>
        <p>Recommander <strong>${candidateName}</strong> pour le poste</p>
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
        <p><strong>En tant que chef de département, vous pouvez recommander cette candidature :</strong></p>
        <div class="confirmation-details">
          <ul class="confirmation-list">
            <li><i class="fas fa-star"></i> Marquer la candidature comme recommandée</li>
            <li><i class="fas fa-bell"></i> Notifier les recruteurs et super admins</li>
            <li><i class="fas fa-comment"></i> Ajouter vos commentaires de recommandation</li>
            <li><i class="fas fa-priority-high"></i> Donner une priorité élevée à cette candidature</li>
          </ul>
        </div>
        
        <div class="recommendation-form">
          <label for="recommendationComment">Commentaire de recommandation :</label>
          <textarea id="recommendationComment" placeholder="Expliquez pourquoi vous recommandez ce candidat..." rows="3" required></textarea>
          
          <label for="recommendationPriority">Niveau de recommandation :</label>
          <select id="recommendationPriority">
            <option value="normal">Recommandation normale</option>
            <option value="high">Recommandation forte</option>
            <option value="urgent">Recommandation urgente</option>
          </select>
        </div>
      </div>
      
      <div class="modal-actions">
        <button class="btn-confirm recommend" onclick="confirmRecommendApplication(${applicationId})">
          <i class="fas fa-thumbs-up"></i> Confirmer la recommandation
        </button>
        <button class="btn-cancel" onclick="closeConfirmationModal()">
          <i class="fas fa-times"></i> Annuler
        </button>
      </div>
    </div>
  </div>
`

  document.body.appendChild(modal)

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeConfirmationModal()
    }
  })

  document.addEventListener("keydown", handleEscapeKey)
}

// FONCTION CORRIGÉE: Confirmer la recommandation avec meilleur feedback
async function confirmRecommendApplication(applicationId) {
  console.log(`👍 Confirmation recommandation candidature ${applicationId}`)

  try {
    const commentElement = document.getElementById("recommendationComment")
    const priorityElement = document.getElementById("recommendationPriority")

    if (!commentElement || !priorityElement) {
      showNotification("Erreur: éléments du formulaire non trouvés", "error")
      return
    }

    const comment = commentElement.value.trim()
    const priority = priorityElement.value

    if (!comment) {
      showNotification("Le commentaire de recommandation est obligatoire", "warning")
      commentElement.focus()
      return
    }

    if (comment.length < 10) {
      showNotification("Le commentaire doit contenir au moins 10 caractères", "warning")
      commentElement.focus()
      return
    }

    closeConfirmationModal()
    showLoading("Traitement de votre recommandation...")

    const response = await fetch(`/api/applications/${applicationId}/recommend`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        comment: comment,
        priority: priority,
      }),
    })

    const result = await response.json()
    hideLoading()

    if (result.success) {
      console.log("👍 Candidature recommandée avec succès")
      showNotification(`✅ ${result.message || "Candidature recommandée avec succès"}`, "success")

      setTimeout(async () => {
        console.log("🔄 Rechargement des données après recommandation...")
        if (currentJob && currentJob.id) {
          await loadJobFromAPI(currentJob.id)
        }
      }, 1000)

      setTimeout(() => {
        showNotification("🎯 Les recruteurs et super admins ont été notifiés de votre recommandation", "info")
      }, 2000)
    } else {
      console.error("❌ Erreur recommandation candidature:", result.message)
      showNotification(`❌ ${result.message}`, "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ Erreur réseau recommandation candidature:", error)
    showNotification("❌ Erreur de connexion lors de la recommandation", "error")
  }
}


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
}

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
      setTimeout(() => {
        loadJobFromAPI()
      }, 1000)
    } else {
      showNotification(result.message || "Erreur lors de l'acceptation", "error")
    }
  } catch (error) {
    console.error("❌ Erreur réseau:", error)
    hideLoading()
    showNotification("Erreur de connexion", "error")
  }
}

// Utility functions
function showLoading(message) {
  console.log("⏳ Loading:", message)
}

function hideLoading() {
  console.log("✅ Loading complete")
}

function showError(message) {
  console.error("❌ Error:", message)
}

function showNotification(message, type) {
  console.log(`📢 ${type.toUpperCase()}:`, message)
}

function closeConfirmationModal() {
  const modal = document.querySelector(".modal-overlay")
  if (modal) modal.remove()
}
