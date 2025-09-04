console.log("🎯 FRONTEND: Dashboard Core chargé avec succès")

// Variables globales
let departments = []
let employees = []
let jobs = []
let currentUser = null
const expandedDepartments = new Set()
let filteredDepartments = []
let isSearchActive = false

// Initialize global applications variable
window.applications = []

// Initialize dashboard when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 FRONTEND: Dashboard initializing...")
  
  // Check authentication first
  if (!checkAuthentication()) {
    return;
  }
  
  initializeDashboard()
  initializeSkillsSystem()
  console.log("✅ FRONTEND: Dashboard initialized")
})

// Check if user is authenticated
function checkAuthentication() {
  const token = localStorage.getItem('hr_access_token');
  if (!token) {
    console.log("❌ FRONTEND: No authentication token found, redirecting to login");
    window.location.replace("/hr-login");
    return false;
  }
  
  // Verify token is not expired (basic check)
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp && payload.exp < now) {
      console.log("❌ FRONTEND: Token expired, redirecting to login");
      localStorage.clear();
      window.location.replace("/hr-login");
      return false;
    }
  } catch (error) {
    console.log("❌ FRONTEND: Invalid token, redirecting to login");
    localStorage.clear();
    window.location.replace("/hr-login");
    return false;
  }
  
  return true;
}

// Prevent back button from showing cached dashboard
window.addEventListener('pageshow', function(event) {
  if (event.persisted) {
    // Page was loaded from cache, check authentication again
    console.log("🔄 FRONTEND: Page loaded from cache, checking authentication");
    if (!checkAuthentication()) {
      return;
    }
  }
});

// Prevent back button navigation to dashboard after logout
window.addEventListener('popstate', function(event) {
  const token = localStorage.getItem('hr_access_token');
  if (!token) {
    console.log("🚫 FRONTEND: Back button blocked - no authentication");
    window.location.replace("/hr-login");
  }
});

// Fonction d'initialisation
async function initializeDashboard() {
  try {
    console.log("🔄 FRONTEND: Début initialisation")
    // Charger l'utilisateur actuel
    await loadCurrentUser()
    // Charger les données de base
    await Promise.all([loadDepartments(), loadEmployees(), loadJobs(), loadDashboardStats()])
    // Load applications with compatibility AFTER other data is loaded
    await loadDashboardData()
    console.log("✅ FRONTEND: Initialisation terminée")
  } catch (error) {
    console.error("❌ FRONTEND: Erreur lors de l'initialisation:", error)
  }
}

async function loadDashboardData() {
  console.log("📊 FRONTEND: Loading dashboard data...")
  try {
    // Load applications with compatibility (use the enhanced function if available)
    if (typeof window.loadApplicationsWithFilters === "function") {
      console.log("🎯 FRONTEND: Using enhanced applications loader with compatibility")
      await window.loadApplicationsWithFilters()
    } else {
      console.log("⚠️ FRONTEND: Falling back to basic applications loader")
      await loadApplications()
    }
    console.log("✅ FRONTEND: Dashboard data loaded successfully")
  } catch (error) {
    console.error("❌ FRONTEND: Error loading dashboard data:", error)
  }
}

// FONCTION DE BASE: Charger les candidatures depuis l'API (fallback)
async function loadApplications() {
  console.log("📋 FRONTEND: Chargement des candidatures (mode basique)")
  try {
    const response = await fetch("/api/applications", {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('hr_access_token')}`,
        'Content-Type': 'application/json'
      }
    })
    const result = await response.json()
    if (result.success) {
      window.applications = (result.applications || []).map((app) => ({
        ...app,
        compatibility_percentage: typeof app.compatibility_percentage === "number" ? app.compatibility_percentage : 0,
        matched_skills_count: typeof app.matched_skills_count === "number" ? app.matched_skills_count : 0,
        total_job_skills: typeof app.total_job_skills === "number" ? app.total_job_skills : 0,
      }))
      console.log(
        "🔍 FRONTEND: Fallback processed applications with compatibility:",
        window.applications.map((app) => ({
          id: app.id,
          compatibility_percentage: app.compatibility_percentage,
          matched_skills_count: app.matched_skills_count,
          total_job_skills: app.total_job_skills,
        })),
      )
      console.log(`✅ FRONTEND: ${window.applications.length} candidatures chargées`)
      // Check if we have compatibility data
      if (window.applications.length > 0 && window.applications[0].compatibility_percentage !== undefined) {
        console.log("🎯 FRONTEND: Compatibility data detected, using enhanced rendering")
        if (typeof window.renderApplicationsWithCompatibility === "function") {
          window.renderApplicationsWithCompatibility()
        } else {
          renderApplicationsWithCompatibility()
        }
      } else {
        console.log("📋 FRONTEND: No compatibility data, using basic rendering")
        renderApplicationsWithCompatibility()
      }
    } else {
      console.error("❌ FRONTEND: Erreur chargement candidatures:", result.message)
      window.applications = []
      renderApplicationsWithCompatibility()
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement candidatures:", error)
    window.applications = []
    renderApplicationsWithCompatibility()
  }
}

// FONCTION MISE À JOUR: Rendu des candidatures avec témoin de recommandation et compatibilité
function renderApplicationsWithCompatibility(filter = "all") {
  console.log("📋 FRONTEND: Rendu des candidatures combiné, filtre:", filter)

  const container = document.getElementById("applicationsContainer")
  if (!container) {
    console.error("❌ FRONTEND: Container candidatures non trouvé")
    return
  }

  let filteredApps = window.applications // Use window.applications
  if (filter !== "all") {
    filteredApps = window.applications.filter((app) => app.status === filter) // Use window.applications
  }

  if (filteredApps.length === 0) {
    container.innerHTML = `
<div class="empty-applications">
  <i class="fas fa-file-alt"></i>
  <h4>Aucune candidature</h4>
  <p>Aucune candidature ${getFilterText(filter)}</p>
</div>
`
    return
  }

  container.innerHTML = filteredApps
    .map((app) => {
      console.log(
        `🎯 FRONTEND: Rendering app ${app.id} with compatibility ${app.compatibility_percentage}% (source: ${app.compatibility_source || "calculated"})`,
      )

      const isAICompatibility = app.compatibility_source === "ai"
      const hasAIReason = isAICompatibility && app.compatibility_reason && app.compatibility_reason.trim() !== ""

      return `
<div class="application-card ${app.status}">
  <div class="application-header">
    <div class="applicant-info">
      <div class="applicant-avatar">${getInitials(app.candidate_name)}</div>
      <div class="applicant-details">
        <h4>${app.candidate_name}
          ${
            app.is_recommended
              ? `
            <span class="recommendation-badge ${app.recommendation_priority}" 
                  title="Candidat recommandé par ${app.recommended_by || "un chef de département"}">
              <i class="fas fa-star"></i> 
              ${app.recommendation_priority === "urgent" ? "URGENT" : app.recommendation_priority === "high" ? "PRIORITÉ HAUTE" : "RECOMMANDÉ"}
            </span>
          `
              : ""
          }
        </h4>
        <p>${app.candidate_email}</p>
        <small><i class="fas fa-briefcase"></i> ${app.job_title}</small>
      </div>
    </div>
    <div class="application-status ${app.status}">
      ${getStatusText(app.status)}
      ${
        app.is_recommended && app.recommendation_priority !== "normal"
          ? `<span class="priority-indicator ${app.recommendation_priority}">
              ${app.recommendation_priority === "urgent" ? "🔥" : ""}
            </span>`
          : ""
      }
    </div>
  </div>

  ${
    app.is_recommended
      ? `
      <div class="recommendation-info clickable" onclick="toggleRecommendationComment(${app.id})" style="
        cursor: pointer;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, rgba(243, 156, 18, 0.1), rgba(230, 126, 34, 0.05));
        border: 1px solid rgba(243, 156, 18, 0.3);
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.75rem 0;
        position: relative;
      " onmouseover="this.style.background='linear-gradient(135deg, rgba(243, 156, 18, 0.15), rgba(230, 126, 34, 0.08))'" 
         onmouseout="this.style.background='linear-gradient(135deg, rgba(243, 156, 18, 0.1), rgba(230, 126, 34, 0.05))'">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas fa-user-tie" style="color: #f39c12;"></i>
            <span style="color: #f39c12; font-weight: 500;">
              Recommandé par: ${app.recommended_by || "N/A"} 
              ${app.recommendation_date ? `le ${formatDate(app.recommendation_date)}` : ""}
            </span>
          </div>
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <small style="color: #cbd5e1; font-size: 0.8rem;">Voir le commentaire</small>
            <i class="fas fa-chevron-down recommendation-chevron-${app.id}" style="
              color: #f39c12; 
              transition: transform 0.3s ease;
              font-size: 0.9rem;
            "></i>
          </div>
        </div>
      </div>

      ${
        app.recommendation_comment
          ? `
          <div class="recommendation-comment recommendation-comment-${app.id}" style="
            background: linear-gradient(135deg, rgba(243, 156, 18, 0.1), rgba(230, 126, 34, 0.05));
            border: 1px solid rgba(243, 156, 18, 0.3);
            border-radius: 8px;
            padding: 0;
            margin: 0 0 1rem 0;
            max-height: 0;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            opacity: 0;
          ">
            <div style="padding: 1rem;">
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <i class="fas fa-comment-alt" style="color: #f39c12;"></i>
                <strong style="color: #f8fafc;">Commentaire de recommandation:</strong>
              </div>
              <p style="
                font-style: italic;
                margin: 0.5rem 0;
                color: #e2e8f0;
                line-height: 1.5;
                background: rgba(0, 0, 0, 0.2);
                padding: 0.75rem;
                border-radius: 6px;
                border-left: 3px solid #f39c12;
              ">${app.recommendation_comment}</p>
              ${app.recommended_by ? `<small style="color: #cbd5e1; font-weight: 500;">— ${app.recommended_by}</small>` : ""}
            </div>
          </div>
        `
          : ""
      }
    `
      : ""
  }

  <div class="application-job">
    <div class="job-info">
      <div class="job-title">${app.job_title}</div>
      <div class="job-department">${app.department_name}</div>
      <div class="job-priority priority-${app.priority || "normal"}">${(app.priority || "normal").toUpperCase()}</div>
    </div>
    <div class="application-date">
      Candidature envoyée le ${formatDate(app.application_date)}
      <br><small>Il y a ${app.days_since_application} jour(s)</small>
    </div>
  </div>

  ${
    app.compatibility_percentage !== undefined
      ? `
      <div class="application-compatibility-section">
        <div class="compatibility-header">
          <div class="compatibility-title">
            <i class="fas fa-chart-pie"></i>
            Compatibilité des compétences
            <span class="compatibility-source ${isAICompatibility ? "ai" : "calculated"}">
              <i class="fas fa-${isAICompatibility ? "robot" : "calculator"}"></i>
              ${isAICompatibility ? "IA" : "CALCULÉ"}
            </span>
          </div>
          <div class="compatibility-percentage ${getCompatibilityClass(app.compatibility_percentage)}">
            ${app.compatibility_percentage}%
            <i class="fas fa-${getCompatibilityIcon(app.compatibility_percentage)}"></i>
          </div>
        </div>
        <div class="compatibility-progress">
          <div class="compatibility-progress-bar ${getCompatibilityClass(app.compatibility_percentage)}"
               style="width: ${app.compatibility_percentage}%"></div>
        </div>
        
        ${
          isAICompatibility
            ? ""
            : `
          <div class="compatibility-details">
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
        `
        }
      </div>
    `
      : ""
  }

  <div class="application-actions">
    <button class="app-btn view" onclick="viewCandidateProfile(${app.candidate_id})">
      <i class="fas fa-user"></i> Voir Profil
    </button>
    <button class="app-btn info" onclick="viewJobDetails(${app.job_id})">
      <i class="fas fa-info-circle"></i> Détails du poste
    </button>
    ${
      isAICompatibility && hasAIReason
        ? `
      <button class="app-btn ai-reason" onclick="showAIReasonModal(${app.id}, '${app.compatibility_reason.replace(/'/g, "\\'")}')">
        <i class="fas fa-robot"></i> Raison IA
      </button>
    `
        : ""
    }
    ${renderApplicationActionButtons(app)}
  </div>
</div>
`
    })
    .join("")
}

// FONCTION CORRIGÉE: Rendre les boutons d'action selon le rôle utilisateur
function renderApplicationActionButtons(app) {
  if (!currentUser) return ""

  // Pour les chefs de département : seulement le bouton recommander
  if (currentUser.role === "department_head") {
    if ((app.status === "pending" || app.status === "reviewed") && !app.is_recommended) {
      // Échapper les caractères spéciaux pour éviter les erreurs JavaScript
      const safeCandidateName = app.candidate_name.replace(/'/g, "\\'").replace(/"/g, '\\"')
      const safeJobTitle = app.job_title.replace(/'/g, "\\'").replace(/"/g, '\\"')
      return `
  <button class="app-btn recommend" onclick="showRecommendModal(${app.id}, '${safeCandidateName}', '${safeJobTitle}')">
    <i class="fas fa-thumbs-up"></i> Recommander
  </button>
`
    }
    // Si déjà recommandé, afficher un indicateur
    if (app.is_recommended) {
      return `
  <div class="recommendation-status">
    <i class="fas fa-check-circle"></i> Déjà recommandé
  </div>
`
    }
    return "" // Pas de boutons pour les autres statuts
  }

  // Pour les recruteurs : boutons complets
  if (currentUser.role === "recruiter") {
    return `

${
  app.status === "interview_scheduled"
    ? `
  <button class="app-btn complete" onclick="completeInterview(${app.id})">
    <i class="fas fa-check"></i> Terminer Entretien
  </button>
  <button class="app-btn reschedule" onclick="rescheduleInterview(${app.id})">
    <i class="fas fa-calendar-alt"></i> Reprogrammer
  </button>
  `
    : ""
}
${
  app.status === "interview_completed" || app.status === "reviewed"
    ? `
  <button class="app-btn accept" onclick="updateApplicationStatus(${app.id}, 'accepted')">
    <i class="fas fa-check-circle"></i> Accepter
  </button>
  <button class="app-btn reject" onclick="updateApplicationStatus(${app.id}, 'rejected')">
    <i class="fas fa-times"></i> Rejeter
  </button>
  `
    : ""
}
`
  }

  // Pour les super admins : pas de boutons d'action
  if (currentUser.role === "super_admin") {
    return "" // Pas de boutons pour les super admins
  }

  return ""
}

// NOUVELLE FONCTION: Toggle du commentaire de recommandation
function toggleRecommendationComment(applicationId) {
  console.log(`🔄 Toggle commentaire recommandation pour l'application ${applicationId}`)
  const commentElement = document.querySelector(`.recommendation-comment-${applicationId}`)
  const chevronElement = document.querySelector(`.recommendation-chevron-${applicationId}`)

  if (!commentElement || !chevronElement) {
    console.error("❌ Éléments de recommandation non trouvés")
    return
  }

  const isExpanded = commentElement.style.maxHeight && commentElement.style.maxHeight !== "0px"

  if (isExpanded) {
    // Fermer le commentaire
    commentElement.style.maxHeight = "0px"
    commentElement.style.opacity = "0"
    commentElement.style.padding = "0"
    chevronElement.style.transform = "rotate(0deg)"

    // Changer le texte d'indication
    const parentInfo = chevronElement.closest(".recommendation-info")
    const hintText = parentInfo.querySelector("small")
    if (hintText) {
      hintText.textContent = "Voir le commentaire"
    }
  } else {
    // Ouvrir le commentaire
    commentElement.style.maxHeight = commentElement.scrollHeight + "px"
    commentElement.style.opacity = "1"
    commentElement.style.padding = "0"
    chevronElement.style.transform = "rotate(180deg)"

    // Changer le texte d'indication
    const parentInfo = chevronElement.closest(".recommendation-info")
    const hintText = parentInfo.querySelector("small")
    if (hintText) {
      hintText.textContent = "Masquer le commentaire"
    }

    // Scroll fluide vers le commentaire après l'animation
    setTimeout(() => {
      commentElement.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      })
    }, 200)
  }
}

