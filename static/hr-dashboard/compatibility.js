console.log("🎯 FRONTEND: Compatibility module loaded")

// Enhanced applications loading with compatibility filters
async function loadApplicationsWithFilters(statusFilter = "all", compatibilityFilter = "all") {
  console.log("📋 FRONTEND: Loading applications with filters:", { statusFilter, compatibilityFilter })

  try {
    const params = new URLSearchParams()
    if (statusFilter !== "all") params.append("status_filter", statusFilter)
    if (compatibilityFilter !== "all") params.append("compatibility_filter", compatibilityFilter)

    console.log("🌐 FRONTEND: Making API request to /api/applications")
    const response = await fetch(`/api/applications?${params.toString()}`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    console.log("📦 FRONTEND: API response:", result)

    if (result.success) {
      // Update the global applications variable
      if (typeof window.applications !== "undefined") {
        window.applications = result.applications || []
      }
      console.log(`✅ FRONTEND: ${result.applications?.length || 0} applications loaded with compatibility data`)

      // Log sample application data for debugging
      if (result.applications && result.applications.length > 0) {
        console.log("🔍 FRONTEND: Sample application data:", result.applications[0])
      }

      renderApplicationsWithCompatibility()
    } else {
      console.error("❌ FRONTEND: Error loading applications:", result.message)
      if (typeof window.applications !== "undefined") {
        window.applications = []
      }
      renderApplicationsWithCompatibility()
    }
  } catch (error) {
    console.error("❌ FRONTEND: Network error loading applications:", error)
    if (typeof window.applications !== "undefined") {
      window.applications = []
    }
    renderApplicationsWithCompatibility()
  }
}

// Enhanced rendering with compatibility information
function renderApplicationsWithCompatibility(filter = "all") {
  console.log("📋 FRONTEND: Rendering applications with compatibility, filter:", filter)

  const container = document.getElementById("applicationsContainer")
  if (!container) {
    console.error("❌ FRONTEND: Applications container not found")
    return
  }

  const applications = window.applications || []
  let filteredApps = applications
  if (filter !== "all") {
    filteredApps = applications.filter((app) => app.status === filter)
  }

  console.log(`🎨 FRONTEND: Rendering ${filteredApps.length} applications`)

  if (filteredApps.length === 0) {
    container.innerHTML = `
            <div class="empty-applications">
                <i class="fas fa-file-alt"></i>
                <h4>Aucune candidature</h4>
                <p>Aucune candidature ${getFilterText(filter)}</p>
                <button class="empty-btn" onclick="createDemoApplications()">
                    <i class="fas fa-plus"></i> Créer des candidatures de test
                </button>
            </div>
        `
    return
  }

  container.innerHTML = filteredApps
    .map((app) => {
      console.log(`🎯 FRONTEND: Rendering app ${app.id} with compatibility ${app.compatibility_percentage}%`)
      return `
        <div class="application-card-enhanced ${app.status}">
            <div class="application-header">
                <div class="applicant-info">
                    <div class="applicant-avatar">${getInitials(app.candidate_name)}</div>
                    <div class="applicant-details">
                        <h4>${app.candidate_name}</h4>
                        <p>${app.candidate_email}</p>
                        <small><i class="fas fa-briefcase"></i> ${app.job_title}</small>
                    </div>
                </div>
                <div class="application-status ${app.status}">
                    ${getStatusText(app.status)}
                </div>
            </div>
            
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

            <!-- Compatibility Section -->
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
                        ${app.matched_skills_count} compétences correspondantes
                    </span>
                    <span class="skill-stat missing">
                        <i class="fas fa-times-circle"></i>
                        ${app.total_job_skills - app.matched_skills_count} manquantes
                    </span>
                    <span>Total: ${app.total_job_skills} compétences</span>
                </div>
                
                <div class="compatibility-actions">
                    <button class="btn-compatibility-details" onclick="viewCompatibilityDetails(${app.id})">
                        <i class="fas fa-search"></i> Détails compatibilité
                    </button>
                </div>
            </div>
            
            <div class="application-actions">
                <button class="app-btn view" onclick="viewCandidateProfile(${app.candidate_id})">
                    <i class="fas fa-user"></i> Voir Profil
                </button>
                <button class="app-btn info" onclick="viewJobDetails(${app.job_id})">
                    <i class="fas fa-info-circle"></i> Détails Poste
                </button>
                <button class="app-btn review" onclick="updateApplicationStatus(${app.id}, 'reviewed')">
                    <i class="fas fa-eye"></i> Examiner
                </button>
                ${
                  app.status === "pending" || app.status === "reviewed"
                    ? `
                    <button class="app-btn schedule" onclick="updateApplicationStatus(${app.id}, 'interview_scheduled')">
                        <i class="fas fa-calendar"></i> Programmer
                    </button>
                `
                    : ""
                }
                ${
                  app.status === "interview_scheduled"
                    ? `
                    <button class="app-btn complete" onclick="updateApplicationStatus(${app.id}, 'interview_completed')">
                        <i class="fas fa-check"></i> Terminer
                    </button>
                `
                    : ""
                }
                ${
                  app.status === "interview_completed" || app.status === "reviewed"
                    ? `
                    <button class="app-btn accept" onclick="updateApplicationStatus(${app.id}, 'accepted')">
                        <i class="fas fa-thumbs-up"></i> Accepter
                    </button>
                    <button class="app-btn reject" onclick="updateApplicationStatus(${app.id}, 'rejected')">
                        <i class="fas fa-thumbs-down"></i> Rejeter
                    </button>
                `
                    : ""
                }
            </div>
        </div>
    `
    })
    .join("")

  console.log("✅ FRONTEND: Applications rendered with compatibility data")
}

// Compatibility helper functions
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

// Filter applications by compatibility
function filterApplicationsByCompatibility(compatibilityLevel) {
  console.log("🔍 FRONTEND: Filtering applications by compatibility:", compatibilityLevel)

  const statusFilter = document.querySelector(".filter-select").value || "all"
  loadApplicationsWithFilters(statusFilter, compatibilityLevel)
}

// Filter applications by name (enhanced)
function filterApplicationByName() {
  const input = document.getElementById("applicationSearchInput")
  const searchTerm = input.value.toLowerCase().trim()

  const applications = window.applications || []
  const filtered = applications.filter((app) => {
    return (
      app.candidate_name.toLowerCase().includes(searchTerm) ||
      app.candidate_email.toLowerCase().includes(searchTerm) ||
      app.job_title.toLowerCase().includes(searchTerm)
    )
  })

  renderFilteredApplications(filtered)
}

function renderFilteredApplications(filteredApps) {
  const container = document.getElementById("applicationsContainer")

  if (!container) return

  if (filteredApps.length === 0) {
    container.innerHTML = `
            <div class="empty-applications">
                <i class="fas fa-search"></i>
                <h4>Aucun résultat</h4>
                <p>Aucune candidature ne correspond à votre recherche</p>
            </div>
        `
    return
  }

  // Use the same enhanced rendering for filtered results
  const originalApplications = window.applications
  window.applications = filteredApps
  renderApplicationsWithCompatibility()
  window.applications = originalApplications
}

// View compatibility details
async function viewCompatibilityDetails(applicationId) {
  console.log("🔍 FRONTEND: Viewing compatibility details for application:", applicationId)

  try {
    const response = await fetch(`/api/application/${applicationId}/compatibility`)
    const result = await response.json()

    if (result.success) {
      showCompatibilityModal(result)
    } else {
      showNotification("Erreur lors du chargement des détails de compatibilité", "error")
    }
  } catch (error) {
    console.error("❌ FRONTEND: Error loading compatibility details:", error)
    showNotification("Erreur de connexion", "error")
  }
}

// Show compatibility modal
function showCompatibilityModal(compatibilityData) {
  const modal = document.createElement("div")
  modal.className = "modal-overlay"
  modal.style.display = "flex"
  modal.style.zIndex = "10003"

  modal.innerHTML = `
        <div class="modal-content" style="max-width: 800px;">
            <div class="modal-header">
                <h3><i class="fas fa-chart-pie"></i> Détails de Compatibilité</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="compatibility-overview">
                    <div class="compatibility-score">
                        <div class="score-circle ${getCompatibilityClass(compatibilityData.compatibility_percentage)}">
                            <span class="score-number">${compatibilityData.compatibility_percentage}%</span>
                            <span class="score-label">Compatibilité</span>
                        </div>
                    </div>
                    
                    <div class="compatibility-summary">
                        <div class="summary-stat">
                            <i class="fas fa-check-circle" style="color: #10b981;"></i>
                            <span>${compatibilityData.matched_count} compétences correspondantes</span>
                        </div>
                        <div class="summary-stat">
                            <i class="fas fa-times-circle" style="color: #ef4444;"></i>
                            <span>${compatibilityData.missing_count} compétences manquantes</span>
                        </div>
                        <div class="summary-stat">
                            <i class="fas fa-list" style="color: #6b7280;"></i>
                            <span>${compatibilityData.total_job_skills} compétences requises au total</span>
                        </div>
                    </div>
                </div>
                
                <div class="skills-breakdown">
                    <div class="skills-section">
                        <div class="skills-breakdown-header">
                            <h4 class="skills-breakdown-title">
                                <i class="fas fa-check-circle" style="color: #10b981;"></i>
                                Compétences Correspondantes (${compatibilityData.matched_count})
                            </h4>
                        </div>
                        <div class="skills-list">
                            ${compatibilityData.matched_skills
                              .map(
                                (skill) => `
                                <div class="skill-item matched">
                                    <div class="skill-info">
                                        <span class="skill-name">${skill.skill_name}</span>
                                        <span class="skill-level ${skill.skill_level}">${getLevelText(skill.skill_level)}</span>
                                        <span class="skill-required ${skill.is_required ? "required" : "optional"}">
                                            ${skill.is_required ? "Requis" : "Optionnel"}
                                        </span>
                                    </div>
                                    <div class="skill-status matched">
                                        <i class="fas fa-check"></i>
                                        Possédée
                                    </div>
                                </div>
                            `,
                              )
                              .join("")}
                        </div>
                    </div>
                    
                    <div class="skills-section">
                        <div class="skills-breakdown-header">
                            <h4 class="skills-breakdown-title">
                                <i class="fas fa-times-circle" style="color: #ef4444;"></i>
                                Compétences Manquantes (${compatibilityData.missing_count})
                            </h4>
                        </div>
                        <div class="skills-list">
                            ${compatibilityData.missing_skills
                              .map(
                                (skill) => `
                                <div class="skill-item missing">
                                    <div class="skill-info">
                                        <span class="skill-name">${skill.skill_name}</span>
                                        <span class="skill-level ${skill.skill_level}">${getLevelText(skill.skill_level)}</span>
                                        <span class="skill-required ${skill.is_required ? "required" : "optional"}">
                                            ${skill.is_required ? "Requis" : "Optionnel"}
                                        </span>
                                    </div>
                                    <div class="skill-status missing">
                                        <i class="fas fa-times"></i>
                                        Manquante
                                    </div>
                                </div>
                            `,
                              )
                              .join("")}
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Fermer</button>
            </div>
        </div>
    `

  document.body.appendChild(modal)
}

// Update application status
async function updateApplicationStatus(applicationId, newStatus) {
  console.log("📝 FRONTEND: Updating application status:", { applicationId, newStatus })

  try {
    const response = await fetch(`/api/applications/${applicationId}/update-status`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status: newStatus }),
    })

    const result = await response.json()

    if (result.success) {
      showNotification(`Candidature mise à jour vers "${getStatusText(newStatus)}"`, "success")
      // Reload applications to reflect changes
      const statusFilter = document.querySelector(".filter-select").value || "all"
      const compatibilityFilter = document.querySelector(".compatibility-filter-select").value || "all"
      loadApplicationsWithFilters(statusFilter, compatibilityFilter)
    } else {
      showNotification("Erreur lors de la mise à jour: " + result.message, "error")
    }
  } catch (error) {
    console.error("❌ FRONTEND: Error updating application status:", error)
    showNotification("Erreur de connexion", "error")
  }
}