// Global variable to store selected skills for a job
let jobSkills = []

// Initialize skills system
function initializeSkillsSystem() {
  // Register skill-related functions globally
  window.addSkill = addSkill
  window.removeSkill = removeSkill
  window.renderSkillsList = renderSkillsList
  window.clearJobSkills = clearJobSkills
  window.getLevelText = getLevelText

  console.log("🔧 FRONTEND: Skills system initialized")
}

// Add a skill to the job
function addSkill() {
  const skillNameInput = document.getElementById("skillNameInput")
  const skillLevelInput = document.getElementById("skillLevelInput")
  const skillRequiredInput = document.getElementById("skillRequiredInput")

  if (!skillNameInput || !skillLevelInput || !skillRequiredInput) {
    console.error("❌ FRONTEND: Skill input elements not found")
    return
  }

  const skillName = skillNameInput.value.trim()
  const skillLevel = skillLevelInput.value
  const isRequired = skillRequiredInput.checked

  if (!skillName) {
    showNotification("Veuillez saisir le nom de la compétence", "warning")
    return
  }

  // Check for duplicate skill
  if (jobSkills.some((skill) => skill.name.toLowerCase() === skillName.toLowerCase())) {
    showNotification("Cette compétence a déjà été ajoutée", "warning")
    return
  }

  // Add new skill
  jobSkills.push({
    name: skillName,
    level: skillLevel,
    required: isRequired,
  })

  console.log(`✅ FRONTEND: Skill added: ${skillName} (${skillLevel}, ${isRequired ? "Required" : "Optional"})`)

  // Reset inputs and refresh display
  skillNameInput.value = ""
  skillLevelInput.value = "intermediate"
  skillRequiredInput.checked = true
  renderSkillsList()
}

// Remove a skill
function removeSkill(index) {
  if (index >= 0 && index < jobSkills.length) {
    const removedSkill = jobSkills.splice(index, 1)[0]
    console.log(`🗑️ FRONTEND: Skill removed: ${removedSkill.name}`)
    renderSkillsList()
  }
}

// Render skills list UI
function renderSkillsList() {
  const skillsList = document.getElementById("skillsList")
  if (!skillsList) {
    console.error("❌ FRONTEND: Skills list element not found")
    return
  }

  if (jobSkills.length === 0) {
    skillsList.innerHTML = `
<div class="skills-empty">
  <i class="fas fa-cogs"></i>
  <p>Aucune compétence ajoutée</p>
  <small>Ajoutez des compétences requises pour ce poste</small>
</div>
`
    return
  }

  skillsList.innerHTML = jobSkills
    .map(
      (skill, index) => `
<div class="skill-item">
<div class="skill-info">
  <span class="skill-name">${skill.name}</span>
  <span class="skill-level ${skill.level}">${getLevelText(skill.level)}</span>
  <span class="skill-required ${skill.required ? "required" : "optional"}">
    ${skill.required ? "Requis" : "Optionnel"}
  </span>
</div>
<button class="btn-remove-skill" onclick="removeSkill(${index})">
  <i class="fas fa-times"></i>
</button>
</div>
`,
    )
    .join("")

  console.log(`📋 FRONTEND: Skills list rendered with ${jobSkills.length} skills`)
}

// Get French text for skill level
function getLevelText(level) {
  const levelTexts = {
    beginner: "Débutant",
    intermediate: "Intermédiaire",
    advanced: "Avancé",
    expert: "Expert",
  }
  return levelTexts[level] || level
}

// Clear all job skills
function clearJobSkills() {
  jobSkills = []
  renderSkillsList()
  console.log("🧹 FRONTEND: All job skills cleared")
}

// FONCTION CORRIGÉE: Afficher la modal de recommandation
function showRecommendModal(applicationId, candidateName, jobTitle) {
  console.log(`👍 Affichage modal recommandation pour ${candidateName} (ID: ${applicationId})`)

  // Vérifier les permissions
  if (!currentUser || currentUser.role !== "department_head") {
    showNotification("Seuls les chefs de département peuvent recommander des candidatures", "warning")
    return
  }

  // Nettoyer toute modal existante
  const existingModal = document.querySelector(".recommend-modal-overlay")
  if (existingModal) {
    existingModal.remove()
  }

  const modal = document.createElement("div")
  modal.className = "modal-overlay recommend-modal-overlay"
  modal.style.cssText = `
position: fixed;
top: 0;
left: 0;
width: 100%;
height: 100%;
background: rgba(0, 0, 0, 0.8);
backdrop-filter: blur(10px);
display: flex;
align-items: center;
justify-content: center;
z-index: 25000;
padding: 2rem;
opacity: 0;
transition: opacity 0.3s ease;
`

  modal.innerHTML = `
<div class="modal-content recommend-modal" style="
background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
border: 2px solid rgba(243, 156, 18, 0.4);
border-radius: 20px;
max-width: 550px;
width: 95%;
max-height: 85vh;
overflow: hidden;
display: flex;
flex-direction: column;
box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
transform: scale(0.95);
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
">
<div class="modal-header" style="
  flex-shrink: 0;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  color: white;
  padding: 1.5rem 2rem;
  border-bottom: none;
  position: relative;
  border-radius: 20px 20px 0 0;
">
  <h3 style="margin: 0; font-size: 1.5rem; font-weight: 700; display: flex; align-items: center; gap: 0.75rem;">
    <i class="fas fa-thumbs-up" style="color: #f39c12;"></i> 
    Recommander cette candidature
  </h3>
  <button class="modal-close" onclick="closeRecommendModal()" style="
    position: absolute;
    top: 1.5rem;
    right: 1.5rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
    font-size: 1.2rem;
  ">&times;</button>
</div>

<div class="modal-body" style="
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 2rem;
  background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
">
  <div class="candidate-info-modal" style="
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.5rem;
    background: linear-gradient(135deg, rgba(243, 156, 18, 0.1), rgba(230, 126, 34, 0.05));
    border: 1px solid rgba(243, 156, 18, 0.3);
    border-radius: 16px;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
  ">
    <div class="candidate-avatar-modal" style="
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #f39c12, #e67e22);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: bold;
      font-size: 1.5rem;
      flex-shrink: 0;
      box-shadow: 0 4px 15px rgba(243, 156, 18, 0.3);
    ">${getInitials(candidateName)}</div>
    <div>
      <h4 style="color: #f8fafc; margin: 0 0 0.5rem 0; font-size: 1.25rem; font-weight: 700;">${candidateName}</h4>
      <p style="color: #cbd5e1; margin: 0.25rem 0; font-size: 0.95rem;"><strong>Poste:</strong> ${jobTitle}</p>
      <p style="color: #cbd5e1; margin: 0.25rem 0; font-size: 0.95rem;"><strong>Votre rôle:</strong> Chef de département</p>
    </div>
  </div>

  <div class="form-group" style="margin-bottom: 2rem;">
    <label class="form-label" style="
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.75rem;
      color: #f1f5f9;
      font-weight: 600;
      font-size: 0.95rem;
    ">
      <i class="fas fa-comment" style="color: #f39c12;"></i>
      Commentaire de recommandation *
    </label>
    <textarea 
      id="recommendationComment"
      class="form-textarea"
      placeholder="Expliquez pourquoi vous recommandez ce candidat (compétences, expérience, adéquation au poste...)..."
      rows="4"
      required
      style="
        width: 100%;
        padding: 1rem;
        border: 2px solid rgba(203, 213, 225, 0.3);
        border-radius: 12px;
        font-size: 0.95rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        background: rgba(248, 250, 252, 0.95);
        color: #1e293b;
        font-weight: 500;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
        font-family: inherit;
        resize: vertical;
        line-height: 1.5;
      "
    ></textarea>
    <small class="form-help" style="
      color: #cbd5e1;
      font-size: 0.85rem;
      margin-top: 0.5rem;
      font-style: italic;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    ">💡 Ce commentaire sera visible par les recruteurs et super admins</small>
  </div>

  <div class="form-group" style="margin-bottom: 2rem;">
    <label class="form-label" style="
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.75rem;
      color: #f1f5f9;
      font-weight: 600;
      font-size: 0.95rem;
    ">
      <i class="fas fa-flag" style="color: #f39c12;"></i>
      Niveau de priorité de votre recommandation
    </label>
    <select id="recommendationPriority" class="form-select" style="
      width: 100%;
      padding: 1rem;
      border: 2px solid rgba(203, 213, 225, 0.3);
      border-radius: 12px;
      font-size: 0.95rem;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      background: rgba(248, 250, 252, 0.95);
      color: #1e293b;
      font-weight: 500;
      box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
      cursor: pointer;
    ">
      <option value="normal">📋 Recommandation normale</option>
      <option value="high">⭐ Recommandation forte</option>
      <option value="urgent">🔥 Recommandation urgente</option>
    </select>
    <small class="form-help" style="
      color: #cbd5e1;
      font-size: 0.85rem;
      margin-top: 0.5rem;
      font-style: italic;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    ">💡 Choisissez le niveau selon l'adéquation du candidat</small>
  </div>

  <div class="recommendation-info" style="
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05));
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
    margin-top: 2rem;
    position: relative;
  ">
    <h5 style="
      margin: 0 0 1rem 0;
      color: #f8fafc;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    ">
      <i class="fas fa-info-circle" style="color: #3b82f6;"></i> 
      Cette action va :
    </h5>
    <ul style="margin: 0; padding-left: 1.5rem; list-style: none;">
      <li style="
        margin: 0.75rem 0;
        color: #cbd5e1;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.75rem;
      ">
        <i class="fas fa-star" style="color: #f59e0b; width: 20px; font-size: 1rem;"></i>
        Marquer la candidature comme recommandée
      </li>
      <li style="
        margin: 0.75rem 0;
        color: #cbd5e1;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.75rem;
      ">
        <i class="fas fa-bell" style="color: #17a2b8; width: 20px; font-size: 1rem;"></i>
        Notifier les recruteurs et super admins
      </li>
      <li style="
        margin: 0.75rem 0;
        color: #cbd5e1;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.75rem;
      ">
        <i class="fas fa-arrow-up" style="color: #28a745; width: 20px; font-size: 1rem;"></i>
        Donner une priorité élevée à cette candidature
      </li>
      <li style="
        margin: 0.75rem 0;
        color: #cbd5e1;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.75rem;
      ">
        <i class="fas fa-user-tie" style="color: #007bff; width: 20px; font-size: 1rem;"></i>
        Associer votre nom à cette recommandation
      </li>
    </ul>
  </div>
</div>

<div class="modal-footer" style="
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem 2rem;
  border-top: 1px solid rgba(59, 130, 246, 0.2);
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border-radius: 0 0 20px 20px;
">
  <button class="btn-secondary" onclick="closeRecommendModal()" style="
    padding: 0.875rem 1.75rem;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.95rem;
    background: linear-gradient(135deg, #64748b, #475569);
    color: white;
    border: 1px solid rgba(100, 116, 139, 0.3);
  ">
    <i class="fas fa-times"></i> Annuler
  </button>
  <button class="btn-primary recommend" onclick="confirmRecommendation(${applicationId})" style="
    padding: 0.875rem 1.75rem;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.95rem;
    background: linear-gradient(135deg, #f39c12, #e67e22);
    color: white;
    border: 1px solid rgba(243, 156, 18, 0.3);
    box-shadow: 0 4px 15px rgba(243, 156, 18, 0.3);
  ">
    <i class="fas fa-thumbs-up"></i> Confirmer la recommandation
  </button>
</div>
</div>
`

  document.body.appendChild(modal)

  // Empêcher le scroll du body
  document.body.style.overflow = "hidden"

  // Animation d'entrée
  requestAnimationFrame(() => {
    modal.style.opacity = "1"
    const modalContent = modal.querySelector(".recommend-modal")
    if (modalContent) {
      modalContent.style.transform = "scale(1)"
    }
  })

  // Focus sur le textarea
  setTimeout(() => {
    const commentField = document.getElementById("recommendationComment")
    if (commentField) {
      commentField.focus()
    }
  }, 100)

  // Fermer en cliquant à l'extérieur
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeRecommendModal()
    }
  })
}

// FONCTION CORRIGÉE: Fermer la modal de recommandation
function closeRecommendModal() {
  const modal = document.querySelector(".recommend-modal-overlay")
  if (modal) {
    modal.style.opacity = "0"
    const modalContent = modal.querySelector(".recommend-modal")
    if (modalContent) {
      modalContent.style.transform = "scale(0.95)"
    }
    setTimeout(() => {
      if (modal.parentElement) {
        modal.remove()
      }
      // S'assurer que le body peut scroller à nouveau
      document.body.style.overflow = "auto"
    }, 300)
  }
}