// Helper function to get level text in French
function getLevelText(level) {
  const levelTexts = {
    beginner: "Débutant",
    intermediate: "Intermédiaire",
    advanced: "Avancé",
    expert: "Expert",
  }
  return levelTexts[level] || level
}

// Create demo applications with compatibility data
async function createDemoApplications() {
  console.log("🎭 FRONTEND: Creating demo applications")

  try {
    const response = await fetch("/api/applications/create-demo", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })

    const result = await response.json()

    if (result.success) {
      showNotification(`${result.applications.length} candidatures de démonstration créées`, "success")
      loadApplicationsWithFilters()
    } else {
      showNotification("Erreur lors de la création des candidatures de test", "error")
    }
  } catch (error) {
    console.error("❌ FRONTEND: Error creating demo applications:", error)
    showNotification("Erreur de connexion", "error")
  }
}

// Enhanced notification function with better styling
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
    success: "linear-gradient(135deg, #10b981, #059669)",
    error: "linear-gradient(135deg, #ef4444, #dc2626)",
    warning: "linear-gradient(135deg, #f59e0b, #d97706)",
    info: "linear-gradient(135deg, #3b82f6, #2563eb)",
  }

  notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas ${icons[type]}"></i>
        </div>
        <div class="notification-content">
            <span>${message}</span>
        </div>
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
        padding: 1rem;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 1rem;
        z-index: 20000;
        backdrop-filter: blur(10px);
        animation: slideInRight 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        min-width: 320px;
        max-width: 450px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    `

  document.body.appendChild(notification)

  setTimeout(() => {
    notification.style.animation = "slideOutRight 0.3s ease-in"
    setTimeout(() => {
      if (notification.parentElement) {
        document.body.removeChild(notification)
      }
    }, 300)
  }, 5000)
}

// Declare helper functions
function getFilterText(filter) {
  const filterTexts = {
    all: "",
    pending: "en attente",
    reviewed: "examinée",
    interview_scheduled: "programmée pour entretien",
    interview_completed: "entretien terminé",
    accepted: "acceptée",
    rejected: "rejetée",
  }
  return filterTexts[filter] || filter
}

function getInitials(name) {
  return name
    .split(" ")
    .map((word) => word.charAt(0))
    .join("")
    .toUpperCase()
}

function getStatusText(status) {
  const statusTexts = {
    pending: "En attente",
    reviewed: "Examinée",
    interview_scheduled: "Programmée pour entretien",
    interview_completed: "Entretien terminé",
    accepted: "Acceptée",
    rejected: "Rejetée",
  }
  return statusTexts[status] || status
}

function formatDate(date) {
  const options = { year: "numeric", month: "long", day: "numeric" }
  return new Date(date).toLocaleDateString("fr-FR", options)
}

// Make functions available globally
window.loadApplicationsWithFilters = loadApplicationsWithFilters
window.renderApplicationsWithCompatibility = renderApplicationsWithCompatibility
window.filterApplicationsByCompatibility = filterApplicationsByCompatibility
window.filterApplicationByName = filterApplicationByName
window.viewCompatibilityDetails = viewCompatibilityDetails
window.updateApplicationStatus = updateApplicationStatus
window.createDemoApplications = createDemoApplications
window.getCompatibilityClass = getCompatibilityClass
window.getCompatibilityIcon = getCompatibilityIcon

console.log("✅ FRONTEND: Compatibility module ready")