// FONCTION CORRIGÉE: Confirmer la recommandation
async function confirmRecommendation(applicationId) {
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

    // Validation
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

    // Fermer la modal AVANT d'afficher le loading
    closeRecommendModal()
    showLoading("Traitement de votre recommandation...")

    const response = await fetch(`/api/applications/${applicationId}/recommend`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        'Authorization': `Bearer ${localStorage.getItem('hr_access_token')}`,
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
      // Afficher la notification de succès
      showNotification(`✅ ${result.message || "Candidature recommandée avec succès"}`, "success")

      // Recharger les candidatures pour voir les changements
      await loadApplications()

      // Afficher un message de confirmation supplémentaire
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

function showAIReasonModal(applicationId, reason) {
  console.log(`🤖 [v0] DASHBOARD: Showing AI reason modal for application ${applicationId}`)

  const modal = document.createElement("div")
  modal.className = "ai-reason-modal-overlay"
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    animation: fadeIn 0.2s ease-out;
  `

  modal.innerHTML = `
    <div class="ai-reason-modal-content" style="
      background: linear-gradient(135deg, #1e293b, #334155);
      border: 1px solid rgba(16, 185, 129, 0.3);
      border-radius: 16px;
      max-width: 600px;
      width: 90%;
      max-height: 80vh;
      overflow-y: auto;
      animation: slideIn 0.3s ease-out;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    ">
      <div class="ai-reason-modal-header" style="
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 1.5rem;
        border-radius: 16px 16px 0 0;
        position: relative;
        overflow: hidden;
      ">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <i class="fas fa-robot" style="font-size: 1.5rem;"></i>
            <div>
              <h3 style="margin: 0; font-size: 1.25rem; font-weight: 600;">Analyse IA</h3>
              <p style="margin: 0; opacity: 0.9; font-size: 0.9rem;">Candidature #${applicationId}</p>
            </div>
          </div>
          <button onclick="closeAIReasonModal()" style="
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            font-size: 1.2rem;
          " onmouseover="this.style.background='rgba(255, 255, 255, 0.3)'" 
             onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
      
      <div class="ai-reason-modal-body" style="padding: 2rem;">
        <div class="ai-analysis-section" style="
          background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
          border: 1px solid rgba(16, 185, 129, 0.2);
          border-radius: 12px;
          padding: 1.5rem;
          position: relative;
          overflow: hidden;
        ">
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
            <i class="fas fa-brain" style="color: #10b981; font-size: 1.2rem;"></i>
            <h4 style="margin: 0; color: #10b981; font-weight: 600;">Raisonnement de l'IA</h4>
            <span class="modal-source-badge" style="
              background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.1));
              color: #10b981;
              border: 1px solid rgba(16, 185, 129, 0.3);
              padding: 0.25rem 0.5rem;
              border-radius: 12px;
              font-size: 0.7rem;
              font-weight: 600;
              text-transform: uppercase;
              letter-spacing: 0.5px;
              margin-left: auto;
            ">
              <i class="fas fa-robot"></i> IA
            </span>
          </div>
          <div style="
            color: #e2e8f0;
            line-height: 1.6;
            font-size: 0.95rem;
            background: rgba(0, 0, 0, 0.2);
            padding: 1rem;
            border-radius: 8px;
            border-left: 3px solid #10b981;
          ">
            ${reason}
          </div>
        </div>
      </div>
      
      <div class="ai-reason-modal-footer" style="
        padding: 1.5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        justify-content: flex-end;
      ">
        <button onclick="closeAIReasonModal()" style="
          background: linear-gradient(135deg, #6b7280, #4b5563);
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s ease;
        " onmouseover="this.style.background='linear-gradient(135deg, #4b5563, #374151)'" 
           onmouseout="this.style.background='linear-gradient(135deg, #6b7280, #4b5563)'">
          Fermer
        </button>
      </div>
    </div>
  `

  document.body.appendChild(modal)

  // Close on overlay click
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeAIReasonModal()
    }
  })

  // Close on escape key
  const handleEscape = (e) => {
    if (e.key === "Escape") {
      closeAIReasonModal()
      document.removeEventListener("keydown", handleEscape)
    }
  }
  document.addEventListener("keydown", handleEscape)
}

function closeAIReasonModal() {
  const modal = document.querySelector(".ai-reason-modal-overlay")
  if (modal) {
    modal.style.animation = "fadeOut 0.2s ease-out"
    setTimeout(() => {
      modal.remove()
    }, 200)
  }
}

// Compatibility helper functions (fallback if compatibility.js not loaded)
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

// Fonctions utilitaires pour les candidatures
function getInitials(name) {
  if (!name) return "??"
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
}

function filterApplications(status) {
  console.log("🔍 FRONTEND: Filtrage candidatures:", status)
  if (typeof window.renderApplicationsWithCompatibility === "function") {
    window.renderApplicationsWithCompatibility(status)
  } else {
    renderApplicationsWithCompatibility(status)
  }
}

// Filter applications by compatibility (fallback)
function filterApplicationsByCompatibility(compatibilityLevel) {
  console.log("🔍 FRONTEND: Filtering applications by compatibility:", compatibilityLevel)
  if (typeof window.loadApplicationsWithFilters === "function") {
    const statusFilter = document.querySelector(".filter-select").value || "all"
    window.loadApplicationsWithFilters(statusFilter, compatibilityLevel)
  } else {
    console.log("⚠️ FRONTEND: Enhanced compatibility filtering not available")
  }
}

// View compatibility details (fallback)
function viewCompatibilityDetails(applicationId) {
  console.log("🔍 FRONTEND: Viewing compatibility details for application:", applicationId)
  if (typeof window.viewCompatibilityDetails === "function") {
    window.viewCompatibilityDetails(applicationId)
  } else {
    showNotification("Fonctionnalité de compatibilité non disponible", "warning")
  }
}

// Update application status (fallback)
function updateApplicationStatus(applicationId, newStatus) {
  console.log("📝 FRONTEND: Updating application status:", { applicationId, newStatus })
  if (typeof window.updateApplicationStatus === "function") {
    window.updateApplicationStatus(applicationId, newStatus)
  } else {
    showNotification("Fonctionnalité de mise à jour non disponible", "warning")
  }
}

// Fonction pour charger l'utilisateur actuel
async function loadCurrentUser() {
  console.log("👤 FRONTEND: Chargement utilisateur actuel")
  try {
    const response = await fetch("/api/current-user", {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('hr_access_token')}`,
        'Content-Type': 'application/json'
      }
    })
    const result = await response.json()
    console.log("API Response:", result)
    if (result.success) {
      currentUser = result.user
      console.log("✅ FRONTEND: Utilisateur chargé:", currentUser)
      updateUserDisplay()
      // Adapter l'interface selon le rôle
      adaptInterfaceForRole()
    } else {
      console.error("❌ FRONTEND: Erreur chargement utilisateur:", result.message)
      if (result.message === "Utilisateur non connecté") {
        window.location.href = "/hr-login"
      }
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement utilisateur:", error)
  }
}

// FONCTION MISE À JOUR: Adapter l'interface selon le rôle
function adaptInterfaceForRole() {
  if (!currentUser) return
  console.log(`🔧 FRONTEND: Adaptation interface pour le rôle: ${currentUser.role}`)

  // Restrictions pour CHEF DE DÉPARTEMENT
  if (currentUser.role === "department_head") {
    console.log("🔒 FRONTEND: Mode chef de département activé")
    // Masquer tous les boutons de création de département
    const createDeptButtons = document.querySelectorAll('[onclick="openDepartmentModal()"]')
    createDeptButtons.forEach((btn) => {
      btn.style.display = "none"
      console.log("🚫 FRONTEND: Bouton création département masqué")
    })

    // Masquer le bouton "Nouveau Département" dans les actions rapides
    const quickActionCards = document.querySelectorAll(".quick-action-card")
    quickActionCards.forEach((card) => {
      const actionInfo = card.querySelector(".action-info h3")
      if (actionInfo && actionInfo.textContent.includes("Nouveau Département")) {
        card.style.display = "none"
        console.log("🚫 FRONTEND: Action rapide création département masquée")
      }
    })

    // Masquer le bouton + dans la sidebar des départements
    const addBtnInSidebar = document.querySelector(".sidebar-actions .add-btn")
    if (addBtnInSidebar) {
      addBtnInSidebar.style.display = "none"
      console.log("🚫 FRONTEND: Bouton + sidebar départements masqué")
    }

    // Ajouter un indicateur visuel
    const roleElement = document.getElementById("userRoleDisplay")
    if (roleElement) {
      roleElement.style.color = "#f59e0b"
    }
  }
  // Restrictions pour RECRUTEUR
  else if (currentUser.role === "recruiter") {
    console.log("🔍 FRONTEND: Mode recruteur activé")
    // Masquer tous les boutons de création de département
    const createDeptButtons = document.querySelectorAll('[onclick="openDepartmentModal()"]')
    createDeptButtons.forEach((btn) => {
      btn.style.display = "none"
      console.log("🚫 FRONTEND: Bouton création département masqué pour recruteur")
    })

    // Masquer le bouton "Nouveau Département" dans les actions rapides
    const quickActionCards = document.querySelectorAll(".quick-action-card")
    quickActionCards.forEach((card) => {
      const actionInfo = card.querySelector(".action-info h3")
      if (
        actionInfo &&
        (actionInfo.textContent.includes("Nouveau Département") || actionInfo.textContent.includes("Nouveau Poste"))
      ) {
        card.style.display = "none"
        console.log("🚫 FRONTEND: Action rapide masquée pour recruteur:", actionInfo.textContent)
      }
    })

    // Masquer le bouton + dans la sidebar des départements
    const addBtnInSidebar = document.querySelector(".sidebar-actions .add-btn")
    if (addBtnInSidebar) {
      addBtnInSidebar.style.display = "none"
      console.log("🚫 FRONTEND: Bouton + sidebar départements masqué pour recruteur")
    }

    // Ajouter un indicateur visuel
    const roleElement = document.getElementById("userRoleDisplay")
    if (roleElement) {
      roleElement.style.color = "#10b981"
    }
  }
  // Mode SUPER ADMIN (accès complet)
  else if (currentUser.role === "super_admin") {
    console.log("👑 FRONTEND: Mode Super Admin - Accès complet")
    // Ajouter un indicateur visuel
    const roleElement = document.getElementById("userRoleDisplay")
    if (roleElement) {
      roleElement.style.color = "#dc2626"
    }
  }
}

// Fonction pour mettre à jour l'affichage utilisateur
function updateUserDisplay() {
  if (currentUser) {
    const userName = `${currentUser.first_name} ${currentUser.last_name}`
    const userInitials = `${currentUser.first_name.charAt(0)}${currentUser.last_name.charAt(0)}`
    const roleTranslations = {
      super_admin: "Admin",
      recruiter: "Recruteur",
      department_head: "Chef de Département",
    }
    const translatedRole = roleTranslations[currentUser.role] || currentUser.role

    // Mettre à jour le rôle au-dessus du titre
    const roleElement = document.getElementById("userRoleDisplay")
    if (roleElement) {
      roleElement.textContent = translatedRole
    }

    // Mettre à jour le message de bienvenue
    const welcomeElement = document.getElementById("welcomeMessage")
    if (welcomeElement) {
      welcomeElement.textContent = `Bienvenue, ${userName}`
    }

    // Mettre à jour l'avatar
    const avatar = document.getElementById("userAvatar")
    if (avatar) {
      avatar.textContent = userInitials
    }
  }
}

// Fonction pour charger les statistiques du dashboard
async function loadDashboardStats() {
  console.log("📊 FRONTEND: Chargement statistiques dashboard")
  try {
    const response = await fetch("/api/dashboard-stats", {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('hr_access_token')}`,
        'Content-Type': 'application/json'
      }
    })
    const result = await response.json()
    if (result.success) {
      const stats = result.stats
      console.log("✅ FRONTEND: Statistiques chargées:", stats)
      updateStatsDisplay(stats)
    } else {
      console.error("❌ FRONTEND: Erreur chargement statistiques:", result.message)
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement statistiques:", error)
  }
}

// Fonction pour mettre à jour l'affichage des statistiques
function updateStatsDisplay(stats) {
  document.getElementById("totalDepartments").textContent = stats.total_departments || 0
  document.getElementById("totalEmployees").textContent = stats.total_employees || 0
  document.getElementById("totalJobs").textContent = stats.total_jobs || 0
  document.getElementById("urgentJobs").textContent = stats.urgent_jobs || 0
  document.getElementById("totalApplications").textContent = stats.total_applications || 0

  // Mettre à jour les pourcentages de changement
  const deptChange = document.querySelector("#totalDepartments").parentElement.querySelector(".stat-change")
  const jobChange = document.querySelector("#totalJobs").parentElement.querySelector(".stat-change")
  const empChange = document.querySelector("#totalEmployees").parentElement.querySelector(".stat-change")

  if (deptChange) deptChange.textContent = stats.dept_change || "+0%"
  if (jobChange) jobChange.textContent = stats.job_change || "+0%"
  if (empChange) empChange.textContent = stats.emp_change || "+0%"

  // Mettre à jour les classes de couleur
  updateStatChangeClass(deptChange, stats.dept_change || "+0%")
  updateStatChangeClass(jobChange, stats.job_change || "+0%")
  updateStatChangeClass(empChange, stats.emp_change || "+0%")

  console.log("✅ FRONTEND: Statistiques affichées")
}

// Fonction pour mettre à jour les classes de couleur des changements
function updateStatChangeClass(element, change) {
  if (!element) return
  element.classList.remove("positive", "negative", "warning")
  if (change.startsWith("+")) {
    element.classList.add("positive")
  } else if (change.startsWith("-")) {
    element.classList.add("negative")
  } else {
    element.classList.add("warning")
  }
}

// Fonctions de navigation
function openCompanyProfile() {
  console.log("🏢 FRONTEND: Ouverture profil entreprise")
  window.location.href = "/company-profile"
}

function logout() {
  console.log("🚪 FRONTEND: Déconnexion")
  
  // Clear all authentication data
  localStorage.removeItem('hr_access_token');
  localStorage.removeItem('hr_refresh_token');
  localStorage.removeItem('hr_user');
  
  // Clear session storage as well
  sessionStorage.clear();
  
  // Force reload to clear any cached data
  window.location.replace("/hr-login");
}

// Gestion des modals - FONCTIONS AMÉLIORÉES POUR LE CSS
function closeAllModals() {
  const modals = ["departmentModal", "jobModal", "employeeModal"]
  modals.forEach((modalId) => {
    const modal = document.getElementById(modalId)
    if (modal) {
      modal.style.display = "none"
      modal.classList.remove("show")
    }
  })
  document.body.style.overflow = "auto"
}

// NOUVELLES FONCTIONS: Gestion de l'assignation de manager
function toggleManagerAssignment() {
  // Vérifier les permissions pour créer des utilisateurs
  if (currentUser && (currentUser.role === "department_head" || currentUser.role === "recruiter")) {
    showNotification("Vous n'avez pas les permissions pour créer de nouveaux utilisateurs", "warning")
    document.getElementById("assignManagerToggle").checked = false
    return
  }

  const toggle = document.getElementById("assignManagerToggle")
  const section = document.getElementById("managerAssignmentSection")

  if (toggle.checked) {
    section.style.display = "block"
    section.classList.remove("hidden")
    section.classList.add("visible")
    // Charger les chefs disponibles
    loadAvailableManagers()
  } else {
    section.style.display = "none"
    section.classList.remove("visible")
    section.classList.add("hidden")
    // Réinitialiser tous les champs
    resetManagerFields()
  }
}

function toggleManagerType() {
  const existingRadio = document.getElementById("existingManagerRadio")
  const newRadio = document.getElementById("newManagerRadio")
  const existingSection = document.getElementById("existingManagerSection")
  const newSection = document.getElementById("newManagerSection")

  if (existingRadio.checked) {
    existingSection.style.display = "block"
    newSection.style.display = "none"
    existingSection.classList.add("visible")
    newSection.classList.add("hidden")
  } else if (newRadio.checked) {
    existingSection.style.display = "none"
    newSection.style.display = "block"
    existingSection.classList.add("visible")
    newSection.classList.add("hidden")
  }
}

function resetManagerFields() {
  // Réinitialiser les radios
  document.getElementById("existingManagerRadio").checked = false
  document.getElementById("newManagerRadio").checked = false

  // Cacher les sections
  document.getElementById("existingManagerSection").style.display = "none"
  document.getElementById("newManagerSection").style.display = "none"

  // Réinitialiser les champs
  document.getElementById("existingManagerSelect").value = ""
  document.getElementById("managerFirstName").value = ""
  document.getElementById("managerLastName").value = ""
  document.getElementById("managerEmail").value = ""
  document.getElementById("managerPassword").value = ""
  document.getElementById("canAddDepartment").checked = true
  document.getElementById("canManageApplications").checked = true
}

// Charger les chefs de département disponibles
async function loadAvailableManagers() {
  console.log("👥 FRONTEND: Chargement des chefs disponibles")
  try {
    const response = await fetch("/api/available-managers", {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('hr_access_token')}`,
        'Content-Type': 'application/json'
      }
    })
    const result = await response.json()
    const select = document.getElementById("existingManagerSelect")

    if (result.success) {
      const managers = result.managers || []
      console.log(`✅ FRONTEND: ${managers.length} chefs disponibles`)

      select.innerHTML = '<option value="">Sélectionner un chef de département</option>'
      managers.forEach((manager) => {
        const option = document.createElement("option")
        option.value = manager.id
        option.textContent = `${manager.first_name || ""} ${manager.last_name || ""} (${manager.email || ""})`
        select.appendChild(option)
      })

      if (managers.length === 0) {
        select.innerHTML = '<option value="">Aucun chef de département disponible</option>'
      }
    } else {
      console.error("❌ FRONTEND: Erreur chargement chefs:", result.message)
      select.innerHTML = '<option value="">Erreur de chargement</option>'
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement chefs:", error)
    document.getElementById("existingManagerSelect").innerHTML = '<option value="">Erreur de connexion</option>'
  }
}

// FONCTIONS MODALES AMÉLIORÉES POUR LE CSS
function openDepartmentModal() {
  console.log("🏢 FRONTEND: Ouverture modal département")
  closeAllModals()
  const modal = document.getElementById("departmentModal")
  if (modal) {
    modal.style.display = "flex"
    modal.classList.add("show")
    document.body.style.overflow = "hidden"

    // Réinitialiser le formulaire
    document.getElementById("departmentForm").reset()
    document.getElementById("departmentColor").value = "#3b82f6"

    // Masquer la section manager par défaut
    document.getElementById("assignManagerToggle").checked = false
    document.getElementById("managerAssignmentSection").style.display = "none"
    resetManagerFields()

    // Animation d'entrée
    requestAnimationFrame(() => {
      modal.style.opacity = "1"
    })
  }
}

function closeDepartmentModal() {
  console.log("🏢 FRONTEND: Fermeture modal département")
  const modal = document.getElementById("departmentModal")
  if (modal) {
    modal.classList.remove("show")
    setTimeout(() => {
      modal.style.display = "none"
      document.body.style.overflow = "auto"
    }, 300)

    // Réinitialiser le formulaire
    document.getElementById("departmentForm").reset()
    document.getElementById("assignManagerToggle").checked = false
    document.getElementById("managerAssignmentSection").style.display = "none"
    resetManagerFields()
  }
}

function openJobModal(preselectedDeptId = null) {
  console.log("💼 FRONTEND: Ouverture modal poste")
  closeAllModals()

  const modal = document.getElementById("jobModal")
  if (modal) {
    modal.style.display = "flex"
    modal.classList.add("show")
    document.body.style.overflow = "hidden"

    // Réinitialiser le formulaire
    document.getElementById("jobForm").reset()

    // Clear job skills
    clearJobSkills()

    // Charger les données dans les selects
    loadDepartmentsInSelect("jobDepartment")
    loadEmployeesInSelect("jobEmployee")

    // Pré-sélectionner le département si fourni
    if (preselectedDeptId) {
      setTimeout(() => {
        const deptSelect = document.getElementById("jobDepartment")
        if (deptSelect) {
          deptSelect.value = preselectedDeptId
        }
      }, 100)
    }

    // Définir la date limite par défaut (dans 30 jours)
    const deadline = new Date()
    deadline.setDate(deadline.getDate() + 30)
    document.getElementById("jobDeadline").value = deadline.toISOString().split("T")[0]

    // Animation d'entrée
    requestAnimationFrame(() => {
      modal.style.opacity = "1"
    })
  }

  // Focus on first input
  setTimeout(() => {
    document.getElementById("jobTitle").focus()
  }, 200)
}

function closeJobModal() {
  console.log("💼 FRONTEND: Fermeture modal poste")

  const modal = document.getElementById("jobModal")
  if (modal) {
    modal.classList.remove("show")
    setTimeout(() => {
      modal.style.display = "none"
      document.body.style.overflow = "auto"
    }, 300)
    // Réinitialiser le formulaire
    document.getElementById("jobForm").reset()
    // Clear job skills
    clearJobSkills()
  }
}

function closeEmployeeModal() {
  console.log("👤 FRONTEND: Fermeture modal employé")
  const modal = document.getElementById("employeeModal")
  if (modal) {
    modal.classList.remove("show")
    setTimeout(() => {
      modal.style.display = "none"
      document.body.style.overflow = "auto"
    }, 300)
    // Réinitialiser le formulaire
    document.getElementById("employeeForm").reset()
  }
}

// Fonction pour basculer l'expansion d'un département
function toggleDepartmentExpansion(departmentId) {
  console.log("🔄 FRONTEND: Basculer expansion département:", departmentId)
  if (expandedDepartments.has(departmentId)) {
    expandedDepartments.delete(departmentId)
  } else {
    expandedDepartments.add(departmentId)
  }

  // Réafficher les départements
  if (isSearchActive) {
    displayFilteredDepartments(filteredDepartments)
  } else {
    displayDepartments()
  }
}

// FONCTION MODIFIÉE: Créer un département avec chef optionnel
async function createDepartment() {
  console.log("🏢 FRONTEND: Début création département")
  const name = document.getElementById("departmentName").value.trim()
  const description = document.getElementById("departmentDescription").value.trim()
  const color = document.getElementById("departmentColor").value
  const assignManager = document.getElementById("assignManagerToggle").checked

  if (!name) {
    showNotification("Le nom du département est requis", "warning")
    return
  }

  // Données de base du département
  const departmentData = {
    name: name,
    description: description || "",
    color: color,
    budget: 0.0,
  }

  // Si assignation d'un chef de département
  if (assignManager) {
    const existingManagerRadio = document.getElementById("existingManagerRadio")
    const newManagerRadio = document.getElementById("newManagerRadio")

    if (!existingManagerRadio.checked && !newManagerRadio.checked) {
      showNotification("Veuillez sélectionner le type d'assignation du chef", "warning")
      return
    }

    if (existingManagerRadio.checked) {
      // Assigner un chef existant
      const managerId = document.getElementById("existingManagerSelect").value
      if (!managerId) {
        showNotification("Veuillez sélectionner un chef de département", "warning")
        return
      }
      departmentData.assign_existing_manager = true
      departmentData.existing_manager_id = Number.parseInt(managerId)
    } else if (newManagerRadio.checked) {
      // Créer un nouveau chef
      const managerFirstName = document.getElementById("managerFirstName").value.trim()
      const managerLastName = document.getElementById("managerLastName").value.trim()
      const managerEmail = document.getElementById("managerEmail").value.trim()
      const managerPassword = document.getElementById("managerPassword").value.trim()

      if (!managerFirstName || !managerLastName || !managerEmail || !managerPassword) {
        showNotification("Tous les champs du nouveau chef sont requis", "warning")
        return
      }

      if (managerPassword.length < 8) {
        showNotification("Le mot de passe doit contenir au moins 8 caractères", "warning")
        return
      }

      departmentData.create_manager = true
      departmentData.manager_data = {
        first_name: managerFirstName,
        last_name: managerLastName,
        email: managerEmail,
        password: managerPassword,
        role: "department_head",
        permissions: {
          can_add_department: document.getElementById("canAddDepartment").checked,
          can_manage_applications: document.getElementById("canManageApplications").checked,
        },
      }
    }
  }

  console.log("📤 FRONTEND: Envoi données département:", departmentData)

  try {
    showLoading("Création du département en cours...")
    const response = await fetch("/api/create-department", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        'Authorization': `Bearer ${localStorage.getItem('hr_access_token')}`,
      },
      body: JSON.stringify(departmentData),
    })

    const result = await response.json()
    hideLoading()

    if (result.success) {
      console.log("✅ FRONTEND: Département créé avec succès")
      showNotification(result.message || "Département créé avec succès!", "success")
      closeDepartmentModal()
      await refreshDashboard()
    } else {
      console.error("❌ FRONTEND: Erreur création département:", result.message)
      showNotification("Erreur: " + result.message, "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ FRONTEND: Erreur réseau:", error)
    showNotification("Erreur de connexion au serveur. Veuillez réessayer.", "error")
  }
}

// Fonction pour créer un poste - AMÉLIORÉE AVEC SKILLS
async function createJob() {
  console.log("💼 FRONTEND: Début création poste")

  const title = document.getElementById("jobTitle").value.trim()
  const departmentId = document.getElementById("jobDepartment").value
  const priority = document.getElementById("jobPriority").value
  const deadline = document.getElementById("jobDeadline").value
  const employmentType = document.getElementById("jobType").value
  const salaryMin = document.getElementById("jobSalaryMin").value
  const salaryMax = document.getElementById("jobSalaryMax").value
  const description = document.getElementById("jobDescription").value.trim()
  const requirements = document.getElementById("jobRequirements").value.trim()
  const responsibilities = document.getElementById("jobResponsibilities").value.trim()
  const assignedEmployeeId = document.getElementById("jobEmployee").value

  // Validation
  if (!title) {
    showNotification("Le titre du poste est obligatoire", "warning")
    return
  }
  if (!departmentId) {
    showNotification("Veuillez sélectionner un département", "warning")
    return
  }
  if (!priority) {
    showNotification("Veuillez sélectionner une priorité", "warning")
    return
  }
  if (!employmentType) {
    showNotification("Veuillez sélectionner un type de contrat", "warning")
    return
  }
  if (!description) {
    showNotification("La description du poste est obligatoire", "warning")
    return
  }

  // Validation salaire
  if (salaryMin && salaryMax && Number.parseFloat(salaryMin) > Number.parseFloat(salaryMax)) {
    showNotification("Le salaire minimum ne peut pas être supérieur au salaire maximum", "warning")
    return
  }

  // Prepare skills data
  const skillsData = jobSkills.map((skill) => ({
    skill_name: skill.name,
    skill_level: skill.level,
    is_required: skill.required,
  }))

  const jobData = {
    title: title,
    department_id: Number.parseInt(departmentId),
    description: description,
    employment_type: employmentType,
    priority: priority,
    deadline: deadline || null,
    salary_min: salaryMin ? Number.parseFloat(salaryMin) : null,
    salary_max: salaryMax ? Number.parseFloat(salaryMax) : null,
    requirements: requirements || "",
    responsibilities: responsibilities || "",
    assigned_employee_id: assignedEmployeeId ? Number.parseInt(assignedEmployeeId) : null,
    skills: skillsData,
  }

  console.log("📤 FRONTEND: Envoi données poste avec compétences:", jobData)

  try {
    showLoading("Création du poste en cours...")
    const response = await fetch("/api/create-job", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        'Authorization': `Bearer ${localStorage.getItem('hr_access_token')}`,
      },
      body: JSON.stringify(jobData),
    })

    const result = await response.json()
    hideLoading()

    if (result.success) {
      console.log("✅ FRONTEND: Poste créé avec succès")
      let message = `Poste "${title}" créé avec succès !`
      if (result.skills_added > 0) {
        message += ` ${result.skills_added} compétence(s) ajoutée(s).`
      }
      if (result.skills_errors && result.skills_errors.length > 0) {
        message += ` Attention: ${result.skills_errors.length} erreur(s) sur les compétences.`
      }
      showNotification(message, "success")
      closeJobModal()
      await refreshDashboard()
    } else {
      console.error("❌ FRONTEND: Erreur création poste:", result.message)
      showNotification("Erreur: " + result.message, "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ FRONTEND: Erreur réseau:", error)
    showNotification("Erreur de connexion au serveur. Veuillez réessayer.", "error")
  }
}

// Fonction pour créer un employé
async function createEmployee() {
  console.log("👤 FRONTEND: Début création employé")
  const firstName = document.getElementById("employeeFirstName").value.trim()
  const lastName = document.getElementById("employeeLastName").value.trim()
  const email = document.getElementById("employeeEmail").value.trim()
  const departmentId = document.getElementById("employeeDepartment").value
  const position = document.getElementById("employeePosition").value.trim()
  const phone = document.getElementById("employeePhone").value.trim()
  const hireDate = document.getElementById("employeeHireDate").value
  const salary = document.getElementById("employeeSalary").value
  const employmentType = document.getElementById("employeeType").value

  if (!firstName || !lastName || !email || !departmentId || !position) {
    showNotification("Veuillez remplir tous les champs obligatoires", "warning")
    return
  }

  // Validation email
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    showNotification("Veuillez saisir un email valide", "warning")
    return
  }

  const employeeData = {
    first_name: firstName,
    last_name: lastName,
    email: email,
    department_id: Number.parseInt(departmentId),
    position: position,
    phone: phone || "",
    hire_date: hireDate || null,
    salary: salary ? Number.parseFloat(salary) : null,
    employment_type: employmentType,
    employee_id: "",
  }

  console.log("📤 FRONTEND: Envoi données employé:", employeeData)

  try {
    showLoading("Création de l'employé en cours...")
    const response = await fetch("/api/create-employee", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        'Authorization': `Bearer ${localStorage.getItem('hr_access_token')}`,
      },
      body: JSON.stringify(employeeData),
    })

    const result = await response.json()
    hideLoading()

    if (result.success) {
      console.log("✅ FRONTEND: Employé créé avec succès")
      showNotification(`Employé "${firstName} ${lastName}" créé avec succès !`, "success")
      closeEmployeeModal()
      await refreshDashboard()
    } else {
      console.error("❌ FRONTEND: Erreur création employé:", result.message)
      showNotification("Erreur: " + result.message, "error")
    }
  } catch (error) {
    hideLoading()
    console.error("❌ FRONTEND: Erreur réseau:", error)
    showNotification("Erreur de connexion au serveur. Veuillez réessayer.", "error")
  }
}

// Fonction pour rafraîchir tout le dashboard
async function refreshDashboard() {
  console.log("🔄 FRONTEND: Rafraîchissement complet du dashboard")
  await loadDepartments()
  await loadEmployees()
  await loadJobs()
  await loadDashboardData() // Use loadDashboardData to ensure compatibility logic
  await loadDashboardStats()
}

// Fonction pour charger les départements
async function loadDepartments() {
  console.log("🔄 FRONTEND: Chargement des départements")
  try {
    const response = await fetch("/api/departments", {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('hr_access_token')}`,
        'Content-Type': 'application/json'
      }
    })
    const result = await response.json()
    if (result.success) {
      departments = result.departments || []
      console.log(`✅ FRONTEND: ${departments.length} départements chargés`)
      // Si une recherche est active, refiltrer les résultats
      if (isSearchActive) {
        const searchTerm = document.getElementById("searchInput").value.toLowerCase().trim()
        if (searchTerm) {
          filterDepartments()
        } else {
          displayDepartments()
        }
      } else {
        displayDepartments()
      }
    } else {
      console.error("❌ FRONTEND: Erreur chargement départements:", result.message)
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement départements:", error)
  }
}

// Fonction pour charger les postes
async function loadJobs() {
  console.log("🔄 FRONTEND: Chargement des postes")
  try {
    const response = await fetch("/api/jobs", {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('hr_access_token')}`,
        'Content-Type': 'application/json'
      }
    })
    const result = await response.json()
    if (result.success) {
      jobs = result.jobs || []
      console.log(`✅ FRONTEND: ${jobs.length} postes chargés`)
    } else {
      console.error("❌ FRONTEND: Erreur chargement postes:", result.message)
    }
  } catch (error) {
    console.error("❌ FRONTEND: Erreur réseau chargement postes:", error)
  }
}

// Fonction pour afficher les départements
function displayDepartments() {
  const departmentsList = document.getElementById("departmentsList")
  if (!departmentsList) {
    console.error("❌ FRONTEND: Element departmentsList non trouvé")
    return
  }

  if (departments.length === 0) {
    departmentsList.innerHTML = `
<div class="empty-departments">
  <div class="empty-icon"><i class="fas fa-building"></i></div>
  <h4>Aucun département</h4>
  <p>Commencez par créer votre premier département</p>
  <button class="empty-btn" onclick="openDepartmentModal()">
    <i class="fas fa-plus"></i> Créer Département
  </button>
</div>
`
    return
  }

  renderDepartmentsList(departments)
}

// Fonction pour afficher les départements filtrés
function displayFilteredDepartments(filteredDepts) {
  const departmentsList = document.getElementById("departmentsList")
  if (!departmentsList) {
    console.error("❌ FRONTEND: Element departmentsList non trouvé")
    return
  }

  if (filteredDepts.length === 0) {
    departmentsList.innerHTML = `
<div class="empty-departments">
  <div class="empty-icon"><i class="fas fa-search"></i></div>
  <h4>Aucun résultat trouvé</h4>
  <p>Aucun département ne correspond à votre recherche</p>
  <button class="empty-btn" onclick="clearSearch()">
    <i class="fas fa-times"></i> Effacer la recherche
  </button>
</div>
`
    return
  }

  renderDepartmentsList(filteredDepts)
}

// FONCTION AMÉLIORÉE: Générer le HTML des départements avec le nouveau CSS
function renderDepartmentsList(deptList) {
  const departmentsList = document.getElementById("departmentsList")
  let html = ""

  deptList.forEach((dept) => {
    const isExpanded = expandedDepartments.has(dept.id)
    const departmentEmployees = employees.filter((emp) => emp.department_id === dept.id)
    const departmentJobs = jobs.filter((job) => job.department_id === dept.id)

    html += `
<div class="department-card-enhanced" data-id="${dept.id}">
  <div class="department-header">
    <div class="department-info">
      <h4 style="color: ${dept.color || "#3b82f6"}">${dept.name || "Département sans nom"}</h4>
      <p>${dept.description || "Aucune description"}</p>
      <div class="manager">
        <i class="fas fa-user-tie"></i>
        ${dept.manager_name || "Aucun responsable assigné"}
      </div>
    </div>
    <div class="department-stats">
      <div class="stat-badge employees">
        <i class="fas fa-users"></i>
        ${dept.employee_count || departmentEmployees.length} employé${(dept.employee_count || departmentEmployees.length) > 1 ? "s" : ""}
      </div>
      <div class="stat-badge jobs">
        <i class="fas fa-briefcase"></i>
        ${dept.job_count || departmentJobs.length} poste${(dept.job_count || departmentJobs.length) > 1 ? "s" : ""}
      </div>
    </div>
  </div>

  <div class="department-actions">
    <button class="btn-expand ${isExpanded ? "expanded" : ""}"
             onclick="toggleDepartmentExpansion(${dept.id})"
             title="${isExpanded ? "Masquer" : "Voir"} les détails">
      <i class="fas fa-chevron-${isExpanded ? "up" : "down"}"></i>
      ${isExpanded ? "Masquer" : "Voir"} les détails
    </button>
    <button class="btn-add-job" onclick="openJobModal(${dept.id})" title="Créer un poste">
      <i class="fas fa-briefcase"></i>
    </button>
  </div>

  ${isExpanded ? renderDepartmentDetails(dept, departmentEmployees, departmentJobs) : ""}
</div>
`
  })

  departmentsList.innerHTML = html
}

// FONCTION AMÉLIORÉE: Afficher les détails d'un département
function renderDepartmentDetails(department, deptEmployees, deptJobs) {
  return `
<div class="department-details">
<div class="details-tabs">
  <div class="tab-section">
    <h5><i class="fas fa-users"></i> Employés (${deptEmployees.length})</h5>
    <div class="items-list">
      ${
        deptEmployees.length > 0
          ? deptEmployees
              .map(
                (emp) => `
                <div class="item-card">
                  <div class="item-avatar">${emp.first_name ? emp.first_name[0] : ""}${emp.last_name ? emp.last_name[0] : ""}</div>
                  <div class="item-info">
                    <strong>${emp.first_name || ""} ${emp.last_name || ""}</strong>
                    <span>${emp.position || "Poste non défini"}</span>
                    <small>${emp.email || "Email non défini"}</small>
                  </div>
                  <div class="item-actions">
                    <button class="btn-icon-small" onclick="viewEmployeeProfile(${emp.id})" title="Voir le profil">
                      <i class="fas fa-eye"></i>
                    </button>
                  </div>
                </div>
              `,
              )
              .join("")
          : '<div class="empty-message">Aucun employé dans ce département</div>'
      }
    </div>
  </div>

  <div class="tab-section">
    <h5><i class="fas fa-briefcase"></i> Postes (${deptJobs.length})</h5>
    <div class="items-list">
      ${
        deptJobs.length > 0
          ? deptJobs
              .map(
                (job) => `
                <div class="item-card">
                  <div class="item-avatar"><i class="fas fa-briefcase"></i></div>
                  <div class="item-info">
                    <strong>${job.title || "Titre non défini"}</strong>
                    <span>${job.employment_type || "Type non défini"} - ${job.salary_min && job.salary_max ? `${job.salary_min}€ - ${job.salary_max}€` : "Salaire non spécifié"}</span>
                    <small class="priority-${job.priority || "normal"}">${getPriorityLabel(job.priority || "normal")}</small>
                    ${job.assigned_employee_id ? '<span class="status-filled"><i class="fas fa-check"></i> Poste pourvu</span>' : ""}
                    ${job.skills && job.skills.length > 0 ? `<small><i class="fas fa-cogs"></i> ${job.skills.length} compétence(s)</small>` : ""}
                  </div>
                  <div class="item-actions">
                    <button class="btn-icon-small" onclick="viewJobDetails(${job.id})" title="Voir les détails">
                      <i class="fas fa-eye"></i>
                    </button>
                  </div>
                </div>
              `,
              )
              .join("")
          : '<div class="empty-message">Aucun poste dans ce département</div>'
      }
    </div>
  </div>
</div>
</div>
`
}

// Fonction pour charger les départements dans un select
function loadDepartmentsInSelect(selectId) {
  const select = document.getElementById(selectId)
  if (!select) return

  select.innerHTML = '<option value="">Sélectionner un département</option>'
  departments.forEach((dept) => {
    const option = document.createElement("option")
    option.value = dept.id
    option.textContent = dept.name
    select.appendChild(option)
  })
}

// Fonction pour charger les employés dans un select
function loadEmployeesInSelect(selectId) {
  const select = document.getElementById(selectId)
  if (!select) return

  select.innerHTML = '<option value="">Aucun employé assigné</option>'
  employees.forEach((emp) => {
    const option = document.createElement("option")
    option.value = emp.id
    option.textContent = `${emp.first_name || ""} ${emp.last_name || ""} (${emp.position || "Poste non défini"})`
    select.appendChild(option)
  })
}

function viewEmployeeProfile(employeeId) {
  const employee = employees.find((e) => e.id === employeeId)
  if (!employee) {
    showNotification("Employé introuvable", "error")
    return
  }

  // S'il a une propriété candidate_id, alors il vient d'un candidat
  if (employee.candidate_id) {
    console.log("➡️ Ouvrir comme candidat")
    window.open(`/employee-profile?candidate_id=${employee.candidate_id}`, "_blank")
  } else {
    console.log("➡️ Ouvrir comme employé normal")
    window.open(`/employee-profile?id=${employeeId}`, "_blank")
  }
}

// Fonctions placeholder
function exportData() {
  console.log("📊 FRONTEND: Export données")
  showNotification("Fonctionnalité en cours de développement", "info")
}

function generateReport() {
  console.log("📈 FRONTEND: Génération rapport")
  window.location.href = "/hr-reports"
}

// ==================== FONCTION DE RECHERCHE CORRIGÉE ====================
function filterDepartments() {
  console.log("🔍 FRONTEND: Filtrage départements")
  const searchInput = document.getElementById("searchInput")
  if (!searchInput) {
    console.error("❌ FRONTEND: Input de recherche non trouvé")
    return
  }

  const searchTerm = searchInput.value.toLowerCase().trim()
  console.log(`🔍 FRONTEND: Terme de recherche: "${searchTerm}"`)

  // Si le terme de recherche est vide, afficher tous les départements
  if (!searchTerm) {
    console.log("🔍 FRONTEND: Recherche vide, affichage de tous les départements")
    isSearchActive = false
    filteredDepartments = []
    displayDepartments()
    return
  }

  // Marquer qu'une recherche est active
  isSearchActive = true

  // Filtrer les départements selon le terme de recherche
  filteredDepartments = departments.filter((dept) => {
    const name = (dept.name || "").toLowerCase()
    const description = (dept.description || "").toLowerCase()
    const matches = name.includes(searchTerm) || description.includes(searchTerm)
    if (matches) {
      console.log(`✅ FRONTEND: Département "${dept.name}" correspond à la recherche`)
    }
    return matches
  })

  console.log(`🔍 FRONTEND: ${filteredDepartments.length} départements trouvés pour "${searchTerm}"`)

  // Afficher les départements filtrés
  displayFilteredDepartments(filteredDepartments)
}

// Fonction pour effacer la recherche
function clearSearch() {
  console.log("🔍 FRONTEND: Effacement de la recherche")
  const searchInput = document.getElementById("searchInput")
  if (searchInput) {
    searchInput.value = ""
  }
  isSearchActive = false
  filteredDepartments = []
  displayDepartments()
}

// Charger les employés depuis l'API
async function loadEmployees() {
  console.log("👥 FRONTEND: Chargement des employés")
  try {
    const response = await fetch("/api/employees", {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('hr_access_token')}`,
        'Content-Type': 'application/json'
      }
    })
    const result = await response.json()
    if (result.success) {
      employees = result.employees || []
      console.log(`✅ FRONTEND: ${employees.length} employés chargés`)
    } else {
      console.error("❌ FRONTEND: Erreur chargement employés:", result.message)
      employees = []
    }
  } catch (error) {
    console.error("❌ Erreur réseau chargement employés:", error)
    employees = []
  }
}

function getFilterText(filter) {
  const filterTexts = {
    all: "",
    pending: "en attente",
    reviewed: "examinées",
    interview_scheduled: "avec entretien programmé",
    accepted: "acceptées",
    rejected: "rejetées",
    recommended: "recommandées",
  }
  return filterTexts[filter] || ""
}

function getStatusText(status) {
  const statusTexts = {
    pending: "En attente",
    reviewed: "Examinée",
    interview_scheduled: "Entretien programmé",
    accepted: "Acceptée",
    rejected: "Rejetée",
  }
  return statusTexts[status] || status
}

function getPriorityLabel(priority) {
  const labels = {
    urgent: "🔥 Urgent",
    normal: "📋 Normal",
    low: "⏳ Faible",
  }
  return labels[priority] || priority
}

function formatDate(dateString) {
  if (!dateString) return "Date inconnue"
  const date = new Date(dateString)
  return date.toLocaleDateString("fr-FR")
}

// Fonctions d'interaction avec les candidatures
function viewCandidateProfile(candidateId) {
  console.log("👤 FRONTEND: Ouverture profil candidat:", candidateId)
  window.open(`/employee-profile?candidate_id=${candidateId}`, "_blank")
}

// FONCTION CORRIGÉE: Voir les détails d'un poste
function viewJobDetails(jobId) {
  console.log("💼 FRONTEND: Navigation vers job-details pour le poste:", jobId)
  window.location.href = `/job-details?id=${jobId}`
}

function filterApplicationByName() {
  const input = document.getElementById("applicationSearchInput")
  if (!input) return

  const searchTerm = input.value.toLowerCase().trim()
  const filtered = window.applications.filter((app) => {
    // Use window.applications
    return (
      (app.candidate_name || "").toLowerCase().includes(searchTerm) ||
      (app.candidate_email || "").toLowerCase().includes(searchTerm)
    )
  })
  renderApplicationsList(filtered)
}

function renderApplicationsList(list) {
  const container = document.getElementById("applicationsContainer")

  if (!container) return

  if (list.length === 0) {
    container.innerHTML = `
<div class="empty-applications">
  <i class="fas fa-search"></i>
  <h4>Aucun résultat</h4>
  <p>Aucune candidature ne correspond à votre recherche</p>
</div>
`
    return
  }

  container.innerHTML = list
    .map((app) => {
      console.log(
        `🎯 FRONTEND: Search rendering app ${app.id} with compatibility ${app.compatibility_percentage}% (matched: ${app.matched_skills_count}, total: ${app.total_job_skills})`,
      )
      return `
<div class="application-card ${app.status}">
  <div class="application-header">
    <div class="applicant-info">
      <div class="applicant-avatar">${getInitials(app.candidate_name)}</div>
      <div class="applicant-details">
        <h4>${app.candidate_name}
          ${
            app.is_recommended
              ? `
            <span class="recommendation-badge ${app.recommendation_priority}" 
                  title="Candidat recommandé par ${app.recommended_by || "un chef de département"}">
              <i class="fas fa-star"></i> 
              ${app.recommendation_priority === "urgent" ? "URGENT" : app.recommendation_priority === "high" ? "PRIORITÉ HAUTE" : "RECOMMANDÉ"}
            </span>
          `
              : ""
          }
        </h4>
        <p>${app.candidate_email}</p>
        <small><i class="fas fa-briefcase"></i> ${app.job_title}</small>
      </div>
    </div>
    <div class="application-status ${app.status}">
      ${getStatusText(app.status)}
      ${
        app.is_recommended && app.recommendation_priority !== "normal"
          ? `<span class="priority-indicator ${app.recommendation_priority}">
              ${app.recommendation_priority === "urgent" ? "🔥" : ""}
            </span>`
          : ""
      }
    </div>
  </div>

  ${
    app.is_recommended
      ? `
      <div class="recommendation-info clickable" onclick="toggleRecommendationComment(${app.id})" style="
        cursor: pointer;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, rgba(243, 156, 18, 0.1), rgba(230, 126, 34, 0.05));
        border: 1px solid rgba(243, 156, 18, 0.3);
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.75rem 0;
        position: relative;
      " onmouseover="this.style.background='linear-gradient(135deg, rgba(243, 156, 18, 0.15), rgba(230, 126, 34, 0.08))'" 
         onmouseout="this.style.background='linear-gradient(135deg, rgba(243, 156, 18, 0.1), rgba(230, 126, 34, 0.05))'">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas fa-user-tie" style="color: #f39c12;"></i>
            <span style="color: #f39c12; font-weight: 500;">
              Recommandé par: ${app.recommended_by || "N/A"} 
              ${app.recommendation_date ? `le ${formatDate(app.recommendation_date)}` : ""}
            </span>
          </div>
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <small style="color: #cbd5e1; font-size: 0.8rem;">Voir le commentaire</small>
            <i class="fas fa-chevron-down recommendation-chevron-${app.id}" style="
              color: #f39c12; 
              transition: transform 0.3s ease;
              font-size: 0.9rem;
            "></i>
          </div>
        </div>
      </div>

      ${
        app.recommendation_comment
          ? `
          <div class="recommendation-comment recommendation-comment-${app.id}" style="
            background: linear-gradient(135deg, rgba(243, 156, 18, 0.1), rgba(230, 126, 34, 0.05));
            border: 1px solid rgba(243, 156, 18, 0.3);
            border-radius: 8px;
            padding: 0;
            margin: 0 0 1rem 0;
            max-height: 0;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            opacity: 0;
          ">
            <div style="padding: 1rem;">
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <i class="fas fa-comment-alt" style="color: #f39c12;"></i>
                <strong style="color: #f8fafc;">Commentaire de recommandation:</strong>
              </div>
              <p style="
                font-style: italic;
                margin: 0.5rem 0;
                color: #e2e8f0;
                line-height: 1.5;
                background: rgba(0, 0, 0, 0.2);
                padding: 0.75rem;
                border-radius: 6px;
                border-left: 3px solid #f39c12;
              ">${app.recommendation_comment}</p>
              ${app.recommended_by ? `<small style="color: #cbd5e1; font-weight: 500;">— ${app.recommended_by}</small>` : ""}
            </div>
          </div>
        `
          : ""
      }
    `
      : ""
  }

  <div class="application-job">
    <div class="job-info">
      <div class="job-title">${app.job_title}</div>
      <div class="job-department">${app.department_name}</div>
      <div class="job-priority priority-${app.priority || "normal"}">${(app.priority || "normal").toUpperCase()}</div>
    </div>
    <div class="application-date">
      Candidature envoyée le ${formatDate(app.application_date)}
      <br><small>Il y a ${app.days_since_application} jour(s)</small>
    </div>
  </div>

  ${
    app.compatibility_percentage !== undefined
      ? `
      <div class="application-compatibility-section">
        <div class="compatibility-header">
          <div class="compatibility-title">
            <i class="fas fa-chart-pie"></i>
            Compatibilité des compétences
          </div>
          <div class="compatibility-percentage ${getCompatibilityClass(app.compatibility_percentage)}">
            ${app.compatibility_percentage}%
            <i class="fas fa-${getCompatibilityIcon(app.compatibility_percentage)}"></i>
          </div>
        </div>
        <div class="compatibility-progress">
          <div class="compatibility-progress-bar ${getCompatibilityClass(app.compatibility_percentage)}"
               style="width: ${app.compatibility_percentage}%"></div>
        </div>
        <div class="compatibility-details">
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
      </div>
    `
      : ""
  }

    <div class="application-actions">
    <button class="app-btn view" onclick="viewCandidateProfile(${app.candidate_id})">
      <i class="fas fa-user"></i> Voir Profil
    </button>
    <button class="app-btn info" onclick="viewJobDetails(${app.job_id})">
      <i class="fas fa-info-circle"></i> Détails du poste
    </button>
    ${renderApplicationActionButtons(app)}
  </div>

  </div>
</div>
`
    })
    .join("")
}

// Fermer les modales en cliquant à l'extérieur
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    if (e.target.classList.contains("recommend-modal-overlay")) {
      closeRecommendModal()
    } else {
      const modal = e.target
      modal.classList.remove("show")
      setTimeout(() => {
        modal.style.display = "none"
        document.body.style.overflow = "auto"
      }, 300)
    }
  }
})

// Gestion des touches clavier
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    // Fermer la modal de recommandation si ouverte
    const recommendModal = document.querySelector(".recommend-modal-overlay")
    if (recommendModal) {
      closeRecommendModal()
      return
    }

    // Fermer les autres modals
    const modals = ["departmentModal", "jobModal", "employeeModal"]
    modals.forEach((modalId) => {
      const modal = document.getElementById(modalId)
      if (modal && modal.style.display === "flex") {
        modal.classList.remove("show")
        setTimeout(() => {
          modal.style.display = "none"
          document.body.style.overflow = "auto"
        }, 300)
      }
    })
  }
})

// Mise à jour de la couleur preview
document.addEventListener("DOMContentLoaded", () => {
  const colorInput = document.getElementById("departmentColor")
  const colorPreview = document.querySelector(".color-preview")
  if (colorInput && colorPreview) {
    colorInput.addEventListener("change", function () {
      colorPreview.style.backgroundColor = this.value
    })
    // Initialiser la couleur preview
    colorPreview.style.backgroundColor = colorInput.value
  }
})

// FONCTION DE NOTIFICATION AMÉLIORÉE
function showNotification(message, type = "info") {
  console.log(`📢 NOTIFICATION [$type.toUpperCase()]: $message`)

  // Créer l'élément de notification
  const notification = document.createElement("div")
  notification.className = `notification notification-$type`
  notification.style.cssText = `
position: fixed;
top: 20px;
right: 20px;
z-index: 30000;
min-width: 300px;
max-width: 500px;
padding: 1rem;
border-radius: 12px;
box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
backdrop-filter: blur(15px);
border-left: 4px solid;
font-weight: 500;
animation: slideInRight 0.3s ease;
color: white;
`

  // Couleurs selon le type
  const colors = {
    success:
      "background: linear-gradient(135deg, rgba(16, 185, 129, 0.95), rgba(5, 150, 105, 0.9)); border-left-color: #10b981;",
    error:
      "background: linear-gradient(135deg, rgba(239, 68, 68, 0.95), rgba(220, 38, 38, 0.9)); border-left-color: #ef4444;",
    warning:
      "background: linear-gradient(135deg, rgba(245, 158, 11, 0.95), rgba(217, 119, 6, 0.9)); border-left-color: #f59e0b;",
    info: "background: linear-gradient(135deg, rgba(59, 130, 246, 0.95), rgba(37, 99, 235, 0.9)); border-left-color: #3b82f6;",
  }

  notification.style.cssText += colors[type] || colors.info

  notification.innerHTML = `
<div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
<span style="flex: 1; font-weight: 500;">${message}</span>
<button onclick="this.parentElement.parentElement.remove()" style="
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;
">
  <i class="fas fa-times"></i>
</button>
</div>
`

  // Ajouter les styles d'animation si pas encore fait
  if (!document.getElementById("notificationStyles")) {
    const styles = document.createElement("style")
    styles.id = "notificationStyles"
    styles.textContent = `
@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideOutRight {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}
`
    document.head.appendChild(styles)
  }

  // Ajouter la notification au DOM
  document.body.appendChild(notification)

  // Supprimer automatiquement avec animation
  setTimeout(() => {
    if (notification.parentElement) {
      notification.style.animation = "slideOutRight 0.3s ease-in"
      setTimeout(() => {
        if (notification.parentElement) {
          document.body.removeChild(notification)
        }
      }, 300)
    }
  }, 5000)
}

// Fonction utilitaire pour afficher le loading
function showLoading(message) {
  console.log("⏳ Affichage loading:", message)
  const loadingHTML = `
<div class="loading-overlay" style="
position: fixed;
top: 0;
left: 0;
width: 100%;
height: 100%;
background: rgba(0,0,0,0.7);
backdrop-filter: blur(5px);
display: flex;
align-items: center;
justify-content: center;
z-index: 28000;
">
<div class="loading-content" style="
  background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
  color: white;
  border: 1px solid rgba(59, 130, 246, 0.3);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
">
  <i class="fas fa-spinner fa-spin" style="font-size: 2rem; margin-bottom: 1rem; color: #3b82f6;"></i>
  <p style="margin: 0; font-weight: 500;">${message}</p>
</div>
</div>
`
  document.body.insertAdjacentHTML("beforeend", loadingHTML)
}

// Fonction utilitaire pour masquer le loading
function hideLoading() {
  const loadingOverlay = document.querySelector(".loading-overlay")
  if (loadingOverlay) {
    loadingOverlay.remove()
  }
}

console.log("✅ FRONTEND: Dashboard Core script chargé et fonctionnel")
